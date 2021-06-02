from ..models import MemberTypeSlot
from ..schemas import MemberTypeSlotCreate, MemberTypeSlotUpdate
from .base import CRUDBase


class CRUDMemberTypeSlot(
    CRUDBase[MemberTypeSlot, MemberTypeSlotCreate, MemberTypeSlotUpdate]
):
    pass


member_type_slot = CRUDMemberTypeSlot(MemberTypeSlot)
