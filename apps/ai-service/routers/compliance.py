from __future__ import annotations

import structlog
from fastapi import APIRouter
from pydantic import BaseModel

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/compliance", tags=["compliance"])


class ComplianceRequest(BaseModel):
    content: str
    grant_requirements: list[str] = []
    word_limit: int | None = None
    char_limit: int | None = None


class ComplianceIssue(BaseModel):
    type: str  # word_count | char_count | prohibited_language | missing_requirement
    severity: str  # error | warning | info
    message: str
    position: int | None = None


class ComplianceResponse(BaseModel):
    issues: list[ComplianceIssue]
    word_count: int
    char_count: int
    is_compliant: bool


@router.post("", response_model=ComplianceResponse)
async def check_compliance(body: ComplianceRequest):
    words = body.content.split()
    word_count = len(words)
    char_count = len(body.content)
    issues: list[ComplianceIssue] = []

    if body.word_limit and word_count > body.word_limit:
        issues.append(ComplianceIssue(
            type="word_count",
            severity="error",
            message=f"Exceeds word limit by {word_count - body.word_limit} words ({word_count}/{body.word_limit})",
        ))
    elif body.word_limit and word_count > body.word_limit * 0.95:
        issues.append(ComplianceIssue(
            type="word_count",
            severity="warning",
            message=f"Approaching word limit ({word_count}/{body.word_limit})",
        ))

    if body.char_limit and char_count > body.char_limit:
        issues.append(ComplianceIssue(
            type="char_count",
            severity="error",
            message=f"Exceeds character limit ({char_count}/{body.char_limit})",
        ))

    # Basic prohibited language check
    prohibited = ["guaranteed", "will definitely", "100% success", "promise"]
    for phrase in prohibited:
        if phrase.lower() in body.content.lower():
            issues.append(ComplianceIssue(
                type="prohibited_language",
                severity="warning",
                message=f"Avoid absolute language: '{phrase}'",
            ))

    return ComplianceResponse(
        issues=issues,
        word_count=word_count,
        char_count=char_count,
        is_compliant=not any(i.severity == "error" for i in issues),
    )
