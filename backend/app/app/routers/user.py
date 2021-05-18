import sqlalchemy as sa
import looms
import io
from typing import List, Any
from uuid import UUID
from loguru import logger
from app import deps, schemas, models, crud
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, Security, Response

router = APIRouter()


@router.get("/me", response_model=schemas.User)
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
            sa.orm.subqueryload(
                models.User.member.and_(models.Member.active == True)
            ).subqueryload(
                models.Member.member_type.and_(models.MemberType.active == True)
            )
        ],
    )


@router.put("/me", response_model=schemas.User)
async def update_user_me(
    update: schemas.UserUpdateMe,
    current_user_id: models.User = Security(deps.get_current_user_id, scopes=["basic"]),
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    """
    Update own user.
    """
    user = await crud.user.update(db, models.User.id == current_user_id, obj_in=update)
    try:
        await db.commit()
        return user
    except sa.exc.IntegrityError as ex:
        await db.rollback()
        raise ex


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
                models.Member.member_type.and_(models.Membertype.active == True)
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


@router.get("/{user_id}/identicon.png", responses={200: {"content": {"image/png": {}}}})
async def read_user_by_id_identicon(
    user_id: int,
    _: int = Security(deps.get_current_user_id, scopes=["basic"]),
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


@router.get("/{user_id}/member", response_model=schemas.Page[schemas.MemberMemberType])
async def member_list(
    user_id: int,
    paging: deps.Paging = Depends(deps.Paging),
    _: int = Security(deps.get_current_user_id, scopes=["admin"]),
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    """
    Get list of all memberships for a specific user
    """
    return await crud.member.get_multi_page(
        db,
        (models.Member.user_id == user_id),
        join=[models.Member.member_type],
        options=[
            sa.orm.subqueryload(models.Member.user.and_(models.User.active == True)),
            sa.orm.subqueryload(
                models.Member.member_type.and_(models.MemberType.active == True)
            ),
        ],
        page=paging.page,
        per_page=paging.per_page,
        order_by=[models.MemberType.name.asc(), models.MemberType.id.asc()],
    )
