from datetime import datetime
from .base import CRUDBase
from .. import schemas, models
import pydantic


class LockTableSchema(pydantic.BaseModel):
    name: str
    ran_at: datetime


class CRUDDoorEvent(CRUDBase[models.Doorevent, schemas.DoorEvent, schemas.DoorEvent]):
    pass


door_event = CRUDDoorEvent(models.Doorevent)
