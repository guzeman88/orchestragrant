from __future__ import annotations

from typing import Annotated
from uuid import UUID

import structlog
from fastapi import Depends, HTTPException, status, WebSocket
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import User
from services.auth_service import decode_access_token

logger = structlog.get_logger(__name__)

bearer_scheme = HTTPBearer(auto_error=False)

VALID_ROLES = {"owner", "director", "grant_writer", "staff", "read_only"}
ROLE_HIERARCHY = {
    "owner": 5,
    "director": 4,
    "grant_writer": 3,
    "staff": 2,
    "read_only": 1,
}


async def _get_user_from_token(token: str, db: AsyncSession) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(token)
        user_id: str = payload.get("sub")
        if not user_id:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    result = await db.execute(select(User).where(User.id == UUID(user_id)))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise credentials_exception
    return user


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return await _get_user_from_token(credentials.credentials, db)


def require_role(minimum_role: str):
    """Dependency factory that enforces a minimum role level."""
    async def _check(current_user: Annotated[User, Depends(get_current_user)]) -> User:
        user_level = ROLE_HIERARCHY.get(current_user.role, 0)
        required_level = ROLE_HIERARCHY.get(minimum_role, 999)
        if user_level < required_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires '{minimum_role}' role or higher",
            )
        return current_user
    return _check


async def get_ws_user(websocket: WebSocket, db: AsyncSession = Depends(get_db)) -> User:
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=4001)
        raise HTTPException(status_code=401, detail="Token required")
    return await _get_user_from_token(token, db)


CurrentUser = Annotated[User, Depends(get_current_user)]
DirectorOrAbove = Annotated[User, Depends(require_role("director"))]
OwnerOnly = Annotated[User, Depends(require_role("owner"))]
