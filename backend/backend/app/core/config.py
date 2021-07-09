import secrets
from typing import Any, Dict, List, Optional, Union

from dateutil.tz import tz, gettz
from pydantic import AnyHttpUrl, BaseSettings, EmailStr, HttpUrl, PostgresDsn, validator


class Settings(BaseSettings):
    SECRET_KEY: str = secrets.token_urlsafe(32)
    # 60 minutes * 24 hours * 8 days = 8 days
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8
    SERVER_NAME: str = "default"
    SERVER_HOST: AnyHttpUrl = "http://localhost"
    FRONTEND_HOST: AnyHttpUrl = "http://localhost"
    # BACKEND_CORS_ORIGINS is a JSON-formatted list of origins
    # e.g: '["http://localhost", "http://localhost:4200", "http://localhost:3000", \
    # "http://localhost:8080", "http://local.dockertoolbox.tiangolo.com"]'
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []

    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    PROJECT_NAME: str
    SENTRY_DSN: Optional[HttpUrl] = None

    STRIPE_API_KEY: str = None
    STRIPE_WEBHOOK_SECRET: str = None

    BAMBORA_API_KEY: str = None
    BAMBORA_MD5_KEY: str = None
    BAMBORA_CALLBACK_URL: str = None
    BAMBORA_ACCEPT_URL: str = None
    BAMBORA_CANCEL_URL: str = None

    DOOR_API_KEY: str = "asdf1234"

    # @validator("SENTRY_DSN", pre=True)
    # def sentry_dsn_can_be_blank(cls, v: str) -> Optional[str]:
    #     if len(v) == 0:
    #         return None
    #     return v

    POSTGRES_SERVER: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    SQLALCHEMY_DATABASE_URI: Optional[PostgresDsn] = None

    @validator("SQLALCHEMY_DATABASE_URI", pre=True)
    def assemble_db_connection(cls, v: Optional[str], values: Dict[str, Any]) -> Any:
        if isinstance(v, str):
            return v
        return PostgresDsn.build(
            scheme="postgresql",
            user=values.get("POSTGRES_USER"),
            password=values.get("POSTGRES_PASSWORD"),
            host=values.get("POSTGRES_SERVER"),
            path=f"/{values.get('POSTGRES_DB') or ''}",
        )

    # fido2 stuff
    WEBAUTHN_RP_ID: str = "monkey.gnerd.dk"
    WEBAUTHN_RP_NAME: str = "monkey.gnerd.dk"

    SENDGRID_API_KEY: Optional[str] = None
    SENDGRID_FROM_EMAIL: Optional[EmailStr] = None
    SENDGRID_FROM_NAME: Optional[str] = None

    EMAIL_RESET_TOKEN_EXPIRE_HOURS: int = 48

    TZ_STR: str = "Europe/Copenhagen"
    TZ: Optional[tz.tzfile] = None

    @validator("TZ", pre=True)
    def get_tz(cls, v: Optional[str], values: Dict[str, Any]) -> Any:
        if isinstance(v, tz.tzfile):
            return v
        return gettz(values.get("TZ_STR"))

    class Config:
        case_sensitive = True


settings = Settings()
