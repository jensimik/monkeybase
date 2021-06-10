import pathlib

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware

from . import cron
from .core.config import settings

# routes
from .routers import (
    auth,
    door,
    me,
    member,
    member_type,
    misc,
    slot,
    user,
    webauthn,
    webhook,
)
from .utils.cron import repeat_at

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


app.mount("/static", StaticFiles(directory=module_dir / "static"), name="static")
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(webauthn.router, prefix="/webauthn", tags=["webauthn_2fa"])
app.include_router(user.router, prefix="/users", tags=["user"])
app.include_router(me.router, prefix="/me", tags=["me"])
app.include_router(member_type.router, prefix="/member_types", tags=["member_type"])
app.include_router(slot.router, prefix="/slot", tags=["slot"])
app.include_router(member.router, prefix="/members", tags=["member"])
app.include_router(door.router, prefix="/door-access", tags=["door"])
app.include_router(webhook.router, tags=["webhook"])
app.include_router(misc.router, tags=["misc"])


# release/generate slots every hour if any available
@app.on_event("startup")
@repeat_at(cron="0 * * * *", wait_first=True, raise_exceptions=True)
async def _generate_slots():
    await cron.generate_slots()
