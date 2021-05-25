from app.crud.base import CRUDBase
from app.models import LockTable
import pydantic
from datetime import datetime


class LockTableSchema(pydantic.BaseModel):
    name: str
    ran_at: datetime


class CRUDLockTable(CRUDBase[LockTable, LockTableSchema, LockTableSchema]):
    pass


lock_table = CRUDLockTable(LockTable)
