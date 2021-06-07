import asyncio
import datetime
import pathlib

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from loguru import logger
from starlette.middleware.cors import CORSMiddleware

from . import crud, deps, models
from .core.config import settings
from .core.custom_swagger import get_swagger_ui_html
from .utils.cron import repeat_at

# routes
from .routers import auth, door, me, member, member_type, user, webauthn, misc

app = FastAPI(title=settings.PROJECT_NAME, version="0.0.1", docs_url=None)

# Set all CORS enabled origins
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

module_dir = pathlib.Path(__file__).parent.absolute()


@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    """custom swagger to show which scopes are required for each endpoint"""
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=app.title + " - Swagger UI",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
    )


@app.get("/", include_in_schema=False)
async def root():
    """go away"""
    return {"message": "go away, nothing to see here"}


app.mount("/static", StaticFiles(directory=module_dir / "static"), name="static")
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(webauthn.router, prefix="/webauthn", tags=["webauthn_2fa"])
app.include_router(user.router, prefix="/users", tags=["user"])
app.include_router(me.router, prefix="/me", tags=["me"])
app.include_router(member_type.router, prefix="/member_types", tags=["member_type"])
app.include_router(member.router, prefix="/members", tags=["member"])
app.include_router(door.router, prefix="/door-access", tags=["door"])
app.include_router(misc.router, prefix="/misc", tags=["misc"])


@app.on_event("startup")
@repeat_at(cron="*/10 * * * *", wait_first=True, raise_exceptions=True)
async def _poor_mans_cron():
    logger.info("here")
    async with deps.get_db_context() as db:
        if await crud.lock_table.get(
            db, models.LockTable.name == "crontest", for_update=True, only_active=False
        ):
            await crud.lock_table.update(
                db,
                models.LockTable.name == "crontest",
                obj_in={"ran_at": datetime.datetime.utcnow()},
                only_active=False,
            )
            logger.info("cron ping")
            await asyncio.sleep(
                10
            )  # sleep a bit so the other processes fail to get lock

            await db.commit()
