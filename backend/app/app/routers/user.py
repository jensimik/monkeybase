import sqlalchemy as sa
from typing import List, Any
from uuid import UUID
from loguru import logger
from app import deps, schemas, models, crud
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, Security

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
            sa.orm.subqueryload(models.User.member).subqueryload(
                models.Member.member_type
            )
        ],
    )


@router.put("/me", response_model=schemas.User)
async def update_user_me(
    update: schemas.UserUpdateMe,
    current_user: models.User = Security(deps.get_current_user, scopes=["basic"]),
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    """
    Update own user.
    """
    user = await crud.user.update(db, db_obj=current_user, obj_in=update)
    try:
        await db.commit()
        return user
    except sa.exc.IntegrityError as ex:
        await db.rollback()
        raise ex
        # raise exc.DuplicatedEntryError("The city is already stored")


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
            sa.orm.selectinload(models.User.member).selectinload(
                models.Member.member_type
            )
        ],
        *args,
        page=paging.page,
        per_page=paging.per_page,
        order_by=[models.User.name.asc(), models.User.id.asc()],
    )


@router.get("/{uuid}", response_model=schemas.User)
async def read_user_by_id(
    uuid: UUID,
    _: int = Security(deps.get_current_user_id, scopes=["admin"]),
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    """
    Get a specific user by id.
    """
    return await crud.user.get(
        db,
        models.User.uuid == uuid,
        options=[
            sa.orm.subqueryload(models.User.member).subqueryload(
                models.Member.member_type
            )
        ],
    )


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
        options=[sa.orm.contains_eager(models.Member.member_type)],
        page=paging.page,
        per_page=paging.per_page,
        order_by=[models.MemberType.name.asc(), models.MemberType.id.asc()],
    )
