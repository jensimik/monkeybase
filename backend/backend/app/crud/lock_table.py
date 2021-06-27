from datetime import datetime

import pydantic

from ..models import LockTable
from .base import CRUDBase


class LockTableSchema(pydantic.BaseModel):
    name: str
    ran_at: datetime


class CRUDLockTable(CRUDBase[LockTable, LockTableSchema, LockTableSchema]):
    pass


lock_table = CRUDLockTable(LockTable)
