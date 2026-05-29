from pydantic import BaseModel
import os
from pydantic import BaseModel, Field


class PipelineInput(BaseModel):
    question: str
    stats_text: str
    context: str


class PromptPayload(BaseModel):
    original_question: str
    full_prompt: str


class RawLLMOutput(BaseModel):
    original_question: str
    raw_text: str


class StructuredResponse(BaseModel):
    question: str
    answer: str
    # Vi hämtar live från .env. Hittas den inte har vi en fallback!
    model: str = Field(
        default_factory=lambda: os.getenv(
            "MODEL_NAME", "HuggingFaceTB/SmolLM2-135M-Instruct"
        )
    )
