import datetime
from typing import Any, Dict, List

import aiohttp
from dateutil.relativedelta import MO, SU, relativedelta
from fastapi import APIRouter, Depends, status

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
    date_to = "{:%Y-%m-%d}".format(datetime.date.today() + relativedelta(weekday=SU))
    url = URL.format(date_from=date_from, date_to=date_to)
    async with session.get(url) as resp:
        return await resp.json()


@router.get(
    "/healthz",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
async def healthz():
    return {"dont blame": "the routesetters"}
