from __future__ import annotations

import io
import textwrap
from datetime import datetime, timezone
from typing import Generator

import boto3
import httpx
import structlog
from celery_app import celery_app

logger = structlog.get_logger(__name__)

# ── Chunking helpers ─────────────────────────────────────────────────────────

CHUNK_SIZE = 400   # target words per chunk
CHUNK_OVERLAP = 50 # overlap words


def _word_chunks(text: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> Generator[str, None, None]:
    words = text.split()
    step = size - overlap
    for i in range(0, max(1, len(words) - overlap), step):
        chunk = " ".join(words[i : i + size])
        if chunk.strip():
            yield chunk


def _extract_text_with_llamaparse(file_bytes: bytes, mime_type: str, api_key: str) -> str:
    """Parse document using LlamaParse API and return plain text."""
    upload_res = httpx.post(
        "https://api.cloud.llamaindex.ai/api/parsing/upload",
        headers={"Authorization": f"Bearer {api_key}"},
        files={"file": ("document", io.BytesIO(file_bytes), mime_type)},
        data={"language": "en", "parsing_instruction": "Extract all text. Preserve paragraph structure."},
        timeout=120,
    )
    upload_res.raise_for_status()
    job_id = upload_res.json()["id"]

    # Poll for completion (max 120s)
    import time
    for _ in range(24):
        status_res = httpx.get(
            f"https://api.cloud.llamaindex.ai/api/parsing/job/{job_id}",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=30,
        )
        status_res.raise_for_status()
        data = status_res.json()
        if data.get("status") == "SUCCESS":
            text_res = httpx.get(
                f"https://api.cloud.llamaindex.ai/api/parsing/job/{job_id}/result/text",
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=30,
            )
            text_res.raise_for_status()
            return text_res.json().get("text", "")
        if data.get("status") in ("ERROR", "CANCELLED"):
            raise RuntimeError(f"LlamaParse job failed: {data}")
        time.sleep(5)
    raise TimeoutError("LlamaParse did not finish within 120 seconds")


def _extract_text_fallback(file_bytes: bytes, mime_type: str) -> str:
    """Fallback plain-text extraction without LlamaParse."""
    if mime_type == "application/pdf":
        try:
            import pdfplumber
            with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                pages = [p.extract_text() or "" for p in pdf.pages]
            return "\n\n".join(pages)
        except Exception:
            pass
    if mime_type in ("text/plain",):
        return file_bytes.decode("utf-8", errors="ignore")
    # For docx
    if "wordprocessingml" in mime_type:
        try:
            import docx
            doc = docx.Document(io.BytesIO(file_bytes))
            return "\n".join(p.text for p in doc.paragraphs if p.text)
        except Exception:
            pass
    return ""


def _embed_batch(texts: list[str], api_key: str) -> list[list[float]]:
    """Embed a list of text chunks via OpenAI text-embedding-3-large."""
    from openai import OpenAI
    client = OpenAI(api_key=api_key)
    response = client.embeddings.create(
        model="text-embedding-3-large",
        input=texts,
        dimensions=3072,
    )
    return [item.embedding for item in response.data]


@celery_app.task(name="tasks.document_tasks.process_document", bind=True, max_retries=3)
def process_document(self, document_id: str):
    """
    Full pipeline:
    1. Download from S3
    2. Parse with LlamaParse (fallback: pdfplumber / python-docx)
    3. Chunk text into ~400-word segments with 50-word overlap
    4. Embed via OpenAI text-embedding-3-large
    5. Store as NarrativeAtom rows in ai.narrative_atoms
    6. Mark OrgDocument as complete
    """
    from sqlalchemy import create_engine, delete
    from sqlalchemy.orm import Session
    from config import settings
    from models import OrgDocument, NarrativeAtom

    logger.info("Processing document", document_id=document_id)
    engine = create_engine(settings.DATABASE_URL_SYNC)

    try:
        with Session(engine) as db:
            doc = db.get(OrgDocument, document_id)
            if not doc:
                logger.warning("Document not found", document_id=document_id)
                return

            doc.processing_status = "processing"
            db.commit()

            # ── 1. Download from S3 ─────────────────────────────────────────
            s3 = boto3.client(
                "s3",
                region_name=settings.AWS_REGION,
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID or None,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY or None,
            )
            obj = s3.get_object(Bucket=settings.S3_BUCKET_NAME, Key=doc.file_key)
            file_bytes = obj["Body"].read()

            # ── 2. Extract text ─────────────────────────────────────────────
            if settings.LLAMAPARSE_API_KEY:
                text = _extract_text_with_llamaparse(file_bytes, doc.mime_type, settings.LLAMAPARSE_API_KEY)
            else:
                text = _extract_text_fallback(file_bytes, doc.mime_type)

            if not text.strip():
                logger.warning("No text extracted", document_id=document_id)
                doc.processing_status = "complete"
                doc.processed_at = datetime.now(timezone.utc)
                db.commit()
                return

            # ── 3. Chunk ────────────────────────────────────────────────────
            chunks = list(_word_chunks(text))
            logger.info("Text chunked", document_id=document_id, chunk_count=len(chunks))

            # ── 4. Embed in batches of 50 ───────────────────────────────────
            embeddings: list[list[float]] = []
            if settings.OPENAI_API_KEY:
                batch_size = 50
                for i in range(0, len(chunks), batch_size):
                    batch = chunks[i : i + batch_size]
                    embeddings.extend(_embed_batch(batch, settings.OPENAI_API_KEY))
            else:
                # No OpenAI key: store atoms without embeddings (search will be text-only)
                embeddings = [None] * len(chunks)  # type: ignore[list-item]

            # ── 5. Delete old atoms from this document, insert new ──────────
            db.execute(delete(NarrativeAtom).where(NarrativeAtom.document_id == doc.id))

            for chunk_text, embedding in zip(chunks, embeddings):
                atom = NarrativeAtom(
                    org_id=doc.org_id,
                    document_id=doc.id,
                    text=chunk_text,
                    category=doc.category,
                    embedding=embedding,
                )
                db.add(atom)

            # ── 6. Mark complete ────────────────────────────────────────────
            doc.processing_status = "complete"
            doc.processed_at = datetime.now(timezone.utc)
            db.commit()

            logger.info("Document processed", document_id=document_id, atoms=len(chunks))

    except Exception as exc:
        logger.error("Document processing failed", document_id=document_id, error=str(exc))
        # Mark failed in DB before retry
        try:
            with Session(engine) as db:
                doc = db.get(OrgDocument, document_id)
                if doc and self.request.retries >= self.max_retries:
                    doc.processing_status = "failed"
                    db.commit()
        except Exception:
            pass
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
    finally:
        engine.dispose()
