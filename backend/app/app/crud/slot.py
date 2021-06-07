from ..models import Slot
from ..schemas import SlotCreate, SlotUpdate
from .base import CRUDBase


class CRUDSlot(CRUDBase[Slot, SlotCreate, SlotUpdate]):
    pass


slot = CRUDSlot(Slot)
