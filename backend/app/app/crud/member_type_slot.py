from .base import CRUDBase
from ..models import MemberTypeSlot
from ..schemas import MemberTypeSlotCreate, MemberTypeSlotUpdate


class CRUDMemberTypeSlot(
    CRUDBase[MemberTypeSlot, MemberTypeSlotCreate, MemberTypeSlotUpdate]
):
    pass


member_type_slot = CRUDMemberTypeSlot(MemberTypeSlot)
