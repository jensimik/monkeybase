import datetime

import aiohttp
from dateutil.relativedelta import MO, SU, relativedelta
from fastapi import APIRouter, Depends
from loguru import logger
from typing import List, Dict, Any

from .. import deps

router = APIRouter()

URL = "https://kulturn.kk.dk/opening_hours/instances?from_date={date_from}&to_date={date_to}&nid=1706"


@router.get("/opening-hours", response_model=List[Dict[str, Any]])
async def opening_hours(
    session: aiohttp.ClientSession = Depends(deps.get_http_session),
):
    """try to get opening hours for current week from kk.dk api"""
    date_from = "{:%Y-%m-%d}".format(
        datetime.date.today() + relativedelta(weekday=MO(-1))
    )
    date_to = "{:%Y-%m-%d}".format(
        datetime.date.today() + relativedelta(weekday=SU(-1))
    )
    async with session.get(URL.format(date_from=date_from, date_to=date_to)) as resp:
        return await resp.json()
