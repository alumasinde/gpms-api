from fastapi import APIRouter, Depends

from app.api.deps import Auth, DbSession, AuthContext, require_permission
from app.schemas.rbac import RoleResponse
from app.services.rbac import get_roles

router = APIRouter()


@router.get("", response_model=list[RoleResponse])
async def roles(auth: Auth, db: DbSession, _: AuthContext = Depends(require_permission("roles.read"))):
    return await get_roles(db, auth.tenant.organization_id)
