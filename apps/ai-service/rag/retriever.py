from __future__ import annotations

import structlog
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from config import settings
from generation.embedder import embed_text

logger = structlog.get_logger(__name__)

_engine = None
_session_factory = None


def _get_session_factory():
    global _engine, _session_factory
    if _session_factory is None:
        _engine = create_async_engine(settings.DATABASE_URL, pool_pre_ping=True)
        _session_factory = async_sessionmaker(_engine, class_=AsyncSession, expire_on_commit=False)
    return _session_factory


async def retrieve_atoms(org_id: str, query: str, top_k: int = 8) -> list[dict]:
    """Retrieve the most semantically relevant narrative atoms for a query."""
    try:
        # Generate query embedding
        embed_result = await embed_text([query])
        query_vector = embed_result["embeddings"][0]

        factory = _get_session_factory()
        async with factory() as session:
            # pgvector cosine similarity search
            result = await session.execute(
                sa.text("""
                    SELECT id, text, category,
                           1 - (embedding <=> :query_vec::vector) AS similarity
                    FROM ai.narrative_atoms
                    WHERE org_id = :org_id
                      AND 1 - (embedding <=> :query_vec::vector) >= :min_sim
                    ORDER BY embedding <=> :query_vec::vector
                    LIMIT :top_k
                """),
                {
                    "org_id": org_id,
                    "query_vec": str(query_vector),
                    "min_sim": settings.RAG_MIN_SIMILARITY,
                    "top_k": top_k,
                },
            )
            rows = result.fetchall()
            return [
                {"id": str(r.id), "text": r.text, "category": r.category, "similarity": float(r.similarity)}
                for r in rows
            ]
    except Exception as e:
        logger.error("RAG retrieval failed", error=str(e), org_id=org_id)
        return []
