import datetime

import sqlalchemy as sa
from dateutil.relativedelta import relativedelta
from fastapi import APIRouter, BackgroundTasks, Depends, status
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from ..utils.models_utils import StripeStatusEnum

import stripe

from .. import crud, deps, models

router = APIRouter()


@router.post("/stripe-webhook", response_model=dict, status_code=status.HTTP_200_OK)
async def stripe_event(
    background_tasks: BackgroundTasks,
    event: stripe.Event = Depends(deps.stripe_webhook_event),
    db: AsyncSession = Depends(deps.get_db),
):
    if event.type == "payment_intent.fail":
        payment_intent = event.data
        if slot := await crud.slot.get(
            db,
            models.Slot.stripe_id == payment_intent.id,
            models.Slot.valid_until > datetime.datetime.utcnow(),
            models.Slot.stripe_status == StripeStatusEnum.PENDING,
            options=[
                sa.orm.selectinload(
                    models.Slot.product.and_(models.Product.active == True)
                ),
                sa.orm.selectinload(models.Slot.user.and_(models.User.active == True)),
            ],
            for_update=True,
        ):
            await crud.slot.update(
                db,
                models.Slot.id == slot.id,
                obj_in={"stripe_status": StripeStatusEnum.FAIL},
            )
            await db.commit()
            # TODO: send some kind of message/email to user saying that payment failed?

    elif event.type == "payment_intent.succeeded":
        payment_intent = event.data
        logger.info(payment_intent)
        # get the slot for this payment
        if slot := await crud.slot.get(
            db,
            models.Slot.stripe_id == payment_intent.id,
            models.Slot.valid_until > datetime.datetime.utcnow(),
            models.Slot.stripe_status == StripeStatusEnum.PENDING,
            options=[
                sa.orm.selectinload(
                    models.Slot.product.and_(models.Product.active == True)
                ),
                sa.orm.selectinload(models.Slot.user.and_(models.User.active == True)),
            ],
            for_update=True,
        ):
            await crud.slot.update(
                db,
                models.Slot.id == slot.id,
                obj_in={"stripe_status": StripeStatusEnum.CAPTURED},
            )
            if isinstance(slot.product, models.MemberType):
                member = {
                    "user_id": slot.user_id,
                    "product_id": slot.product_id,
                    "date_start": datetime.date.today(),
                    "date_end": datetime.date.today()
                    + relativedelta(years=1, yearday=1),
                    "stripe_id": slot.stripe_id,
                }
            elif isinstance(slot.product, models.Event):
                member = {
                    "user_id": slot.user_id,
                    "product_id": slot.product_id,
                    "date_start": slot.product.date_start,
                    "date_end": slot.product.date_end,
                    "stripe_id": slot.stripe_id,
                }
            # then create the member in db
            await crud.member.create(db, obj_in=member)
            await db.commit()
            # trigger a welcome message/etc for the event/membertype
            background_tasks.add_task(slot.product.send_welcome, slot.user)
    return {"everything": "is awesome"}
