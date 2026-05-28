from transformers import pipeline
from app.llm.base import Runnable
from app.llm.models import (
    PipelineInput,
    PromptPayload,
    RawLLMOutput,
    StructuredResponse,
)
import os
import logging
import requests
from dotenv import load_dotenv

load_dotenv()
# Global variabel för den lokala maskininlärningsmodellen (Lazy Loading)
GLOBAL_LOCAL_PIPELINE = None

# Konfigurera loggningen
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class PromptBuilder(Runnable[PipelineInput, PromptPayload]):
    name: str = "prompt_builder"

    def invoke(self, data: PipelineInput) -> PromptPayload:
        # Vi gör om datan till ren text som en smart modell älskar
        system_prompt = (
            "Du är en professionell dataanalytiker som hjälper användaren med Spotify-statistik.\n"
            "Använd ENDAST denna data för att svara:\n"
            f"{data.stats_text}\n\n"
            "Svara kort, koncist och alltid på svenska. "
            "Avsluta med 'krama varandra i trafiken'."
        )

        full_prompt = (
            f"<|im_start|>system\n{system_prompt}<|im_end|>\n"
            f"<|im_start|>user\n{data.question}<|im_end|>\n"
            f"<|im_start|>assistant\n"  # Vi lämnar den tom, modellen får formulera meningen själv!
        )

        return PromptPayload(original_question=data.question, full_prompt=full_prompt)


class LLMRunner(Runnable[PromptPayload, RawLLMOutput]):
    name: str = "llm_runner"

    def invoke(self, payload: PromptPayload) -> RawLLMOutput:
        global GLOBAL_LOCAL_PIPELINE

        # hämtar environment variablen
        provider = os.getenv("AI_PROVIDER", "huggingface").lower()

        if provider == "ollama":
            # logik för att hantera ollama anrop
            model_name = os.getenv("MODEL_NAME", "llama3.2")
            ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")

            logger.info(
                f"Skickar förfrågan till Ollama ({model_name}) på {ollama_url}..."
            )

            api_payload = {
                "model": model_name,
                "prompt": payload.full_prompt,
                "stream": False,
                "options": {"temperature": 0.1},
            }

            try:
                response = requests.post(f"{ollama_url}/api/generate", json=api_payload)
                response.raise_for_status()

                raw_text = response.json().get("response", "")
                logger.info("Fick svar från Ollama framgångsrikt")

            except requests.exceptions.RequestException as e:
                logger.error(f"Ett fel uppstod vid kommunikationen med Ollama: {e}")
                raw_text = "Något gick fel :/ Ollama är inte tillgänglig för tillfället"

        else:
            model_name = os.getenv("MODEL_NAME", "HuggingFaceTB/SmolLM2-135M-Instruct")

            if GLOBAL_LOCAL_PIPELINE is None:
                logger.info(f"Laddar in den lokala AI-modellen: {model_name}...")
                GLOBAL_LOCAL_PIPELINE = pipeline(
                    "text-generation", model=model_name, token=os.getenv("HF_TOKEN")
                )
                logger.info("Modellen är reda och inläst i minnet!")

            logger.info("Kör generering likalt med HuggingFace")
            response = GLOBAL_LOCAL_PIPELINE(
                payload.full_prompt,
                max_new_tokens=100,
                temperature=0.1,
                do_sample=True,
                pad_token_id=GLOBAL_LOCAL_PIPELINE.tokenizer.eos_token_id,
            )

            raw_text = response[0]["generated_text"]

        return RawLLMOutput(
            original_question=payload.original_question, raw_text=raw_text
        )


class ResponseParser(Runnable[RawLLMOutput, StructuredResponse]):
    name: str = "response_parser"

    def invoke(self, data: RawLLMOutput) -> StructuredResponse:
        raw_text = data.raw_text
        target_token = "<|im_start|>assistant\n"

        # 1. Hitta var AI:ns faktiska svar börjar
        if target_token in raw_text:
            clean_answer = raw_text.split(target_token)[-1]
        else:
            clean_answer = raw_text

        # 2. Städa bort eventuella ChatML-taggar
        clean_answer = clean_answer.replace("<|im_end|>", "").strip()

        # Hämta den modellen vi kör på och gör den till små bokstäver för enklare matchning
        current_model = os.getenv("MODEL_NAME", "okänd-modell").lower()

        # Vår dynamiska "växel"
        catchphrases = {
            "llama": "Dags att bli farliga",
            "mistral": "håll koden ren och containrarna små",
            "smollm": "krama varandra i trafiken!",
        }

        # Vår default-sträng om ingen matchning hittas
        chosen_phrase = "glöm inte att pusha till main!"

        # DYNAMISK MATCHNING: Vi loopar och kollar om t.ex. "llama" finns inuti "llama3.2"
        for key, phrase in catchphrases.items():
            if key in current_model:
                chosen_phrase = phrase
                break

        # 3. Limma ihop allt
        final_answer = f"{clean_answer}\n\n{chosen_phrase}"

        return StructuredResponse(
            question=data.original_question,
            answer=final_answer,
            model=current_model,
        )


# Vi komponerar ihop kedjan med |-operatorn
spotify_pipeline = PromptBuilder() | LLMRunner() | ResponseParser()
