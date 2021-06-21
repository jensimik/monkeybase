import datetime
from typing import Any, Union

import sqlalchemy as sa
from fastapi import APIRouter, Depends, HTTPException, Security, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from .. import crud, deps, models, schemas

router = APIRouter()


@router.post(
    "",
    response_model=schemas.Event,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Security(deps.get_current_user_id, scopes=["admin"])],
)
async def create_event(
    event: schemas.EventCreate,
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    """
    create a event
    """
    new_event = await crud.event.create(db, obj_in=event)
    await db.commit()
    return new_event


@router.get("", response_model=schemas.Page[schemas.Event])
async def event_list(
    paging: deps.Paging = Depends(deps.Paging),
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    """
    Get list of all events
    """
    return await crud.event.get_multi_page(
        db,
        per_page=paging.per_page,
        page=paging.page,
        order_by=[models.Event.name.asc()],
    )


@router.get("/{event_id}", response_model=schemas.Event)
async def get_event(
    event_id: int,
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    """
    Get a event
    """
    if event := await crud.event.get(db, models.Event.id == event_id):
        return event
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="event not found")


@router.patch(
    "/{event_id}",
    response_model=schemas.Event,
    dependencies=[Security(deps.get_current_user_id, scopes=["admin"])],
)
async def update_event(
    event_id: int,
    update: schemas.EventUpdate,
    db: AsyncSession = Depends(deps.get_db),
):
    """update a event"""

    if event := await crud.event.update(db, models.Event.id == event_id, obj_in=update):
        await db.commit()
        return event
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="event not found")


@router.delete(
    "/{event_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Security(deps.get_current_user_id, scopes=["admin"])],
)
async def delete_event(
    event_id: int,
    db: AsyncSession = Depends(deps.get_db),
):
    """disable a event"""

    if await crud.member.count(db, models.Member.product_id == event_id):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="cannot disable event when active members on it",
        )

    await crud.event.remove(db, models.Event.id == event_id)
    await db.commit()


@router.post(
    "/{event_id}/reserve_a_slot",
    response_model=Union[schemas.WaitingList, schemas.Slot],
)
async def reserve_a_slot(
    response: Response,
    event_id: int,
    user: models.User = Security(deps.get_current_user, scopes=["basic"]),
    db: AsyncSession = Depends(deps.get_db),
) -> Union[models.Slot, models.WaitingList]:
    # first try to get a reservation in my name - usually created from a waiting list
    # or if a slot have been made to renew a membership
    # but can also be from a previous open reservation slot if accidential hit page-refresh
    if slot := await crud.slot.get(
        db,
        models.Slot.product_id == event_id,
        models.Slot.user_id == user.id,
        models.Slot.reserved_until > datetime.datetime.utcnow(),
    ):
        return slot

    # if already on waitinglist then return that fast
    if waiting := await crud.waiting_list.get(
        db,
        models.WaitingList.product_id == event_id,
        models.WaitingList.user_id == user.id,
    ):
        response.status_code = status.HTTP_429_TOO_MANY_REQUESTS
        return waiting

    # check if user is already a member of this membertype already
    if member := await crud.member.get(
        db,
        models.Member.user_id == user.id,
        models.Member.product_id == event_id,
        models.Member.active == True,
    ):
        # if outside resubscribe window then raise error
        raise HTTPException(
            status_code=422,
            detail="you are already a member of this event",
        )

    # if not a member already - then try to get an open available slot
    if slot := await crud.slot.get(
        db,
        models.Slot.product_id == event_id,
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
        db, obj_in={"product_id": event_id, "user_id": user.id}
    ):
        await db.commit()
        response.status_code = status.HTTP_429_TOO_MANY_REQUESTS
        return waiting

    # last resort
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="unknown error"
    )


@router.get(
    "/{event_id}/members",
    response_model=schemas.Page[schemas.MemberUser],
    dependencies=[Security(deps.get_current_user_id, scopes=["admin"])],
)
async def member_list(
    event_id: int,
    paging: deps.Paging = Depends(deps.Paging),
    q: deps.Q = Depends(deps.Q),
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    """
    Get list of all member for this event
    """
    args = [models.Member.product_id == event_id]
    if q.q:
        args.append(
            sa.or_(
                sa.func.lower(models.User.name).contains(q.q.lower(), autoescape=True),
                sa.func.lower(models.User.email).contains(q.q.lower(), autoescape=True),
            )
        )
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
        order_by=[models.User.name.asc(), models.Member.id.asc()],
    )
