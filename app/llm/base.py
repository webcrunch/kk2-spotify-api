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
        current_self = self if self is not None else self.__class__()

        if isinstance(other, Runnable) or (
            hasattr(other, "__class__") and issubclass(other.__class__, Runnable)
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
