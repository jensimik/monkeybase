from app.crud.base import CRUDBase
from app.models import MemberTypeSlot
from app.schemas import MemberTypeSlotCreate, MemberTypeSlotUpdate


class CRUDMemberTypeSlot(
    CRUDBase[MemberTypeSlot, MemberTypeSlotCreate, MemberTypeSlotUpdate]
):
    pass


member_type_slot = CRUDMemberTypeSlot(MemberTypeSlot)
