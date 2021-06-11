import datetime
from typing import Any, Optional

import sqlalchemy as sa
from fastapi import APIRouter, Depends, HTTPException, Security, status
from sqlalchemy.ext.asyncio import AsyncSession

from .. import crud, deps, models, schemas

router = APIRouter()


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=schemas.Member,
    dependencies=[Security(deps.get_current_user_id, scopes=["admin"])],
)
async def create_membership(
    create: schemas.MemberCreate,
    db: AsyncSession = Depends(deps.get_db),
):
    return await crud.member.create(db, obj_in=create)


@router.patch(
    "/{member_id}",
    response_model=schemas.Member,
    dependencies=[Security(deps.get_current_user_id, scopes=["admin"])],
)
async def modify_membership(
    member_id: int,
    update: schemas.MemberUpdate,
    db: AsyncSession = Depends(deps.get_db),
):
    if member := await crud.member.get(db, models.Member.id == member_id):
        return await crud.member.update(
            db,
            models.Member.id == member.id,
            obj_in=update,
        )

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="membership not found"
    )


@router.delete(
    "/{member_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Security(deps.get_current_user_id, scopes=["admin"])],
)
async def deactivate_membership(
    member_id: int,
    db: AsyncSession = Depends(deps.get_db),
):
    if member := await crud.member.get(db, models.Member.id == member_id):
        return await crud.member.update(
            db,
            models.Member.id == member.id,
            obj_in={"date_end": datetime.date.today() - datetime.timedelta(days=1)},
        )

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="membership not found"
    )


@router.get(
    "",
    response_model=schemas.Page[schemas.MemberUser],
    dependencies=[Security(deps.get_current_user_id, scopes=["admin"])],
)
async def member_list(
    product_id: Optional[int] = None,
    paging: deps.Paging = Depends(deps.Paging),
    q: deps.Q = Depends(deps.Q),
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    """
    Get list of all member for this member_type
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
    if product_id is not None:
        args.append(models.Member.product_id == product_id)

    return await crud.member.get_multi_page(
        db,
        join=[models.Member.user],
        *args,
        options=[
            sa.orm.selectinload(models.Member.user.and_(models.User.active == True)),
            sa.orm.selectinload(
                models.Member.product.and_(models.Product.active == True)
            ),
        ],
        per_page=paging.per_page,
        page=paging.page,
        order_by=[models.User.name.asc()],
    )
