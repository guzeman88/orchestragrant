from __future__ import annotations

import os
import shutil
from pathlib import Path
from uuid import UUID

import boto3
import structlog
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from database import get_db
from dependencies import CurrentUser
from models import OrgDocument
from schemas import PresignedUploadRequest, PresignedUploadResponse, DocumentRead

LOCAL_UPLOAD_DIR = Path(__file__).parent.parent / "local_uploads"

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/documents", tags=["documents"])

ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "text/plain",
    "image/jpeg",
    "image/png",
}


def _get_s3_client():
    return boto3.client(
        "s3",
        region_name=settings.AWS_REGION,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID or None,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY or None,
    )


@router.post("/upload-url", response_model=PresignedUploadResponse, status_code=status.HTTP_201_CREATED)
async def get_upload_url(
    body: PresignedUploadRequest,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    if body.mime_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(status_code=400, detail=f"File type not allowed: {body.mime_type}")

    # Create document record (pending status)
    doc = OrgDocument(
        org_id=current_user.org_id,
        category=body.category,
        file_name=body.file_name,
        file_key=f"orgs/{current_user.org_id}/documents/pending-{body.file_name}",
        file_size_bytes=body.file_size_bytes,
        mime_type=body.mime_type,
        uploaded_by=current_user.id,
        processing_status="pending",
        year=body.year,
        description=body.description,
    )
    db.add(doc)
    await db.flush()

    # Update file key with actual document ID
    doc.file_key = f"orgs/{current_user.org_id}/documents/{doc.id}/{body.file_name}"
    await db.flush()

    # Generate presigned URL or local upload URL
    if not settings.AWS_ACCESS_KEY_ID:
        # Local dev: return a local upload endpoint URL
        base_url = settings.API_BASE_URL if hasattr(settings, "API_BASE_URL") else "http://localhost:8001"
        upload_url = f"{base_url}/v1/documents/local-upload/{doc.id}"
    else:
        try:
            s3 = _get_s3_client()
            upload_url = s3.generate_presigned_url(
                "put_object",
                Params={
                    "Bucket": settings.S3_BUCKET_NAME,
                    "Key": doc.file_key,
                    "ContentType": body.mime_type,
                    "ContentLength": body.file_size_bytes,
                },
                ExpiresIn=settings.S3_PRESIGNED_EXPIRY_SECONDS,
            )
        except Exception as e:
            logger.error("Failed to generate presigned URL", error=str(e))
            raise HTTPException(status_code=500, detail="Failed to generate upload URL")

    return PresignedUploadResponse(
        upload_url=upload_url,
        document_id=doc.id,
        expires_in=settings.S3_PRESIGNED_EXPIRY_SECONDS,
    )


@router.put("/local-upload/{doc_id}", status_code=status.HTTP_200_OK)
async def local_upload(
    doc_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Local dev only: accepts raw file body and stores to disk."""
    result = await db.execute(select(OrgDocument).where(OrgDocument.id == doc_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    LOCAL_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    dest = LOCAL_UPLOAD_DIR / str(doc_id)
    body = await request.body()
    dest.write_bytes(body)

    doc.processing_status = "complete"
    await db.flush()
    return {"ok": True}


@router.post("/{doc_id}/confirm", status_code=status.HTTP_204_NO_CONTENT)
async def confirm_upload(
    doc_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Called by client after successful S3 upload to trigger processing."""
    result = await db.execute(
        select(OrgDocument).where(
            OrgDocument.id == doc_id, OrgDocument.org_id == current_user.org_id
        )
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    doc.processing_status = "processing"
    await db.flush()

    # Trigger Celery processing task (skip if no S3)
    if settings.AWS_ACCESS_KEY_ID:
        try:
            from tasks.document_tasks import process_document
            process_document.delay(str(doc.id))
        except Exception as e:
            logger.warning("Failed to enqueue document processing", doc_id=str(doc_id), error=str(e))
    else:
        # Local dev: mark as complete immediately
        doc.processing_status = "complete"
        await db.flush()


@router.get("", response_model=list[DocumentRead])
async def list_documents(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    category: str | None = None,
):
    stmt = select(OrgDocument).where(OrgDocument.org_id == current_user.org_id)
    if category:
        stmt = stmt.where(OrgDocument.category == category)
    stmt = stmt.order_by(OrgDocument.uploaded_at.desc())
    result = await db.execute(stmt)
    return [DocumentRead.model_validate(d) for d in result.scalars().all()]


@router.get("/{doc_id}/download-url")
async def get_download_url(
    doc_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(OrgDocument).where(
            OrgDocument.id == doc_id, OrgDocument.org_id == current_user.org_id
        )
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    if not settings.AWS_ACCESS_KEY_ID:
        # Local dev: return a local download endpoint URL
        base_url = settings.API_BASE_URL if hasattr(settings, "API_BASE_URL") else "http://localhost:8001"
        url = f"{base_url}/v1/documents/local-download/{doc_id}"
        return {"download_url": url, "expires_in": 3600}

    try:
        s3 = _get_s3_client()
        url = s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": settings.S3_BUCKET_NAME, "Key": doc.file_key},
            ExpiresIn=settings.S3_PRESIGNED_EXPIRY_SECONDS,
        )
    except Exception as e:
        logger.error("Failed to generate download URL", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to generate download URL")

    return {"download_url": url, "expires_in": settings.S3_PRESIGNED_EXPIRY_SECONDS}


@router.get("/local-download/{doc_id}")
async def local_download(
    doc_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Local dev only: serve uploaded file from disk."""
    from fastapi.responses import FileResponse
    result = await db.execute(select(OrgDocument).where(OrgDocument.id == doc_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    dest = LOCAL_UPLOAD_DIR / str(doc_id)
    if not dest.exists():
        raise HTTPException(status_code=404, detail="File not found on disk")
    return FileResponse(path=str(dest), filename=doc.file_name, media_type=doc.mime_type)


@router.delete("/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    doc_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(OrgDocument).where(
            OrgDocument.id == doc_id, OrgDocument.org_id == current_user.org_id
        )
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    await db.delete(doc)
    await db.flush()
