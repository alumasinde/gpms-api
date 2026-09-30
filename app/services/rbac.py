from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Membership, Permission, Role


async def get_roles(db: AsyncSession, organization_id: str):
    return (await db.scalars(select(Role).where(Role.organization_id == organization_id).order_by(Role.name))).all()


async def get_permissions(db: AsyncSession, organization_id: str, user_id: str):
    membership = await db.scalar(
        select(Membership).where(Membership.organization_id == organization_id, Membership.user_id == user_id)
        .options(selectinload(Membership.roles).selectinload(Role.permissions))
    )
    if not membership:
        return []
    unique = {p.id: p for role in membership.roles for p in role.permissions}
    return sorted(unique.values(), key=lambda p: p.code)
