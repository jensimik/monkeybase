from .base import CRUDBase
from ..models import Member
from ..schemas import MemberCreate, MemberUpdate


class CRUDMember(CRUDBase[Member, MemberCreate, MemberUpdate]):
    pass


member = CRUDMember(Member)
