from fastapi import APIRouter, Depends

from app.api.deps import Auth, DbSession, AuthContext, require_permission
from app.schemas.rbac import PermissionResponse
from app.services.rbac import get_permissions

router = APIRouter()


@router.get("", response_model=list[PermissionResponse])
async def permissions(auth: Auth, db: DbSession, _: AuthContext = Depends(require_permission("permissions.read"))):
    return await get_permissions(db, auth.tenant.organization_id, auth.user_id)
