from .base import CRUDBase
from ..models import MemberType
from ..schemas import MemberTypeCreate, MemberTypeUpdate


class CRUDMemberType(CRUDBase[MemberType, MemberTypeCreate, MemberTypeUpdate]):
    pass


member_type = CRUDMemberType(MemberType)
