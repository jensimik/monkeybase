from typing import Any

import sqlalchemy as sa
from fastapi import APIRouter, Depends, Security
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from .. import crud, deps, models, schemas
from .user import _delete_user

router = APIRouter()


@router.get("", response_model=schemas.User)
async def read_user_me(
    user_id: models.User = Security(deps.get_current_user_id, scopes=["basic"]),
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    """
    Get current user.
    """
    return await crud.user.get(
        db,
        models.User.id == user_id,
        options=[
            sa.orm.selectinload(
                models.User.member.and_(models.Member.active == True)
            ).selectinload(models.Member.product.and_(models.Product.active == True))
        ],
    )


@router.patch("", response_model=schemas.User)
async def update_user_me(
    update: schemas.UserUpdateMe,
    current_user_id: int = Security(deps.get_current_user_id, scopes=["basic"]),
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    """
    Update own user.
    """
    user = await crud.user.update(db, models.User.id == current_user_id, obj_in=update)
    await db.commit()
    return user


@router.delete("")
async def disable_myself(
    db: AsyncSession = Depends(deps.get_db),
    user_id: models.User = Security(deps.get_current_user_id, scopes=["basic"]),
):
    return await _delete_user(db, user_id)


@router.get("/members", response_model=schemas.Page[schemas.MemberUser])
async def member_list(
    paging: deps.Paging = Depends(deps.Paging),
    user_id: int = Security(deps.get_current_user_id, scopes=["basic"]),
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    """
    Get list of all memberships for me
    """
    return await crud.member.get_multi_page(
        db,
        models.Member.user_id == user_id,
        options=[
            sa.orm.selectinload(
                models.Member.user.and_(models.User.active == True)
            ).sa.orm.selectinload(
                models.Member.product.and_(models.Product.active == True)
            ),
        ],
        per_page=paging.per_page,
        page=paging.page,
        order_by=[models.Member.date_start.asc()],
    )


@router.delete("/members/{member_id}")
async def cancel_membership(
    user_id: int = Security(deps.get_current_user_id, scopes=["basic"]),
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    pass
