import logging
from contextlib import asynccontextmanager

import sentry_sdk
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.routing import APIRoute
from starlette.middleware.cors import CORSMiddleware

from app.api.api import api_router
from app.core.config import settings
from app.core.model_wrapper import ModelWrapper

logger = logging.getLogger(__name__)

# Initialize model wrapper globally so routes can access it
model_wrapper = ModelWrapper()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    # Startup
    try:
        model_wrapper.load()
    except Exception as e:
        logger.warning("Model load failed: %s", e)
    app.state.model_wrapper = model_wrapper

    yield

    # Shutdown (nothing to clean up currently)


def custom_generate_unique_id(route: APIRoute) -> str:
    # Some routes may not define `tags`; fall back to a stable default
    try:
        tag = route.tags[0] if route.tags and len(route.tags) > 0 else "default"
    except Exception:
        tag = "default"
    return f"{tag}-{route.name}"


if settings.SENTRY_DSN and settings.ENVIRONMENT != "local":
    sentry_sdk.init(dsn=str(settings.SENTRY_DSN), enable_tracing=True)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    generate_unique_id_function=custom_generate_unique_id,
    lifespan=lifespan,
)

# Set all CORS enabled origins
if settings.all_cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.all_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/", include_in_schema=False)
async def root_redirect():
    """Redirect root URL to the interactive API docs (served at `/docs`)."""
    return RedirectResponse(url="/docs")


@app.get("/health", tags=["health"])
async def health():
    """Global health check endpoint.

    Standard health check at root level for load balancers,
    Kubernetes probes, and Docker health checks.
    """
    return {"status": "ok"}


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """Catch-all exception handler that logs the full traceback and returns a 500.

    This ensures unhandled exceptions (including those raised during dependency
    injection or validation) are written to the application logs so they can be
    inspected from `docker-compose logs`.

    HTTPException is excluded since FastAPI handles it natively with proper status codes.
    """
    from fastapi import HTTPException

    if isinstance(exc, HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
        )
    logger.exception(
        "Unhandled exception while processing request %s %s",
        request.method,
        request.url,
    )
    return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})
