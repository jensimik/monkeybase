import datetime
from typing import List

import sqlalchemy as sa
from fastapi import APIRouter, Depends, HTTPException, Security, status
from fastapi.security.api_key import APIKeyHeader
from pydantic import BaseModel

from .. import crud, deps, models, schemas
from ..core.config import settings
from ..core.utils import tz_now
from ..db import AsyncSession
from ..utils.models_utils import DoorAccessEnum

router = APIRouter()


api_key_header = APIKeyHeader(name="api_key", auto_error=True)


class DoorAccessQuery(BaseModel):
    key: str


def get_api_key(api_key: str = Security(api_key_header)):
    if api_key != settings.DOOR_API_KEY:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="go away")


@router.post(
    "/door-access",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Security(get_api_key)],
)
async def access_door(
    q: DoorAccessQuery,
    db: AsyncSession = Depends(deps.get_db),
):
    if user := await crud.user.get(
        db,
        models.User.door_id == q.key,
        options=[
            sa.orm.selectinload(
                models.User.member.and_(models.Member.active == True)
            ).selectinload(models.Member.product.and_(models.Product.active == True))
        ],
    ):
        for member in user.member:
            if not isinstance(member.product, models.MemberType):
                continue
            if any(
                [
                    member.product.door_access == DoorAccessEnum.FULL,
                    member.product.door_access == DoorAccessEnum.MORNING
                    and (7 <= tz_now().hour <= 15),
                ]
            ):
                await crud.door_event.create(db, obj_in={"user_id": user.id})
                await db.commit()
                return
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)


@router.get("/door-data", response_model=List[datetime.datetime])
async def public_door_data(db: AsyncSession = Depends(deps.get_db)):
    entries = await crud.door_event.get_multi(
        db,
        models.Doorevent.created_at
        > datetime.datetime.utcnow() - datetime.timedelta(days=180),
        order_by=[models.Doorevent.created_at.desc()],
        only_active=False,
    )
    return [x.created_at for x in entries]
