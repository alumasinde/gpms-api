from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenError, NotFoundError
from app.models import DatabaseConnection, Membership, Organization
from app.tenant.context import TenantContext


async def resolve_tenant_context(
    db: AsyncSession, *, user_id: str, organization_id: str
) -> TenantContext:
    result = await db.execute(
        select(Membership, Organization)
        .join(Organization, Organization.id == Membership.organization_id)
        .where(
            Membership.user_id == user_id,
            Membership.organization_id == organization_id,
            Membership.status == "active",
            Organization.status == "active",
        )
    )
    row = result.first()
    if not row:
        raise ForbiddenError("You do not have access to this organization")
    _, organization = row
    connection = await db.scalar(select(DatabaseConnection).where(DatabaseConnection.organization_id == organization.id))
    database_url = connection.connection_url if connection and connection.mode == "dedicated" else None
    return TenantContext(organization_id=organization.id, storage_mode=organization.storage_mode, database_url=database_url)


async def get_organization(db: AsyncSession, organization_id: str) -> Organization:
    organization = await db.get(Organization, organization_id)
    if not organization:
        raise NotFoundError("Organization not found")
    return organization
