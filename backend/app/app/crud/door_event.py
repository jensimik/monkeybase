from .. import models, schemas
from .base import CRUDBase


class CRUDDoorEvent(CRUDBase[models.Doorevent, schemas.DoorEvent, schemas.DoorEvent]):
    pass


door_event = CRUDDoorEvent(models.Doorevent)
