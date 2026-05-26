from transformers import pipelines 
from pydantic import BaseModel, ConfigDict, SerializeAsAny
from typing import Any, Callable, Generic, TypeVar

I = TypeVar("I")
O = TypeVar("O")
M = TypeVar("M")

class Runnable(BaseModel, Generic[I,O]):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    name: str = None = None
    
    def invoke(self, data: I ) -> O:
        raise NotImplementedError("SubClass is not implemented")
    
    def __or__(self, other: Any) -> "RunnableSequence":
        if isinstance(other, Runnable):
            return RunnableSequence.model_construct(first=self, second=other)
        if callable(other):
            return RunnableSequence.model_construct(
                first=self, 
                second=RunnableLambda.model_construct(
                    func=other, 
                    name=other.__name__
                    ),
                name=other.__name__
            )
        return NotImplemented
    
    def __or__(self, other):
        if callable(other):
            return RunnableSequence.model_construct(
                first=RunnableLambda.model_construct(func=other),
                second=self,
                name=other.__name__,
                ),
            return NotImplemented

class   