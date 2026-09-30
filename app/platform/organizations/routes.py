from fastapi import APIRouter, Depends

from app.api.deps import Auth, DbSession, AuthContext, require_permission
from app.core.exceptions import ForbiddenError
from app.schemas.organizations import OrganizationResponse
from app.services.organizations import list_for_user
from app.tenant.resolver import get_organization

router = APIRouter()


@router.get("", response_model=list[OrganizationResponse])
async def organizations(auth: Auth, db: DbSession, _: AuthContext = Depends(require_permission("organization.read"))):
    return await list_for_user(db, auth.user_id)


@router.get("/{organization_id}", response_model=OrganizationResponse)
async def organization(organization_id: str, auth: Auth, db: DbSession, _: AuthContext = Depends(require_permission("organization.read"))):
    if organization_id != auth.tenant.organization_id:
        raise ForbiddenError("Organization context does not match authenticated tenant")
    return await get_organization(db, organization_id)
