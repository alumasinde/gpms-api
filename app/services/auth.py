from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import get_settings
from app.core.exceptions import ConflictError, UnauthorizedError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    hash_token,
    verify_password,
)
from app.models import (
    Membership,
    Organization,
    Permission,
    RefreshSession,
    Role,
    TenantConfiguration,
    DatabaseConnection,
    User,
)

settings = get_settings()
DEFAULT_PERMISSIONS = [
    ("organization.read", "Read organization"),
    ("users.read", "Read users"),
    ("roles.read", "Read roles"),
    ("roles.manage", "Manage roles"),
    ("permissions.read", "Read permissions"),
]


async def register(db: AsyncSession, data) -> tuple[User, Organization]:
    """Create the initial organization and owner atomically.

    Explicit flushes establish parent rows before dependent rows are inserted.
    This is intentional: relying on scalar foreign-key IDs alone does not give
    SQLAlchemy enough ORM dependency information to guarantee insert ordering.
    """
    email = str(data.email).strip().lower()
    username = data.username.strip().lower()
    organization_code = data.organization_code.strip().lower()

    try:
        async with db.begin():
            exists = await db.scalar(
                select(User).where(or_(User.email == email, User.username == username))
            )
            if exists:
                raise ConflictError("Email or username is already registered")

            org_exists = await db.scalar(
                select(Organization).where(Organization.code == organization_code)
            )
            if org_exists:
                raise ConflictError("Organization code is already in use")

            org = Organization(
                id=str(uuid4()),
                name=data.organization_name.strip(),
                code=organization_code,
                status="active",
                storage_mode="shared",
            )
            db.add(org)
            await db.flush()

            user = User(
                id=str(uuid4()),
                first_name=data.first_name,
                last_name=data.last_name,
                email=email,
                username=username,
                password_hash=hash_password(data.password),
                is_active=True,
            )
            db.add(user)
            await db.flush()

            role = Role(
                id=str(uuid4()),
                organization=org,
                name="Organization Owner",
                code="organization_owner",
                description="Initial organization owner",
                is_system=True,
            )
            membership = Membership(
                id=str(uuid4()),
                organization=org,
                user=user,
                status="active",
            )
            db.add_all([role, membership])
            await db.flush()

            permissions = list(
                await db.scalars(
                    select(Permission).where(Permission.code.in_([code for code, _ in DEFAULT_PERMISSIONS]))
                )
            )
            permissions_by_code = {permission.code: permission for permission in permissions}
            for code, name in DEFAULT_PERMISSIONS:
                if code not in permissions_by_code:
                    permission = Permission(id=str(uuid4()), code=code, name=name)
                    db.add(permission)
                    permissions_by_code[code] = permission
            await db.flush()

            role.permissions.extend(permissions_by_code[code] for code, _ in DEFAULT_PERMISSIONS)
            membership.roles.append(role)

            tenant_config = TenantConfiguration(
                id=str(uuid4()),
                organization=org,
                timezone="Africa/Nairobi",
                locale="en-KE",
                settings={},
            )
            database_connection = DatabaseConnection(
                id=str(uuid4()),
                organization=org,
                mode="shared",
                schema_version=1,
                is_healthy=True,
            )
            db.add_all([tenant_config, database_connection])
            await db.flush()

        return user, org
    except ConflictError:
        raise
    except IntegrityError as exc:
        raise ConflictError("Registration conflicts with an existing account or organization") from exc


async def login(db: AsyncSession, login_value: str, password: str, organization_id: str | None):
    normalized = login_value.strip().lower()
    user = await db.scalar(
        select(User).where(or_(User.email == normalized, User.username == normalized)).options(selectinload(User.memberships))
    )
    if not user or not user.is_active or not verify_password(password, user.password_hash):
        raise UnauthorizedError("Invalid login credentials")

    memberships = [m for m in user.memberships if m.status == "active"]
    if organization_id:
        membership = next((m for m in memberships if m.organization_id == organization_id), None)
        if not membership:
            raise UnauthorizedError("You do not have access to that organization")
    elif len(memberships) == 1:
        membership = memberships[0]
    elif not memberships:
        raise UnauthorizedError("User has no active organization membership")
    else:
        raise UnauthorizedError("organization_id is required because this user belongs to multiple organizations")

    access = create_access_token(user_id=user.id, organization_id=membership.organization_id)
    raw_refresh, token_hash, expires_at = create_refresh_token(user_id=user.id, organization_id=membership.organization_id)
    session = RefreshSession(
        id=str(uuid4()), user_id=user.id, organization_id=membership.organization_id,
        token_hash=token_hash, expires_at=expires_at,
    )
    db.add(session)
    await db.commit()
    return access, raw_refresh


async def refresh(db: AsyncSession, raw_token: str):
    token_hash = hash_token(raw_token)
    session = await db.scalar(select(RefreshSession).where(RefreshSession.token_hash == token_hash))
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    if not session or session.revoked_at or session.expires_at <= now:
        raise UnauthorizedError("Invalid or expired refresh token")
    user = await db.get(User, session.user_id)
    if not user or not user.is_active:
        raise UnauthorizedError("User is inactive")
    membership = await db.scalar(
        select(Membership).where(
            Membership.user_id == session.user_id,
            Membership.organization_id == session.organization_id,
            Membership.status == "active",
        )
    )
    if not membership:
        raise UnauthorizedError("Organization membership is inactive")
    organization = await db.get(Organization, session.organization_id)
    if not organization or organization.status != "active":
        raise UnauthorizedError("Organization is inactive")

    session.revoked_at = now
    access = create_access_token(user_id=user.id, organization_id=session.organization_id)
    raw_refresh, new_hash, expires_at = create_refresh_token(user_id=user.id, organization_id=session.organization_id)
    db.add(RefreshSession(
        id=str(uuid4()), user_id=user.id, organization_id=session.organization_id,
        token_hash=new_hash, expires_at=expires_at,
    ))
    await db.commit()
    return access, raw_refresh


async def logout(db: AsyncSession, raw_token: str) -> None:
    session = await db.scalar(select(RefreshSession).where(RefreshSession.token_hash == hash_token(raw_token)))
    if session and not session.revoked_at:
        session.revoked_at = datetime.now(timezone.utc).replace(tzinfo=None)
        await db.commit()
