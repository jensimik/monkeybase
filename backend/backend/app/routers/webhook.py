import datetime
import hashlib
from fastapi.exceptions import HTTPException

import stripe
from dateutil.relativedelta import relativedelta
from fastapi import APIRouter, BackgroundTasks, Depends, Request, status
from loguru import logger

from .. import crud, deps, models
from ..core.config import settings
from ..core.utils import MailTemplateEnum, send_transactional_email
from ..db import AsyncSession
from ..utils.models_utils import PaymentStatusEnum

router = APIRouter()


class SlotNotFound(Exception):
    pass


async def payment_fail(db, slot):
    user = await crud.user.get(db, models.User.id == slot.user_id)
    product = await crud.product.get(db, models.Product.id == slot.product_id)
    slot = await crud.slot.update(
        db,
        models.Slot.id == slot.id,
        obj_in={"payment_status": PaymentStatusEnum.FAIL},
    )
    return user, slot, product


async def payment_succeeded(db, slot):
    # get the slot for this payment
    user = await crud.user.get(db, models.User.id == slot.user_id)
    product = await crud.product.get(db, models.Product.id == slot.product_id)
    await crud.slot.update(
        db,
        models.Slot.id == slot.id,
        obj_in={
            "payment_status": PaymentStatusEnum.PAID,
            "reserved_until": datetime.datetime.utcnow(),
        },
    )
    if isinstance(product, models.MemberType):
        # check if already a member of this membertype - then extend until next year
        if member_exist := await crud.member.get(
            db,
            models.Member.user_id == user.id,
            models.Member.product_id == product.id,
        ):
            # ok now we just extend the membership for another year
            member = await crud.member.update(
                db,
                models.Member.id == member_exist.id,
                obj_in={
                    "date_end": member_exist.date_end
                    + relativedelta(years=1, nlyearday=15),
                    "stripe_id": slot.stripe_id,
                },
            )
        else:
            # create a new member object
            member = {
                "user_id": slot.user_id,
                "product_id": slot.product_id,
                "stripe_id": slot.stripe_id,
                "date_start": datetime.date.today(),
                "date_end": datetime.date.today()
                + relativedelta(years=1, nlyearday=15),
            }
        await crud.member.create(db, obj_in=member)
    elif isinstance(product, models.Event):
        member = {
            "user_id": slot.user_id,
            "product_id": slot.product_id,
            "date_start": slot.product.date_start,
            "date_end": slot.product.date_end,
            "stripe_id": slot.stripe_id,
        }
        await crud.member.create(db, obj_in=member)

    return user, slot, product


@router.post(
    "/bambora-webhook/{slot_id}", response_model=dict, status_code=status.HTTP_200_OK
)
async def bambora_webhook(
    slot_id: int,
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(deps.get_db),
):
    # check the md5 hash of query params
    hash_received = request.query_params["hash"]
    hash_calculated = hashlib.md5(
        "".join([v for k, v in request.query_params if k != "hash"])
        + settings.BAMBORA_MD5_KEY
    ).hexdigest()
    if hash_received != hash_calculated:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)

    if slot := await crud.slot.get(db, models.Slot.id == slot_id):
        user, _, product = await payment_succeeded(db, slot)
        await db.commit()
        background_tasks.add_task(
            send_transactional_email,
            to_email=user.email,
            template_id=MailTemplateEnum.PAYMENT_SUCCEEDED,
            data={"product_name": product.name, "price": product.price},
        )

    return {"everything": "is awesome"}


@router.post("/stripe-webhook", response_model=dict, status_code=status.HTTP_200_OK)
async def stripe_event(
    background_tasks: BackgroundTasks,
    event: stripe.Event = Depends(deps.get_stripe_webhook_event),
    db: AsyncSession = Depends(deps.get_db),
):
    if event.type == "payment_intent.fail":
        if slot := await crud.slot.get(
            db,
            models.Slot.stripe_id == event.data.object.id,
            models.Slot.reserved_until > datetime.datetime.utcnow(),
            models.Slot.payment_status == PaymentStatusEnum.PENDING,
            for_update=True,
        ):
            user, _, product = await payment_fail(db, slot)
            await db.commit()
            background_tasks.add_task(
                send_transactional_email,
                to_email=user.email,
                template_id=MailTemplateEnum.PAYMENT_FAILED,
                data={"product_name": product.name},
            )

    elif event.type == "payment_intent.succeeded":
        if slot := await crud.slot.get(
            db,
            models.Slot.stripe_id == event.data.object.id,
            models.Slot.reserved_until > datetime.datetime.utcnow(),
            models.Slot.payment_status == PaymentStatusEnum.PENDING,
            for_update=True,
        ):
            user, _, product = await payment_succeeded(db, slot)
            await db.commit()
            background_tasks.add_task(
                send_transactional_email,
                to_email=user.email,
                template_id=MailTemplateEnum.PAYMENT_SUCCEEDED,
                data={"product_name": product.name, "price": product.price},
            )

    return {"everything": "is awesome"}
