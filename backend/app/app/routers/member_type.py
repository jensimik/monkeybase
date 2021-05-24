import sqlalchemy as sa
import datetime
from typing import List, Any
from app import deps, schemas, models, crud
from app.models_utils import SlotTypeEnum
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, Security, status, HTTPException

router = APIRouter()


@router.post("", response_model=schemas.MemberType, status_code=status.HTTP_201_CREATED)
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
    paging: deps.Paging = Depends(deps.Paging),
    # _: int = Security(deps.get_current_user_id, scopes=["basic"]),
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    """
    Get list of all member types
    """
    return await crud.member_type.get_multi_page(
        db,
        per_page=paging.per_page,
        page=paging.page,
        order_by=[models.MemberType.name.asc()],
    )


@router.get("/{member_type_id}/member", response_model=schemas.Page[schemas.MemberUser])
async def member_list(
    member_type_id: int,
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
    return await crud.member.get_multi_page(
        db,
        (models.Member.member_type_id == member_type_id),
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


@router.post(
    "/{member_type_id}/get_or_create_reservation", response_model=schemas.MemberTypeSlot
)
async def get_or_create_reservation(
    member_type_id: int,
    user_id: models.User = Security(deps.get_current_user_id, scopes=["basic"]),
    db: AsyncSession = Depends(deps.get_db),
):
    # check if user is already a member of this membertype already?
    if await crud.member.get(
        db,
        models.Member.user_id == user_id,
        models.Member.member_type_id == member_type_id,
        models.Member.active == True,
    ):
        return HTTPException(
            status_code=422, detail="you are already a member of this membertype"
        )

    # first try to get a reservation in my name - usually from a waiting list
    # but can also be from a previous reservation if accidential hit page-refresh
    if slot := await crud.member_type_slot.get(
        db,
        models.MemberTypeSlot.member_type_id == member_type_id,
        models.MemberTypeSlot.user_id == user_id,
        models.MemberTypeSlot.reserved_until > datetime.datetime.utcnow(),
    ):
        return slot
    # then try to get an open slot if any available
    if slot := await crud.member_type_slot.get(
        db,
        models.MemberTypeSlot.member_type_id == member_type_id,
        models.MemberTypeSlot.slot_type == SlotTypeEnum.OPEN,
        models.MemberTypeSlot.reserved_until < datetime.datetime.utcnow(),
        order_by=[models.MemberTypeSlot.reserved_until.asc()],
        limit=True,
        for_update=True,
        skip_locked=True,
    ):
        # the slot is now locked in db (for_update=True) until commit or rollback
        # we update it with this users user_id and set reserved_until 30 minutes in future
        slot = await crud.member_type_slot.update(
            db,
            models.MemberTypeSlot.id == slot.id,
            obj_in={
                models.MemberTypeSlot.user_id.name: user_id,
                models.MemberTypeSlot.reserved_until.name: datetime.datetime.utcnow()
                + datetime.timedelta(minutes=30),
            },
        )
        await db.commit()
        # TODO: maybe signal to websocket that one slot is reserved
        # TODO: maybe create a background task to wait for 30 minutes
        # and trigger a recalculation of available slots on the websocket
        return slot

    # no slots available - sorry
    raise HTTPException(
        status_code=404, detail="no slots available currently - try again later"
    )
