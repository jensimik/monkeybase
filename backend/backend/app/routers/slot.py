import datetime
from typing import Any, List
from uuid import UUID

import sqlalchemy as sa
from fastapi import APIRouter, Depends, HTTPException, Security, status
from loguru import logger

from .. import crud, deps, models, schemas
from ..db import AsyncSession
from ..utils import stripe
from ..utils.models_utils import PaymentStatusEnum

router = APIRouter()


@router.post("/{slot_key}/create-payment-intent", response_model=dict)
async def slot_create_payment_intent(
    slot_key: str,
    user: models.User = Security(deps.get_current_user, scopes=["basic"]),
    db: AsyncSession = Depends(deps.get_db),
):

    if slot := await crud.slot.get(
        db,
        models.Slot.user_id == user.id,
        models.Slot.key == slot_key,
        options=[
            sa.orm.selectinload(models.Slot.product.and_(models.Product.active == True))
        ],
        for_update=True,
    ):
        # ensure customer is created in stripe and update if already
        if not user.stripe_customer_id:
            stripe_customer_id = stripe.create_customer(
                email=user.email, name=user.name, metadata={"user_id": user.id}
            )
            user = await crud.user.update(
                db,
                models.User.id == user.id,
                obj_in={"stripe_customer_id": stripe_customer_id},
            )
        else:
            stripe.update_customer(
                stripe_customer_id=user.stripe_customer_id,
                email=user.email,
                name=user.name,
            )
        # if a payment intent is already created for this slot - then return it
        if slot.stripe_id:
            if slot.payment_status == PaymentStatusEnum.PENDING:
                return {"payment_intent_id": slot.stripe_id}
            elif slot.payment_status == PaymentStatusEnum.PAID:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="you have already paid this",
                )
            # else continue if FAILED and allow create a new one and retry
        payment_intent = stripe.create_payment_intent(
            stripe_customer_id=user.stripe_customer_id,
            amount=slot.product.price,
            statement_descriptor_suffix=f"{slot.product.name_short}",  # put the product name on the credit card statement as suffix
            metadata={"payment_for_product_id": slot.product_id, "slot_id": slot.id},
        )
        await crud.slot.update(
            db,
            models.Slot.id == slot.id,
            obj_in={
                "stripe_id": payment_intent.id,
                "payment_status": PaymentStatusEnum.PENDING,
            },
        )
        await db.commit()
        return {"client_secret": payment_intent.client_secret}
    else:
        logger.info("not found :-/")

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
