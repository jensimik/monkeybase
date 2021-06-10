import datetime
from typing import Any, Union

import sqlalchemy as sa
from fastapi import APIRouter, Depends, HTTPException, Security, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from .. import crud, deps, models, schemas
from ..core import stripe

router = APIRouter()


@router.post(
    "",
    response_model=schemas.MemberType,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Security(deps.get_current_user_id, scopes=["admin"])],
)
async def create_member_type(
    member_type: schemas.MemberTypeCreate,
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


@router.get("/{member_type_id}", response_model=schemas.MemberType)
async def get_member_type(
    member_type_id: int,
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    """
    Get a member type
    """
    if member_type := await crud.member_type.get(
        db, models.MemberType.id == member_type_id
    ):
        return member_type
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="membertype not found"
    )


@router.patch(
    "/{member_type_id}",
    response_model=schemas.MemberType,
    dependencies=[Security(deps.get_current_user_id, scopes=["admin"])],
)
async def update_member_type(
    member_type_id: int,
    update: schemas.MemberTypeUpdate,
    db: AsyncSession = Depends(deps.get_db),
):
    """update a member_type"""

    if member_type := await crud.member_type.update(
        db, models.MemberType.id == member_type_id, obj_in=update
    ):
        await db.commit()
        return member_type
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="membertype not found"
    )


@router.delete(
    "/{member_type_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Security(deps.get_current_user_id, scopes=["admin"])],
)
async def delete_memeber_type(
    member_type_id: int,
    db: AsyncSession = Depends(deps.get_db),
):
    """disable a member_type"""

    if await crud.member.count(db, models.Member.product_id == member_type_id):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="cannot disable member_type when active members on it",
        )

    await crud.member_type.remove(db, models.MemberType.id == member_type_id)
    await db.commit()


@router.post(
    "/{member_type_id}/reserve_a_slot",
    response_model=Union[schemas.WaitingList, schemas.Slot],
)
async def reserve_a_slot(
    response: Response,
    member_type_id: int,
    user: models.User = Security(deps.get_current_user, scopes=["basic"]),
    db: AsyncSession = Depends(deps.get_db),
) -> Union[models.Slot, models.WaitingList]:
    # first try to get a reservation in my name - usually created from a waiting list
    # or if a slot have been made to renew a membership
    # but can also be from a previous open reservation slot if accidential hit page-refresh
    if slot := await crud.slot.get(
        db,
        models.Slot.product_id == member_type_id,
        models.Slot.user_id == user.id,
        models.Slot.reserved_until > datetime.datetime.utcnow(),
    ):
        return slot

    # if already on waitinglist then return that fast
    if waiting := await crud.waiting_list.get(
        db,
        models.WaitingList.product_id == member_type_id,
        models.WaitingList.user_id == user.id,
    ):
        response.status_code = status.HTTP_429_TOO_MANY_REQUESTS
        return waiting

    # check if user is already a member of this membertype already
    if member := await crud.member.get(
        db,
        models.Member.user_id == user.id,
        models.Member.product_id == member_type_id,
        models.Member.active == True,
    ):
        # if already a member - then you are allowed to resubscribe from 1 december until exire - create a new slot for you here
        today = datetime.date.today()
        if any([today.month == 12, today.month == 1 and today <= member.date_end]):
            if slot := await crud.slot.create(
                db,
                obj_in={
                    "user_id": user.id,
                    "product_id": member_type_id,
                    "reserved_until": datetime.datetime.utcnow()
                    + datetime.timedelta(days=14),
                },
            ):
                await db.commit()
                return slot
        # if outside resubscribe window then raise error
        raise HTTPException(
            status_code=422,
            detail="you are already a member of this membertype and outside resubscribe window",
        )

    # if not a member already - then try to get an open available slot
    if slot := await crud.slot.get(
        db,
        models.Slot.product_id == member_type_id,
        models.Slot.user_id.is_(None),
        order_by=[models.Slot.reserved_until.asc()],
        limit=True,
        for_update=True,
        skip_locked=True,
    ):
        # the slot is now locked in db (for_update=True) until commit or rollback
        # we update it with this users user_id and set reserved_until 2 days in future
        slot = await crud.slot.update(
            db,
            models.Slot.id == slot.id,
            obj_in=schemas.SlotUpdate(
                user_id=user.id,
                reserved_until=datetime.datetime.utcnow() + datetime.timedelta(days=2),
            ),
        )
        await db.commit()
        return slot

    # if no available slot then put on waitinglist
    if waiting := await crud.waiting_list.create(
        db, obj_in={"product_id": member_type_id, "user_id": user.id}
    ):
        await db.commit()
        response.status_code = status.HTTP_429_TOO_MANY_REQUESTS
        return waiting

    # last resort
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="unknown error"
    )


@router.get(
    "/{member_type_id}/members",
    response_model=schemas.Page[schemas.MemberUser],
    dependencies=[Security(deps.get_current_user_id, scopes=["admin"])],
)
async def member_list(
    member_type_id: int,
    paging: deps.Paging = Depends(deps.Paging),
    q: deps.Q = Depends(deps.Q),
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
