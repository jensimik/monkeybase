import io
from typing import Any, List

import looms
import sqlalchemy as sa
from fastapi import APIRouter, Depends, Response, Security, status
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from .. import crud, deps, models, schemas
from ..core.security import get_password_hash

router = APIRouter()


async def _delete_user(db, user_id):
    # actually just set active == False
    await crud.user.remove(db, models.User.id == user_id)

    # TODO: also disable/release any memberships this user have?
    # or instead reject delete until unsubscribed any memberships? (probably better)

    return True


@router.get("", response_model=schemas.Page[schemas.User])
async def user_list(
    paging: deps.Paging = Depends(deps.Paging),
    q: deps.Q = Depends(deps.Q),
    _: int = Security(deps.get_current_user_id, scopes=["admin"]),
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
            ).selectinload(
                models.Member.member_type.and_(models.MemberType.active == True)
            )
        ],
        *args,
        page=paging.page,
        per_page=paging.per_page,
        order_by=[models.User.name.asc(), models.User.id.asc()],
    )


@router.get("/{user_id}", response_model=schemas.User)
async def read_user_by_id(
    user_id: int,
    _: int = Security(deps.get_current_user_id, scopes=["admin"]),
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
            ).subqueryload(
                models.Member.member_type.and_(models.MemberType.active == True)
            )
        ],
    )


@router.post("", response_model=schemas.User, status_code=status.HTTP_201_CREATED)
async def create_user(
    create: schemas.UserCreate,
    _: int = Security(deps.get_current_user_id, scopes=["admin"]),
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    obj_in = create.dict(exclude_unset=True)
    password = obj_in.pop("password")
    obj_in["hashed_password"] = get_password_hash(password)
    user = await crud.user.create(db, obj_in=obj_in)
    await db.commit()
    return user


@router.patch("/{user_id}", response_model=schemas.User)
async def update_user(
    update: schemas.UserUpdate,
    user_id: int,
    _: int = Security(deps.get_current_user_id, scopes=["admin"]),
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


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    _: int = Security(deps.get_current_user_id, scopes=["admin"]),
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


# @router.get("/me", response_model=schemas.User)
# async def read_user_me(
#     user_id: models.User = Security(deps.get_current_user_id, scopes=["basic"]),
#     db: AsyncSession = Depends(deps.get_db),
# ) -> Any:
#     """
#     Get current user.
#     """
#     return await crud.user.get(
#         db,
#         models.User.id == user_id,
#         options=[
#             sa.orm.subqueryload(
#                 models.User.member.and_(models.Member.active == True)
#             ).subqueryload(
#                 models.Member.member_type.and_(models.MemberType.active == True)
#             )
#         ],
#     )


# @router.patch("/me", response_model=schemas.User)
# async def update_user_me(
#     update: schemas.UserUpdateMe,
#     current_user_id: int = Security(deps.get_current_user_id, scopes=["basic"]),
#     db: AsyncSession = Depends(deps.get_db),
# ) -> Any:
#     """
#     Update own user.
#     """
#     user = await crud.user.update(db, models.User.id == current_user_id, obj_in=update)
#     try:
#         await db.commit()
#         return user
#     except sa.exc.IntegrityError as ex:
#         await db.rollback()
#         raise ex


# @router.delete("/me")
# async def disable_myself(
#     db: AsyncSession = Depends(deps.get_db),
#     user_id: models.User = Security(deps.get_current_user_id, scopes=["basic"]),
# ):
#     return await _delete_user(db, user_id)


# @router.get("/{user_id}/member", response_model=schemas.Page[schemas.MemberMemberType])
# async def member_list(
#     user_id: int,
#     paging: deps.Paging = Depends(deps.Paging),
#     _: int = Security(deps.get_current_user_id, scopes=["admin"]),
#     db: AsyncSession = Depends(deps.get_db),
# ) -> Any:
#     """
#     Get list of all memberships for a specific user
#     """
#     return await crud.member.get_multi_page(
#         db,
#         (models.Member.user_id == user_id),
#         join=[models.Member.member_type],
#         options=[
#             sa.orm.subqueryload(models.Member.user.and_(models.User.active == True)),
#             sa.orm.subqueryload(
#                 models.Member.member_type.and_(models.MemberType.active == True)
#             ),
#         ],
#         page=paging.page,
#         per_page=paging.per_page,
#         order_by=[models.MemberType.name.asc(), models.MemberType.id.asc()],
#     )
