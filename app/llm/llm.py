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

        if GLOBAL_LOCAL_PIPELINE is None:
            model_to_load = os.getenv(
                "MODEL_NAME", "HuggingFaceTB/SmolLM2-135M-Instruct"
            )

            logger.info(f"Laddar in den lokala AI-modellen: {model_to_load}...")
            GLOBAL_LOCAL_PIPELINE = pipeline(
                "text-generation", model=model_to_load, token=os.getenv("HF_TOKEN")
            )
            logger.info("Modellen är redo och inläst i minnet!")

        response = GLOBAL_LOCAL_PIPELINE(
            payload.full_prompt,
            max_new_tokens=100,
            temperature=0.1,
            do_sample=True,
            pad_token_id=GLOBAL_LOCAL_PIPELINE.tokenizer.eos_token_id,
        )

        raw_text = response[0]["generated_text"]

        # KORRIGERAD: original_query -> original_question
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
            # Klipp bort allt system- och user-lullull före assistant
            clean_answer = raw_text.split(target_token)[-1]
        else:
            # Fallback om modellen formaterade lite annorlunda
            clean_answer = raw_text

        # 2. Städa bort eventuella ChatML-taggar (så vi slipper se <|im_end|>)
        clean_answer = clean_answer.replace("<|im_end|>", "").strip()

        # 3. Vi limmar på din signatur med en snygg radbrytning!
        final_answer = f"{clean_answer}\n\nkrama varandra i trafiken!"

        # Vi hämtar modellnamnet direkt från miljövariabeln som fallback!
        current_model = os.getenv("MODEL_NAME", "HuggingFaceTB/SmolLM2-1.7B-Instruct")

        return StructuredResponse(
            question=data.original_question,
            answer=clean_answer,
            model=current_model,
        )


# Vi komponerar ihop kedjan med |-operatorn
spotify_pipeline = PromptBuilder() | LLMRunner() | ResponseParser()
