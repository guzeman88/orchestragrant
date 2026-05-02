from __future__ import annotations

import structlog
from openai import AsyncOpenAI
from anthropic import AsyncAnthropic
from config import settings

logger = structlog.get_logger(__name__)
_openai: AsyncOpenAI | None = None
_anthropic: AsyncAnthropic | None = None


def _openai_client() -> AsyncOpenAI:
    global _openai
    if _openai is None:
        _openai = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    return _openai


def _anthropic_client() -> AsyncAnthropic:
    global _anthropic
    if _anthropic is None:
        _anthropic = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
    return _anthropic


async def generate_with_fallback(prompt: str) -> dict:
    """Try OpenAI GPT-4o; fall back to Claude 3.5 Sonnet on failure."""
    try:
        client = _openai_client()
        response = await client.chat.completions.create(
            model=settings.GENERATION_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert grant writer for performing arts organizations. "
                        "Write in the voice of the organization using only the provided source material. "
                        "Never invent facts, statistics, or outcomes not present in the sources."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.4,
            max_tokens=2000,
        )
        content = response.choices[0].message.content or ""
        return {
            "content": content,
            "model": settings.GENERATION_MODEL,
            "tokens_used": response.usage.total_tokens if response.usage else 0,
        }
    except Exception as e:
        logger.warning("OpenAI failed, falling back to Claude", error=str(e))

    # Fallback
    client = _anthropic_client()
    response = await client.messages.create(
        model=settings.FALLBACK_MODEL,
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}],
        system=(
            "You are an expert grant writer for performing arts organizations. "
            "Write in the voice of the organization using only the provided source material. "
            "Never invent facts, statistics, or outcomes not present in the sources."
        ),
    )
    content = response.content[0].text if response.content else ""
    return {
        "content": content,
        "model": settings.FALLBACK_MODEL,
        "tokens_used": (response.usage.input_tokens + response.usage.output_tokens) if response.usage else 0,
    }
