from __future__ import annotations

import structlog
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse

from config import settings
from routers import generate, embed, compliance

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    logger.info("Starting AI Service")
    yield
    logger.info("AI Service shut down")


app = FastAPI(
    title="OrchestraGrant AI Service",
    version="0.1.0",
    docs_url="/docs" if settings.DEBUG else None,
    default_response_class=ORJSONResponse,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["POST", "GET"],
    allow_headers=["Authorization", "Content-Type"],
)

PREFIX = "/v1"
app.include_router(generate.router, prefix=PREFIX)
app.include_router(embed.router, prefix=PREFIX)
app.include_router(compliance.router, prefix=PREFIX)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "ai"}
