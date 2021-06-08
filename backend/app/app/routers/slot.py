import datetime
from typing import Any, List

import sqlalchemy as sa
from fastapi import APIRouter, Depends, HTTPException, Security, status
from sqlalchemy.ext.asyncio import AsyncSession

from .. import crud, deps, models, schemas
from ..core import stripe

router = APIRouter()


@router.post("/{slot_id}/create_payment_intent", response_model=dict)
def slot_create_payment_intent(
    member_type_id: int,
    user_id: models.User = Security(deps.get_current_user_id, scopes=["basic"]),
    db: AsyncSession = Depends(deps.get_db),
):
    pass
