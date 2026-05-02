from __future__ import annotations

import sentry_sdk
import structlog
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import ORJSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from config import settings
from database import create_db_pool, close_db_pool
from routers import auth, organizations, grants, applications, documents, deadlines, users, webhooks
from middleware.logging import LoggingMiddleware
from middleware.rate_limit import RateLimitMiddleware

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    logger.info("Starting OrchestraGrant API", version=settings.APP_VERSION, env=settings.ENV)
    await create_db_pool()
    yield
    await close_db_pool()
    logger.info("OrchestraGrant API shut down")


if settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=settings.ENV,
        traces_sample_rate=0.1,
        profiles_sample_rate=0.1,
    )


app = FastAPI(
    title="OrchestraGrant API",
    version=settings.APP_VERSION,
    description="Grant management platform for performing arts organizations",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    default_response_class=ORJSONResponse,
    lifespan=lifespan,
)

# ─── Middleware ────────────────────────────────────────────────────────────────

app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
    expose_headers=["X-Request-ID", "X-Total-Count"],
)
app.add_middleware(LoggingMiddleware)
app.add_middleware(RateLimitMiddleware)

# ─── Exception Handlers ────────────────────────────────────────────────────────

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return ORJSONResponse(
        status_code=exc.status_code,
        content={
            "type": f"https://orchestragrant.com/errors/{exc.status_code}",
            "title": exc.detail,
            "status": exc.status_code,
            "detail": exc.detail,
            "instance": str(request.url.path),
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    field_errors: dict[str, list[str]] = {}
    for error in exc.errors():
        loc = ".".join(str(l) for l in error["loc"] if l != "body")
        field_errors.setdefault(loc, []).append(error["msg"])

    return ORJSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "type": "https://orchestragrant.com/errors/validation",
            "title": "Validation Error",
            "status": 422,
            "detail": "One or more fields failed validation.",
            "errors": field_errors,
        },
    )


# ─── Routes ───────────────────────────────────────────────────────────────────

PREFIX = "/v1"

app.include_router(auth.router, prefix=PREFIX)
app.include_router(users.router, prefix=PREFIX)
app.include_router(organizations.router, prefix=PREFIX)
app.include_router(grants.router, prefix=PREFIX)
app.include_router(applications.router, prefix=PREFIX)
app.include_router(documents.router, prefix=PREFIX)
app.include_router(deadlines.router, prefix=PREFIX)
app.include_router(webhooks.router, prefix=PREFIX)


@app.get("/health", tags=["system"])
async def health_check():
    return {"status": "ok", "version": settings.APP_VERSION}
