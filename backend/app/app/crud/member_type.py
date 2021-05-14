from app.crud.base import CRUDBase
from app.models import MemberType
from app.schemas import MemberTypeCreate, MemberTypeUpdate


class CRUDMemberType(CRUDBase[MemberType, MemberTypeCreate, MemberTypeUpdate]):
    pass


member_type = CRUDMemberType(MemberType)
