from transformers import pipeline
from app.llm.base import Runnable
from app.llm.models import (
    PipelineInput,
    PromptPayload,
    RawLLMOutput,
    StructuredResponse,
)

# Global variabel för den lokala maskininlärningsmodellen (Lazy Loading)
GLOBAL_LOCAL_PIPELINE = None


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

        # Det korrekta chattformatet för SmolLM2
        full_prompt = f"<|im_start|>system\n{system_prompt}<|im_end|>\n<|im_start|>user\n{data.query}<|im_end|>\n<|im_start|>assistant\n"
        return PromptPayload(original_query=data.query, full_prompt=full_prompt)


class LLMRunner(Runnable[PromptPayload, RawLLMOutput]):
    name: str = "llm_runner"

    def invoke(self, payload: PromptPayload) -> RawLLMOutput:
        global GLOBAL_LOCAL_PIPELINE

        if GLOBAL_LOCAL_PIPELINE is None:
            print("Laddar in den lokala AI-modellen i minnet...")
            GLOBAL_LOCAL_PIPELINE = pipeline(
                "text-generation", model="HuggingFaceTB/SmolLM2-1.7B-Instruct"
            )
            print("Modellen är redo och inläst!")

        response = GLOBAL_LOCAL_PIPELINE(
            payload.full_prompt,
            max_new_tokens=100,
            temperature=0.1,
            do_sample=True,
            pad_token_id=GLOBAL_LOCAL_PIPELINE.tokenizer.eos_token_id,
        )

        raw_text = response[0]["generated_text"]
        return RawLLMOutput(original_query=payload.original_query, raw_text=raw_text)


class ResponseParser(Runnable[RawLLMOutput, StructuredResponse]):
    name: str = "response_parser"

    def invoke(self, data: RawLLMOutput) -> StructuredResponse:
        ai_clean = data.raw_text.split("Svar:")[-1].strip()
        return StructuredResponse(fraga=data.original_query, ai_svar=ai_clean)


# Vi komponerar ihop kedjan med |-operatorn
spotify_pipeline = PromptBuilder() | LLMRunner() | ResponseParser()
