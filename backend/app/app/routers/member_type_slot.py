import datetime
from typing import Any, List, Optional

import sqlalchemy as sa
from app import crud, deps, models, schemas
from app.models_utils import SlotTypeEnum
from fastapi import APIRouter, Depends, HTTPException, Security
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


# @router.get("", response_model=schemas.Page[schemas.MemberTypeSlot])
# async def get_slots(
#     paging: deps.Paging = Depends(deps.Paging),
#     member_type_id: Optional[int] = None,
#     _: models.User = Security(deps.get_current_user_id, scopes=["admin"]),
#     db: AsyncSession = Depends(deps.get_db),
# ):
#     args = []
#     if member_type_id is not None:
#         args.append(models.MemberTypeSlot.member_type_id == member_type_id)
#     return await crud.member_type_slot.get_multi_page(
#         db,
#         *args,
#         page=paging.page,
#         per_page=paging.per_page,
#         order_by=[models.MemberTypeSlot.id.asc()],
#     )


# @router.post("", response_model=schemas.MemberTypeSlot)
# async def create_slot(
#     _: models.User = Security(deps.get_current_user_id, scopes=["admin"]),
#     db: AsyncSession = Depends(deps.get_db),
# ):
#     pass


# @router.get("/{slot_id}", response_model=schemas.MemberTypeSlot)
# async def get_slot(
#     slot_id: int,
#     _: models.User = Security(deps.get_current_user_id, scopes=["admin"]),
#     db: AsyncSession = Depends(deps.get_db),
# ):
#     pass


# @router.delete("/{slot_id}")
# async def disable_slot(
#     slot_id: int,
#     _: models.User = Security(deps.get_current_user_id, scopes=["admin"]),
#     db: AsyncSession = Depends(deps.get_db),
# ):
#     pass
