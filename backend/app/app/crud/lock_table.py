from datetime import datetime
from .base import CRUDBase
from ..models import LockTable
import pydantic


class LockTableSchema(pydantic.BaseModel):
    name: str
    ran_at: datetime


class CRUDLockTable(CRUDBase[LockTable, LockTableSchema, LockTableSchema]):
    pass


lock_table = CRUDLockTable(LockTable)
