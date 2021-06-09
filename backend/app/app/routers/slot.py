import datetime
from typing import Any, List

import sqlalchemy as sa
from fastapi import APIRouter, Depends, HTTPException, Security, status
from sqlalchemy.ext.asyncio import AsyncSession

from .. import crud, deps, models, schemas
from ..core import stripe
from ..utils.models_utils import StripeStatusEnum

router = APIRouter()


@router.post("/{slot_id}/create_payment_intent", response_model=dict)
async def slot_create_payment_intent(
    slot_id: int,
    user: models.User = Security(deps.get_current_user, scopes=["basic"]),
    db: AsyncSession = Depends(deps.get_db),
):
    if slot := await crud.slot.get(
        db,
        models.Slot.user_id == user.id,
        models.Slot.id == slot_id,
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
            if slot.stripe_status == StripeStatusEnum.PENDING:
                return {"payment_intent_id": slot.stripe_id}
            elif slot.stripe_status == StripeStatusEnum.PAID:
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
                "stripe_status": StripeStatusEnum.PENDING,
            },
        )
        await db.commit()
        return {"client_secret": payment_intent.client_secret}

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
