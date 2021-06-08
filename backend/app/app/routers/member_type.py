import datetime
from typing import Any, List

import sqlalchemy as sa
from fastapi import APIRouter, Depends, HTTPException, Security, status
from sqlalchemy.ext.asyncio import AsyncSession

from .. import crud, deps, models, schemas
from ..core import stripe

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


@router.patch("/{member_type_id}", response_model=schemas.MemberType)
async def update_member_type(
    member_type_id: int,
    update: schemas.MemberTypeUpdate,
    _: models.User = Security(deps.get_current_user_id, scopes=["admin"]),
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


@router.delete("/{member_type_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_memeber_type(
    member_type_id: int,
    _: models.User = Security(deps.get_current_user_id, scopes=["admin"]),
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


@router.post("/{member_type_id}/reserve_a_slot", response_model=schemas.Slot)
async def reserve_a_slot(
    member_type_id: int,
    user: models.User = Security(deps.get_current_user, scopes=["basic"]),
    db: AsyncSession = Depends(deps.get_db),
):
    # first try to get a reservation in my name - usually from a waiting list
    # or if a slot have been made to renew a membership
    # but can also be from a previous open reservation slot if accidential hit page-refresh
    if slot := await crud.slot.get(
        db,
        models.Slot.product_id == member_type_id,
        models.Slot.user_id == user.id,
        models.Slot.reserved_until > datetime.datetime.utcnow(),
    ):
        return slot

    # check if user is already a member of this membertype already
    if await crud.member.get(
        db,
        models.Member.user_id == user.id,
        models.Member.member_type_id == member_type_id,
        models.Member.active == True,
    ):
        return HTTPException(
            status_code=422, detail="you are already a member of this membertype"
        )

    # then try to get an open available slot
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

        # # ensure user is created in stripe as a customer
        # if user.stripe_customer_id:
        #     stripe.update_customer(email=user.email, name=user.name)
        # else:
        #     stripe_customer_id = stripe.create_customer(
        #         email=user.email, name=user.name
        #     )
        #     user = await crud.user.update(
        #         db,
        #         models.User.id == user.id,
        #         obj_in={"stripe_customer_id": stripe_customer_id},
        # )

        # TODO: maybe signal to websocket that one slot is reserved
        # TODO: maybe create a background task to wait for 30 minutes
        # and trigger a recalculation of available slots on the websocket
        return slot

    # no slots available - sorry
    raise HTTPException(
        status_code=404, detail="no slots available currently - try again later"
    )


# @router.post("/{member_type_id}/", response_model=schemas.Member)
# async def use_a_slot(
#     member_type_id: int,
#     member: schemas.MemberCreateMe,
#     user_id: models.User = Security(deps.get_current_user_id, scopes=["basic"]),
#     db: AsyncSession = Depends(deps.get_db),
# ):
#     slot = await crud.member_type_slot.get(
#         db,
#         models.MemberTypeSlot.key == member.key,
#         models.MemberTypeSlot.user_id == user_id,
#         models.MemberTypeSlot.member_type_id == member_type_id,
#         models.MemberTypeSlot.reserved_until > datetime.datetime.utcnow(),
#         for_update=True,
#     )
#     if not slot:
#         raise HTTPException(
#             status_code=401,
#             detail="sorry, your reservation does not exist or has expired",
#         )
#     # disable the slot if successfull
#     await crud.member_type_slot.remove(db, models.MemberTypeSlot.id == slot.id)

#     # TODO: validate member.payment_id?
#     # TODO: and mark the payment reservation to be captured at next capture run

#     date_start = datetime.date.utcnow()
#     # ends last day of year/new years - have to renew membership before that date!
#     date_end = datetime.date(
#         year=date_start.year + 1, month=1, day=1
#     ) - datetime.timedelta(days=1)
#     member = await crud.member.create(
#         db,
#         schemas.MemberCreate(
#             user_id=user_id,
#             member_type_id=member_type_id,
#             payment_id=member.payment_id,
#             date_start=date_start,
#             date_end=date_end,
#         ),
#     )

#     await db.commit()

#     return member


# @router.post("/{member_type_id}/create_payment_intent")
# async def create_payment_intent(
#     member_type_id: int,
#     user_id: models.User = Security(deps.get_current_user_id, scopes=["basic"]),
#     db: AsyncSession = Depends(deps.get_db),
# ):
#     pass


@router.get(
    "/{member_type_id}/members", response_model=schemas.Page[schemas.MemberUser]
)
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
