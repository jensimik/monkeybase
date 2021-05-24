from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, Security, Response
from app import models, schemas, crud, deps

router = APIRouter()


@router.post("")
def test(
    current_user_id: int = Security(
        deps.get_current_user_id, scopes=["basic", "subscribe_token"]
    ),
    # db: AsyncSession = Depends(deps.get_db),
):
    return False
