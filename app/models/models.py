from __future__ import annotations
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.mysql import CHAR, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Organization(TimestampMixin, Base):
    __tablename__ = "organizations"

    id: Mapped[str] = mapped_column(CHAR(36), primary_key=True, default=lambda: str(__import__("uuid").uuid4()))
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    code: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="active")
    storage_mode: Mapped[str] = mapped_column(String(20), nullable=False, default="shared")

    memberships: Mapped[list[Membership]] = relationship(back_populates="organization", cascade="all, delete-orphan")
    roles: Mapped[list[Role]] = relationship(back_populates="organization", cascade="all, delete-orphan")
    tenant_configuration: Mapped[TenantConfiguration | None] = relationship(
        back_populates="organization", uselist=False, cascade="all, delete-orphan"
    )
    database_connection: Mapped[DatabaseConnection | None] = relationship(
        back_populates="organization", uselist=False, cascade="all, delete-orphan"
    )


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(CHAR(36), primary_key=True, default=lambda: str(__import__("uuid").uuid4()))
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    username: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    memberships: Mapped[list[Membership]] = relationship(back_populates="user")


class Membership(TimestampMixin, Base):
    __tablename__ = "memberships"
    __table_args__ = (UniqueConstraint("organization_id", "user_id", name="uq_membership_org_user"),)

    id: Mapped[str] = mapped_column(CHAR(36), primary_key=True, default=lambda: str(__import__("uuid").uuid4()))
    organization_id: Mapped[str] = mapped_column(CHAR(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[str] = mapped_column(CHAR(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="active")

    organization: Mapped[Organization] = relationship(back_populates="memberships")
    user: Mapped[User] = relationship(back_populates="memberships")
    roles: Mapped[list[Role]] = relationship(secondary="membership_roles", back_populates="memberships")


class Role(TimestampMixin, Base):
    __tablename__ = "roles"
    __table_args__ = (UniqueConstraint("organization_id", "code", name="uq_role_org_code"),)

    id: Mapped[str] = mapped_column(CHAR(36), primary_key=True, default=lambda: str(__import__("uuid").uuid4()))
    organization_id: Mapped[str] = mapped_column(CHAR(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(String(80), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    is_system: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    organization: Mapped[Organization] = relationship(back_populates="roles")
    memberships: Mapped[list[Membership]] = relationship(secondary="membership_roles", back_populates="roles")
    permissions: Mapped[list[Permission]] = relationship(secondary="role_permissions", back_populates="roles")


class Permission(Base):
    __tablename__ = "permissions"

    id: Mapped[str] = mapped_column(CHAR(36), primary_key=True, default=lambda: str(__import__("uuid").uuid4()))
    code: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)

    roles: Mapped[list[Role]] = relationship(secondary="role_permissions", back_populates="permissions")


class MembershipRole(Base):
    __tablename__ = "membership_roles"
    __table_args__ = (UniqueConstraint("membership_id", "role_id", name="uq_membership_role"),)

    membership_id: Mapped[str] = mapped_column(CHAR(36), ForeignKey("memberships.id", ondelete="CASCADE"), primary_key=True)
    role_id: Mapped[str] = mapped_column(CHAR(36), ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True)


class RolePermission(Base):
    __tablename__ = "role_permissions"
    __table_args__ = (UniqueConstraint("role_id", "permission_id", name="uq_role_permission"),)

    role_id: Mapped[str] = mapped_column(CHAR(36), ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True)
    permission_id: Mapped[str] = mapped_column(CHAR(36), ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True)


class TenantConfiguration(TimestampMixin, Base):
    __tablename__ = "tenant_configurations"

    id: Mapped[str] = mapped_column(CHAR(36), primary_key=True, default=lambda: str(__import__("uuid").uuid4()))
    organization_id: Mapped[str] = mapped_column(CHAR(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, unique=True)
    timezone: Mapped[str] = mapped_column(String(80), nullable=False, default="Africa/Nairobi")
    locale: Mapped[str] = mapped_column(String(20), nullable=False, default="en-KE")
    settings: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    organization: Mapped[Organization] = relationship(back_populates="tenant_configuration")


class DatabaseConnection(TimestampMixin, Base):
    __tablename__ = "database_connections"

    id: Mapped[str] = mapped_column(CHAR(36), primary_key=True, default=lambda: str(__import__("uuid").uuid4()))
    organization_id: Mapped[str] = mapped_column(CHAR(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, unique=True)
    mode: Mapped[str] = mapped_column(String(20), nullable=False, default="shared")
    connection_url: Mapped[str | None] = mapped_column(Text)
    secret_ref: Mapped[str | None] = mapped_column(String(255))
    schema_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    is_healthy: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    last_health_check_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    organization: Mapped[Organization] = relationship(back_populates="database_connection")


class RefreshSession(TimestampMixin, Base):
    __tablename__ = "refresh_sessions"

    id: Mapped[str] = mapped_column(CHAR(36), primary_key=True, default=lambda: str(__import__("uuid").uuid4()))
    user_id: Mapped[str] = mapped_column(CHAR(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    organization_id: Mapped[str] = mapped_column(CHAR(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
