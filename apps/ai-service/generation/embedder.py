from __future__ import annotations

import structlog
from openai import AsyncOpenAI
from config import settings

logger = structlog.get_logger(__name__)
_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    return _client


async def embed_text(texts: list[str]) -> dict:
    client = _get_client()
    response = await client.embeddings.create(
        model=settings.EMBEDDING_MODEL,
        input=texts,
        dimensions=settings.EMBEDDING_DIMENSIONS,
    )
    return {
        "embeddings": [item.embedding for item in response.data],
        "model": settings.EMBEDDING_MODEL,
        "dimensions": settings.EMBEDDING_DIMENSIONS,
    }
