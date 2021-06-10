import io
from os import stat
from typing import Any, List

import looms
import sqlalchemy as sa
from fastapi import APIRouter, Depends, Response, Security, status, HTTPException
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from .. import crud, deps, models, schemas
from ..core.security import get_password_hash

router = APIRouter()


async def _delete_user(db: AsyncSession, user_id: int):
    active_memberships = await crud.member.get_multi(
        db, models.Member.user_id == user_id
    )
    if active_memberships:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="cannot disable user with active membership",
        )

    await crud.user.remove(db, models.User.id == user_id)
    await db.commit()


@router.get(
    "",
    response_model=schemas.Page[schemas.User],
    dependencies=[Security(deps.get_current_user_id, scopes=["admin"])],
)
async def user_list(
    paging: deps.Paging = Depends(deps.Paging),
    q: deps.Q = Depends(deps.Q),
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    """
    Get list of all active users
    """
    # search query if searching with q parameter
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

    return await crud.user.get_multi_page(
        db,
        options=[
            sa.orm.selectinload(
                models.User.member.and_(models.Member.active == True)
            ).selectinload(models.Member.product.and_(models.Product.active == True))
        ],
        *args,
        page=paging.page,
        per_page=paging.per_page,
        order_by=[models.User.name.asc(), models.User.id.asc()],
    )


@router.get(
    "/{user_id}",
    response_model=schemas.User,
    dependencies=[Security(deps.get_current_user_id, scopes=["admin"])],
)
async def read_user_by_id(
    user_id: int,
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    """
    Get a specific user by id.
    """
    return await crud.user.get(
        db,
        models.User.id == user_id,
        options=[
            sa.orm.subqueryload(
                models.User.member.and_(models.Member.active == True)
            ).subqueryload(models.Member.product.and_(models.Product.active == True))
        ],
    )


@router.post(
    "",
    response_model=schemas.User,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Security(deps.get_current_user_id, scopes=["admin"])],
)
async def create_user(
    create: schemas.UserCreate,
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    obj_in = create.dict(exclude_unset=True)
    password = obj_in.pop("password")
    obj_in["hashed_password"] = get_password_hash(password)
    user = await crud.user.create(db, obj_in=obj_in)
    await db.commit()
    return user


@router.patch(
    "/{user_id}",
    response_model=schemas.User,
    dependencies=[Security(deps.get_current_user_id, scopes=["admin"])],
)
async def update_user(
    update: schemas.UserUpdate,
    user_id: int,
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    """
    Update user.
    """
    user = await crud.user.update(db, models.User.id == user_id, obj_in=update)
    try:
        await db.commit()
        return user
    except sa.exc.IntegrityError as ex:
        await db.rollback()
        raise ex


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Security(deps.get_current_user_id, scopes=["admin"])],
)
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(deps.get_db),
):
    """disable user"""

    await _delete_user(db, user_id)


@router.get("/{user_id}/identicon.png", responses={200: {"content": {"image/png": {}}}})
async def read_user_by_id_identicon(
    user_id: int,
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    """
    Get a identicon for a specific user by id.
    """
    user = await crud.user.get(db, models.User.id == user_id)

    img = looms.generate(user.email)
    img = img.quantize(method=2)

    with io.BytesIO() as bi:
        img.save(bi, "png")
        bi.seek(0)
        return Response(content=bi.getvalue(), media_type="image/png")
