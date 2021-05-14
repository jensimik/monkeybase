from typing import Generic, TypeVar, List, Sequence, Optional
from pydantic.fields import ModelField
from pydantic import BaseModel, ValidationError
from pydantic.generics import GenericModel

T = TypeVar("T")


class Page(GenericModel, Generic[T]):
    items: Sequence[T]
    next: str
    has_next: bool
