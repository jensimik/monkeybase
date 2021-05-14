from typing import Optional, List, Any
from pydantic import BaseModel


class Page(BaseModel):
    data: List[Any] = []
    next: str
