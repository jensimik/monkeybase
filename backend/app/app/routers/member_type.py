import sqlalchemy as sa
from typing import List, Any
from app import deps, schemas, models, crud
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, Security

router = APIRouter()


@router.post("", response_model=schemas.MemberType)
async def create_member_type(
    member_type: schemas.MemberTypeCreate,
    _: int = Security(deps.get_current_user_id, scopes=["admin"]),
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    """
    create a member_type
    """
    new_member_type = await crud.member_type.create(db, obj_in=member_type)
    await db.commit()
    return new_member_type


@router.get("", response_model=schemas.Page[schemas.MemberType])
async def member_type_list(
    l_qp: deps.ListQP = Depends(deps.ListQP),
    _: int = Security(deps.get_current_user_id, scopes=["basic"]),
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    """
    Get list of all member types
    """
    return await crud.member_type.get_multi_page(
        db,
        (models.MemberType.open_public == True),
        per_page=l_qp.per_page,
        page=l_qp.page,
        order_by=[models.MemberType.name.asc()],
    )


@router.get("/{member_type_id}/member", response_model=schemas.Page[schemas.MemberUser])
async def member_list(
    member_type_id: int,
    l_qp: deps.ListQP = Depends(deps.ListQP),
    _: int = Security(deps.get_current_user_id, scopes=["admin"]),
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    """
    Get list of all member for this membership_type
    """
    return await crud.member.get_multi_page(
        db,
        (models.Member.member_type_id == member_type_id),
        join=[models.Member.user],
        options=[sa.orm.contains_eager(models.Member.user)],
        per_page=l_qp.per_page,
        page=l_qp.page,
        order_by=[models.User.name.asc()],
    )
