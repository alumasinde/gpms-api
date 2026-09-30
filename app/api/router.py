from fastapi import APIRouter

from app.platform.organizations.routes import router as organizations_router
from app.platform.roles.routes import router as roles_router
from app.platform.users.routes import router as users_router
from app.platform.auth.routes import router as auth_router

api_router = APIRouter()
api_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
api_router.include_router(organizations_router, prefix="/organizations", tags=["Organizations"])
api_router.include_router(roles_router, prefix="/roles", tags=["Roles"])
api_router.include_router(users_router, prefix="/permissions", tags=["Permissions"])
