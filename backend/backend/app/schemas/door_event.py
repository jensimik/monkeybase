from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class DoorEvent(BaseModel):
    user_id: int
    created_at: Optional[datetime] = None
