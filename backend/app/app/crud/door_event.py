from datetime import datetime

import pydantic

from .. import models, schemas
from .base import CRUDBase


class LockTableSchema(pydantic.BaseModel):
    name: str
    ran_at: datetime


class CRUDDoorEvent(CRUDBase[models.Doorevent, schemas.DoorEvent, schemas.DoorEvent]):
    pass


door_event = CRUDDoorEvent(models.Doorevent)
