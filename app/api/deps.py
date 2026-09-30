from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Header
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_platform_db
from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.security import decode_access_token
from app.models import Membership, Role
from app.tenant.context import TenantContext
from app.tenant.resolver import resolve_tenant_context

bearer = HTTPBearer(auto_error=False)
DbSession = Annotated[AsyncSession, Depends(get_platform_db)]


@dataclass(frozen=True)
class AuthContext:
    user_id: str
    tenant: TenantContext


async def get_auth_context(
    db: DbSession,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
    x_organization_id: Annotated[str | None, Header()] = None,
) -> AuthContext:
    if not credentials or credentials.scheme.lower() != "bearer":
        raise UnauthorizedError()
    try:
        payload = decode_access_token(credentials.credentials)
        user_id = payload.get("sub")
        token_org = payload.get("org")
        if payload.get("type") != "access" or not user_id or not token_org:
            raise UnauthorizedError("Invalid access token")
    except Exception as exc:
        if isinstance(exc, UnauthorizedError):
            raise
        raise UnauthorizedError("Invalid or expired access token") from exc

    if x_organization_id and x_organization_id != token_org:
        raise UnauthorizedError("Organization context does not match access token")
    tenant = await resolve_tenant_context(db, user_id=user_id, organization_id=token_org)
    return AuthContext(user_id=user_id, tenant=tenant)


Auth = Annotated[AuthContext, Depends(get_auth_context)]


def require_permission(permission_code: str):
    async def dependency(auth: Auth, db: DbSession) -> AuthContext:
        membership = await db.scalar(
            select(Membership)
            .where(
                Membership.organization_id == auth.tenant.organization_id,
                Membership.user_id == auth.user_id,
                Membership.status == "active",
            )
            .options(selectinload(Membership.roles).selectinload(Role.permissions))
        )
        if not membership:
            raise ForbiddenError("Active organization membership required")
        allowed = any(
            permission_code == permission.code
            for role in membership.roles
            for permission in role.permissions
        )
        if not allowed:
            raise ForbiddenError(f"Missing permission: {permission_code}")
        return auth

    return dependency
