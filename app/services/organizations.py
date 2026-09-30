from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Membership, Organization


async def list_for_user(db: AsyncSession, user_id: str):
    return (await db.scalars(
        select(Organization)
        .join(Membership, Membership.organization_id == Organization.id)
        .where(Membership.user_id == user_id, Membership.status == "active")
        .order_by(Organization.name)
    )).all()
