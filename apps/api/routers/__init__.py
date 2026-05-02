from routers.auth import router as auth_router
from routers.users import router as users_router
from routers.organizations import router as organizations_router
from routers.grants import router as grants_router
from routers.applications import router as applications_router
from routers.documents import router as documents_router
from routers.deadlines import router as deadlines_router

__all__ = [
    "auth_router",
    "users_router",
    "organizations_router",
    "grants_router",
    "applications_router",
    "documents_router",
    "deadlines_router",
]
