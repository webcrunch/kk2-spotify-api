from transformers import pipeline
from pydantic import BaseModel, ConfigDict, SerializeAsAny
from typing import Any, Callable, Generic, TypeVar

I = TypeVar("I")
O = TypeVar("O")
M = TypeVar("M")


class Runnable(BaseModel, Generic[I, O]):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    name: str | None = None

    def invoke(self, data: I) -> O:
        raise NotImplementedError("Subclasses is not implemented")

    def __or__(self, other: Any) -> "RunnableSequence":
        # Fallback: Om Pydantic har strulat till instansen
        current_self = self if self is not None else self.__class__()

        # Kolla om 'other' är en instans av Runnable (eller en subklass)
        if isinstance(other, Runnable) or (
            hasclass := hasattr(other, "__class__")
            and issubclass(other.__class__, Runnable)
        ):
            return RunnableSequence.model_construct(first=current_self, second=other)

        if callable(other):
            return RunnableSequence.model_construct(
                first=current_self,
                second=RunnableLambda.model_construct(
                    func=other, name=getattr(other, "__name__", "lambda")
                ),
                name=getattr(other, "__name__", "lambda"),
            )
        return NotImplemented

    def __ror__(self, other: Any) -> Any:
        if callable(other):
            return RunnableSequence.model_construct(
                first=RunnableLambda.model_construct(func=other),
                second=self,
                name=getattr(other, "__name__", "lambda"),
            )
        return NotImplemented


class RunnableLambda(Runnable[I, O]):
    func: Callable[[I], O]

    def invoke(self, data: I) -> O:
        return self.func(data)


class RunnableSequence(Runnable[I, O], Generic[I, M, O]):
    first: SerializeAsAny[Runnable[I, M]]
    second: SerializeAsAny[Runnable[M, O]]

    def invoke(self, data: I) -> O:
        return self.second.invoke(self.first.invoke(data))


# Hårt typade pydantic modeller


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


# PIPELINES


class PromptBuilder(Runnable[PipelineInput, PromptPayload]):
    name: str = "prompt_builder"

    def invoke(self, data: PipelineInput) -> PromptPayload:
        system_prompt = (
            "Du är en expert på dataanalys och musiktrender. "
            "Svara kortfattat, professionell och alltid på svenska. "
            f"Använd denna statistik för att svara:\n{data.stats_text}\n"
            "Avsluta alltid ditt svar med 'krama varandra i trafiken'."
        )

        full_prompt = f"{system_prompt}\n\nFråga: {data.query}\nSvar:"
        return PromptPayload(original_query=data.query, full_prompt=full_prompt)


GLOBAL_LOCAL_PIPELINE = None


class LLMRunner(Runnable[PromptPayload, RawLLMOutput]):
    name: str = "llm_runner"

    def invoke(self, payload: PromptPayload) -> RawLLMOutput:
        global GLOBAL_LOCAL_PIPELINE

        if GLOBAL_LOCAL_PIPELINE is None:
            print("Laddar in den lokala AI-modellen...")
            GLOBAL_LOCAL_PIPELINE = pipeline(
                "text-generation", model="HuggingFaceTB/SmolLM2-135M-Instruct"
            )
            print("Modellen är redo!")

        # 1. FIXEN: Vi använder en ren text-sträng men sätter säkra gränser för sökningen
        # Vi lägger till do_sample=True och en lägre temperatur så den inte svävar iväg
        response = GLOBAL_LOCAL_PIPELINE(
            payload.full_prompt,
            max_new_tokens=100,
            temperature=0.1,  # Låg temperatur = mer strikt och håller sig till fakta
            do_sample=True,
            pad_token_id=GLOBAL_LOCAL_PIPELINE.tokenizer.eos_token_id,
        )

        raw_text = response[0]["generated_text"]
        return RawLLMOutput(original_query=payload.original_query, raw_text=raw_text)


class ResponseParser(Runnable[RawLLMOutput, StructuredResponse]):
    name: str = "response_parser"

    def invoke(self, data: RawLLMOutput) -> StructuredResponse:

        # Vi plockar bara ut det som ain svarade
        ai_clean = data.raw_text.split("Svar:")[-1].strip()

        return StructuredResponse(fraga=data.original_query, ai_svar=ai_clean)


spotify_pipeline = PromptBuilder() | LLMRunner() | ResponseParser()
