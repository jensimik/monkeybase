from typing import Generic, TypeVar, Sequence
from pydantic.generics import GenericModel

T = TypeVar("T")


class Page(GenericModel, Generic[T]):
    items: Sequence[T]
    next: str
    has_next: bool
