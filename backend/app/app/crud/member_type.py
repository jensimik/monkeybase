from ..models import MemberType
from ..schemas import MemberTypeCreate, MemberTypeUpdate
from .base import CRUDBase


class CRUDMemberType(CRUDBase[MemberType, MemberTypeCreate, MemberTypeUpdate]):
    pass


member_type = CRUDMemberType(MemberType)
