from typing import Any, Optional

import sqlalchemy as sa
from fastapi import APIRouter, Depends, Security
from sqlalchemy.ext.asyncio import AsyncSession

from .. import crud, deps, models, schemas

router = APIRouter()


@router.post("")
async def create_membership(
    create: schemas.MemberCreateMe,
    current_user_id: int = Security(deps.get_current_user_id, scopes=["admin"]),
    db: AsyncSession = Depends(deps.get_db),
):
    return False


@router.patch("/{member_id}")
async def modify_membership(
    create: schemas.MemberCreateMe,
    current_user_id: int = Security(deps.get_current_user_id, scopes=["admin"]),
    db: AsyncSession = Depends(deps.get_db),
):
    return False


@router.delete("/{member_id}")
async def deactivate_membership(
    member_id: int,
    user_id: int = Security(deps.get_current_user_id, scopes=["admin"]),
    db: AsyncSession = Depends(deps.get_db),
):
    member = await crud.member.get(
        db, models.Member.id == member_id, models.Member.user_id == user_id
    )
    return False


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
