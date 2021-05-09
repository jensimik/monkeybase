import sqlalchemy as sa
from typing import List, Any
from app import deps, schemas, models, crud
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, Security

router = APIRouter()


@router.get("", response_model=List[schemas.User])
async def user_list(
    _: int = Security(deps.get_current_user_id, scopes=["admin"]),
    db: AsyncSession = Depends(deps.get_db),
    limit: int = 100,
    skip: int = 0,
) -> Any:
    """
    Get list of all active users
    """
    return await crud.user.get_multi(
        db, order_by=models.User.name.asc(), skip=skip, limit=limit
    )


@router.get("/{user_id}", response_model=schemas.User)
async def read_user_by_id(
    user_id: int,
    _: models.User = Security(deps.get_current_admin_user, scopes=["admin"]),
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    """
    Get a specific user by id.
    """
    return await crud.user.get(db, id=user_id)


@router.get("/me", response_model=schemas.User)
async def read_user_me(
    current_user: models.User = Security(
        deps.get_current_active_user, scopes=["basic"]
    ),
) -> Any:
    """
    Get current user.
    """
    return current_user


@router.put("/me", response_model=schemas.User)
async def update_user_me(
    update: schemas.UserUpdateMe,
    current_user: models.User = Security(
        deps.get_current_active_user, scopes=["basic"]
    ),
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
