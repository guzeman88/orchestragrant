from __future__ import annotations

import time

import redis.asyncio as aioredis
import structlog
from fastapi import status
from fastapi.responses import ORJSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from config import settings

logger = structlog.get_logger(__name__)

# Paths with tighter rate limits
_TIGHT_PATHS = {"/v1/auth/login", "/v1/auth/refresh"}


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Simple sliding-window rate limiter using Redis.
    Login endpoints: 10 req/min per IP.
    All other endpoints: 300 req/min per user (identified via IP as fallback).
    """

    def __init__(self, app, **kwargs):
        super().__init__(app, **kwargs)
        self._redis: aioredis.Redis | None = None

    def _get_redis(self) -> aioredis.Redis:
        if self._redis is None:
            self._redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
        return self._redis

    async def dispatch(self, request: Request, call_next) -> Response:
        # Skip rate limiting in test env
        if settings.ENV == "test":
            return await call_next(request)

        path = request.url.path
        ip = request.client.host if request.client else "unknown"

        if path in _TIGHT_PATHS:
            limit = settings.RATE_LIMIT_LOGIN_PER_MINUTE
            window = 60
            key = f"rl:login:{ip}"
        else:
            limit = 300
            window = 60
            key = f"rl:api:{ip}"

        try:
            redis = self._get_redis()
            now = int(time.time())
            pipe = redis.pipeline()
            pipe.zadd(key, {str(now): now})
            pipe.zremrangebyscore(key, 0, now - window)
            pipe.zcard(key)
            pipe.expire(key, window)
            results = await pipe.execute()
            count = results[2]

            if count > limit:
                logger.warning("Rate limit exceeded", ip=ip, path=path, count=count)
                return ORJSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "type": "https://orchestragrant.com/errors/429",
                        "title": "Too Many Requests",
                        "status": 429,
                        "detail": "Rate limit exceeded. Please slow down.",
                    },
                    headers={"Retry-After": str(window)},
                )
        except Exception as e:
            # Non-fatal: if Redis is down, don't block requests
            logger.error("Rate limit check failed", error=str(e))

        return await call_next(request)
