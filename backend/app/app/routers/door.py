import datetime
from typing import Any

import sqlalchemy as sa
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Security, status
from fastapi.security.api_key import APIKeyHeader
from loguru import logger
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from .. import crud, deps, models, schemas
from ..core.config import settings
from ..models_utils import DoorAccessEnum

router = APIRouter()


api_key_header = APIKeyHeader(name="access_token")


class DoorAccess(BaseModel):
    status: bool


class DoorAccessQuery(BaseModel):
    key: str


async def log_door_event(
    user_id: int,
    db: AsyncSession = Depends(deps.get_db),
):
    await crud.door_event.create(db, obj_in={models.Doorevent.user_id.name: user_id})
    await db.commit()


@router.post("", response_model=DoorAccess)
async def access_door(
    q: DoorAccessQuery,
    background_tasks: BackgroundTasks,
    api_key: str = Security(api_key_header),
    db: AsyncSession = Depends(deps.get_db),
):
    if api_key != settings.DOOR_API_KEY:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="go away")
    now = datetime.datetime.utcnow()
    user = await crud.user.get(
        db,
        models.User.door_id == q.key,
        options=[
            sa.orm.subqueryload(
                models.User.member.and_(models.Member.active == True)
            ).subqueryload(
                models.Member.member_type.and_(models.MemberType.active == True)
            )
        ],
    )
    if user:
        for member in user.member:
            for member_type in member.member_type:
                if any(
                    [
                        member_type.door_access == DoorAccessEnum.FULL,
                        member_type.door_access == DoorAccessEnum.MORNING
                        and (7 <= now.hour <= 16),
                    ]
                ):
                    background_tasks.add_task(log_door_event, user.id)
                    return True
    return False
