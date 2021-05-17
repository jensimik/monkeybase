from loguru import logger
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.custom_swagger import get_swagger_ui_html
from fastapi.staticfiles import StaticFiles

from .routers import auth
from .routers import user
from .routers import member_type
from .routers import webauthn

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


app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(webauthn.router, prefix="/webauthn", tags=["webauthn-2fa"])
app.include_router(user.router, prefix="/user", tags=["user"])
app.include_router(member_type.router, prefix="/member_type", tags=["member"])
