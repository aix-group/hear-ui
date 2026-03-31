import logging
import secrets
from typing import Annotated, Any, Literal

from pydantic import (
    AnyUrl,
    BeforeValidator,
    computed_field,
)
from pydantic_settings import BaseSettings, SettingsConfigDict

_config_logger = logging.getLogger(__name__)


def parse_cors(v: Any) -> list[str] | str:
    if isinstance(v, str) and not v.startswith("["):
        return [i.strip() for i in v.split(",")]
    elif isinstance(v, list | str):
        return v
    raise ValueError(v)


# Generate a fallback key only once at module load so it stays stable
# across the lifetime of the process. In production, always set SECRET_KEY
# via environment variable or .env file.
_FALLBACK_SECRET_KEY = secrets.token_urlsafe(32)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",  # one level above backend
        env_ignore_empty=True,
        extra="ignore",
    )

    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = _FALLBACK_SECRET_KEY
    FRONTEND_HOST: str = "http://localhost:5173"
    SENTRY_DSN: str | None = None
    ENVIRONMENT: Literal["local", "staging", "production"] = "local"

    BACKEND_CORS_ORIGINS: Annotated[
        list[AnyUrl] | str, BeforeValidator(parse_cors)
    ] = []

    @computed_field  # type: ignore[prop-decorator]
    @property
    def all_cors_origins(self) -> list[str]:
        return [str(origin).rstrip("/") for origin in self.BACKEND_CORS_ORIGINS] + [
            self.FRONTEND_HOST
        ]

    PROJECT_NAME: str = "Hear-UI"
    PREDICTION_THRESHOLD: float = 0.5

    # Database
    POSTGRES_SERVER: str
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str

    @computed_field  # type: ignore[prop-decorator]
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        # Use the psycopg (psycopg3) dialect when psycopg[binary] is installed
        # The project depends on psycopg[binary] (psycopg v3). SQLAlchemy will
        # import the appropriate DBAPI for 'psycopg'. Previously this used
        # 'psycopg2' which requires the psycopg2 package; change to 'psycopg'
        # to avoid ModuleNotFoundError when only psycopg v3 is available.
        return (
            f"postgresql+psycopg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@"
            f"{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    # Testing flag to enable destructive schema operations in local/test runs
    TESTING: bool = False


# Create instance
settings = Settings()

if settings.SECRET_KEY == _FALLBACK_SECRET_KEY:
    _config_logger.warning(
        "SECRET_KEY not set via environment or .env file — using a random fallback. "
        "Sessions will not survive restarts. Set SECRET_KEY for production use."
    )
