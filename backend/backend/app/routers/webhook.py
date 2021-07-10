import datetime

import stripe
from dateutil.relativedelta import relativedelta
from fastapi import APIRouter, BackgroundTasks, Depends, status
from loguru import logger

from .. import crud, deps, models, schemas
from ..core.utils import MailTemplateEnum, send_transactional_email
from ..db import AsyncSession
from ..utils.models_utils import PaymentStatusEnum

router = APIRouter()


class SlotNotFound(Exception):
    pass


# async def payment_fail(db, payment_id, background_tasks):
#     if slot := await crud.slot.get(
#         db,
#         models.Slot.payment_id == payment_id,
#         models.Slot.reserved_until > datetime.datetime.utcnow(),
#         models.Slot.payment_status == PaymentStatusEnum.PENDING,
#         for_update=True,
#     ):
#         user = await crud.user.get(db, models.User.id == slot.user_id)
#         product = await crud.product.get(db, models.Product.id == slot.product_id)
#         slot = await crud.slot.update(
#             db,
#             models.Slot.id == slot.id,
#             obj_in={"payment_status": PaymentStatusEnum.FAIL},
#         )
#         await db.commit()
#         background_tasks.add_task(
#             send_transactional_email,
#             to_email=user.email,
#             template_id=MailTemplateEnum.PAYMENT_FAILED,
#             data={"product_name": product.name},
#         )
#         return True

#     raise SlotNotFound()


async def payment_succeeded(db, payment_id, background_tasks):
    if slot := await crud.slot.get(
        db,
        models.Slot.payment_id == payment_id,
        models.Slot.reserved_until > datetime.datetime.utcnow(),
        models.Slot.payment_status == PaymentStatusEnum.PENDING,
        for_update=True,
    ):
        logger.info("found")
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
                        "payment_id": slot.payment_id,
                    },
                )
            else:
                # create a new member object
                member = {
                    "user_id": slot.user_id,
                    "product_id": slot.product_id,
                    "payment_id": slot.payment_id,
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
                "payment_id": slot.payment_id,
            }
            await crud.member.create(db, obj_in=member)

        await db.commit()
        # send payment success email
        background_tasks.add_task(
            send_transactional_email,
            to_email=user.email,
            template_id=MailTemplateEnum.PAYMENT_SUCCEEDED,
            data={"product_name": product.name, "price": product.price},
        )
        return True

    raise SlotNotFound()


@router.post(
    "/netseasy",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(deps.neteasy_auth)],
)
async def netseasy_webhook(
    webhook_event: schemas.WebhookEvent,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(deps.get_db),
):
    if webhook_event.event == "payment.checkout.completed":
        await payment_succeeded(db, webhook_event.data["paymentId"], background_tasks)

    # elif webhook_event.event == "payment.charge.failed":
    #     await payment_fail(db, webhook_event.data["paymentId"], background_tasks)


@router.post("/stripe", response_model=dict, status_code=status.HTTP_200_OK)
async def stripe_event(
    background_tasks: BackgroundTasks,
    event: stripe.Event = Depends(deps.get_stripe_webhook_event),
    db: AsyncSession = Depends(deps.get_db),
):
    if event.type == "payment_intent.succeeded":
        await payment_succeeded(db, event.data.object.id, background_tasks)

    # elif event.type == "payment_intent.fail":
    #     await payment_fail(db, event.data.object.id, background_tasks)

    return {"everything": "is awesome"}
