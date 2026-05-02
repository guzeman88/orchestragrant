from __future__ import annotations

import structlog
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from routers import scrape

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    logger.info("Starting Discovery Service")
    yield
    logger.info("Discovery Service shut down")


app = FastAPI(
    title="OrchestraGrant Discovery Service",
    version="0.1.0",
    docs_url="/docs" if settings.DEBUG else None,
    default_response_class=ORJSONResponse,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000"],
    allow_methods=["POST", "GET"],
    allow_headers=["Authorization", "Content-Type"],
)

PREFIX = "/v1"
app.include_router(scrape.router, prefix=PREFIX)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "discovery"}
