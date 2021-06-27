from ..models import WaitingList
from ..schemas import WaitingListCreate, WaitingListUpdate
from .base import CRUDBase


class CRUDWaitingList(CRUDBase[WaitingList, WaitingListCreate, WaitingListUpdate]):
    pass


waiting_list = CRUDWaitingList(WaitingList)
