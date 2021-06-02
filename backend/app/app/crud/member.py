from ..models import Member
from ..schemas import MemberCreate, MemberUpdate
from .base import CRUDBase


class CRUDMember(CRUDBase[Member, MemberCreate, MemberUpdate]):
    pass


member = CRUDMember(Member)
