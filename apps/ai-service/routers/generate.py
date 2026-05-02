from __future__ import annotations

from typing import Optional
from uuid import UUID

import structlog
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from config import settings
from rag.retriever import retrieve_atoms
from generation.llm_client import generate_with_fallback
from generation.prompt_builder import build_section_prompt

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/generate", tags=["generation"])


class GenerateRequest(BaseModel):
    org_id: str
    section_title: str
    section_prompt: Optional[str] = None
    grant_title: Optional[str] = None
    grant_description: Optional[str] = None
    requested_amount: Optional[float] = None
    word_limit: Optional[int] = None
    tone: str = "professional"  # professional | warm | urgent | data_driven
    existing_content: Optional[str] = None


class GenerateResponse(BaseModel):
    content: str
    sources: list[dict]
    model_used: str
    tokens_used: int


@router.post("", response_model=GenerateResponse)
async def generate_section(body: GenerateRequest):
    # Retrieve relevant narrative atoms
    query = f"{body.section_title} {body.section_prompt or ''} {body.grant_title or ''}"
    atoms = await retrieve_atoms(org_id=body.org_id, query=query, top_k=settings.RAG_TOP_K)

    if not atoms:
        logger.warning("No narrative atoms found for org", org_id=body.org_id)

    # Build prompt
    prompt = build_section_prompt(
        section_title=body.section_title,
        section_prompt=body.section_prompt,
        grant_title=body.grant_title,
        grant_description=body.grant_description,
        requested_amount=body.requested_amount,
        word_limit=body.word_limit,
        tone=body.tone,
        atoms=atoms,
        existing_content=body.existing_content,
    )

    # Generate
    result = await generate_with_fallback(prompt)

    return GenerateResponse(
        content=result["content"],
        sources=[{"id": a["id"], "text_snippet": a["text"][:200]} for a in atoms],
        model_used=result["model"],
        tokens_used=result["tokens_used"],
    )
