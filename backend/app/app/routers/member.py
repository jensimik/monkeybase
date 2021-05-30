from typing import Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, Security
import sqlalchemy as sa
from .. import models, schemas, crud, deps


router = APIRouter()


# @router.post("")
# def test(
#     create: schemas.MemberCreateMe,
#     current_user_id: int = Security(deps.get_current_user_id, scopes=["basic"]),
#     db: AsyncSession = Depends(deps.get_db),
# ):
#     return False


@router.get("", response_model=schemas.Page[schemas.MemberUser])
async def member_list(
    member_type_id: Optional[int] = None,
    paging: deps.Paging = Depends(deps.Paging),
    q: deps.Q = Depends(deps.Q),
    _: int = Security(deps.get_current_user_id, scopes=["admin"]),
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    """
    Get list of all member for this membership_type
    """
    args = (
        [
            sa.or_(
                sa.func.lower(models.User.name).contains(q.q.lower(), autoescape=True),
                sa.func.lower(models.User.email).contains(q.q.lower(), autoescape=True),
            )
        ]
        if q.q
        else []
    )
    if member_type_id is not None:
        args.append(models.Member.member_type_id == member_type_id)

    return await crud.member.get_multi_page(
        db,
        join=[models.Member.user],
        *args,
        options=[
            sa.orm.subqueryload(models.Member.user.and_(models.User.active == True)),
            sa.orm.subqueryload(
                models.Member.member_type.and_(models.MemberType.active == True)
            ),
        ],
        per_page=paging.per_page,
        page=paging.page,
        order_by=[models.User.name.asc()],
    )
