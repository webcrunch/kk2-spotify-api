from pydantic import BaseModel


class PipelineInput(BaseModel):
    query: str
    stats_text: str


class PromptPayload(BaseModel):
    original_query: str
    full_prompt: str


class RawLLMOutput(BaseModel):
    original_query: str
    raw_text: str


class StructuredResponse(BaseModel):
    fraga: str
    ai_svar: str
