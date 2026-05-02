from __future__ import annotations

import structlog
from fastapi import APIRouter
from pydantic import BaseModel

from generation.embedder import embed_text

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/embed", tags=["embeddings"])


class EmbedRequest(BaseModel):
    texts: list[str]


class EmbedResponse(BaseModel):
    embeddings: list[list[float]]
    model: str
    dimensions: int


@router.post("", response_model=EmbedResponse)
async def create_embeddings(body: EmbedRequest):
    if len(body.texts) > 100:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Max 100 texts per request")

    result = await embed_text(body.texts)
    return EmbedResponse(
        embeddings=result["embeddings"],
        model=result["model"],
        dimensions=result["dimensions"],
    )
