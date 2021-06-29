from typing import Any, Dict, List

import aiohttp
from dateutil.relativedelta import MO, SU, relativedelta
from dateutil.rrule import DAILY, rrule
from fastapi import APIRouter, Depends, status

from .. import deps
from ..utils.custom_swagger import get_swagger_ui_html
from ..core.utils import tz_today

router = APIRouter()

URL = "https://kulturn.kk.dk/opening_hours/instances?from_date={date_from:%Y-%m-%d}&to_date={date_to:%Y-%m-%d}&nid=1706"


@router.get("/opening-hours", response_model=List[Dict[str, Any]])
async def opening_hours(
    session: aiohttp.ClientSession = Depends(deps.get_http_session),
):
    """try to get opening hours for today+7days from kk.dk api"""
    # date_from = datetime.date.today() + relativedelta(weekday=MO(-1))
    # date_to = datetime.date.today() + relativedelta(weekday=SU)
    date_from = tz_today()
    date_to = date_from + relativedelta(days=7)
    url = URL.format(date_from=date_from, date_to=date_to)
    async with session.get(url) as resp:
        data = await resp.json()
        d = {i["date"]: i for i in data}
        res = []
        for day_dt in rrule(freq=DAILY, dtstart=date_from, until=date_to):
            day = str(day_dt.date())
            res.append(
                {
                    "date": day,
                    "is_open": day in d,
                    "open": d.get(day, {}).get("start_time"),
                    "close": d.get(day, {}).get("end_time"),
                }
            )
        return res


@router.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    """custom swagger to show which scopes are required for each endpoint"""
    return get_swagger_ui_html(
        openapi_url="/openapi.json",
        title="Swagger UI",
        oauth2_redirect_url="/docs/oauth2-redirect",
    )


@router.get(
    "/healthz",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
async def healthz():
    return {"if too weak": "dont blame the routesetter"}
