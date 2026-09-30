"""phase 1 foundation

Revision ID: 0001_phase1_foundation
Revises:
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

revision = "0001_phase1_foundation"
down_revision = None
branch_labels = None
depends_on = None


def id_col():
    return sa.Column("id", mysql.CHAR(36), primary_key=True, nullable=False)


def upgrade() -> None:
    op.create_table(
        "organizations",
        id_col(),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("code", sa.String(80), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="active"),
        sa.Column("storage_mode", sa.String(20), nullable=False, server_default="shared"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("code", name="uq_organizations_code"),
    )
    op.create_table(
        "users",
        id_col(),
        sa.Column("first_name", sa.String(100), nullable=False),
        sa.Column("last_name", sa.String(100), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("username", sa.String(80), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("email", name="uq_users_email"),
        sa.UniqueConstraint("username", name="uq_users_username"),
    )
    op.create_table(
        "permissions",
        id_col(),
        sa.Column("code", sa.String(120), nullable=False),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("description", sa.Text()),
        sa.UniqueConstraint("code", name="uq_permissions_code"),
    )
    op.create_table(
        "memberships",
        id_col(),
        sa.Column("organization_id", mysql.CHAR(36), nullable=False),
        sa.Column("user_id", mysql.CHAR(36), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("organization_id", "user_id", name="uq_membership_org_user"),
    )
    op.create_table(
        "roles",
        id_col(),
        sa.Column("organization_id", mysql.CHAR(36), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("code", sa.String(80), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("is_system", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("organization_id", "code", name="uq_role_org_code"),
    )
    op.create_table(
        "membership_roles",
        sa.Column("membership_id", mysql.CHAR(36), primary_key=True),
        sa.Column("role_id", mysql.CHAR(36), primary_key=True),
        sa.ForeignKeyConstraint(["membership_id"], ["memberships.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("membership_id", "role_id", name="uq_membership_role"),
    )
    op.create_table(
        "role_permissions",
        sa.Column("role_id", mysql.CHAR(36), primary_key=True),
        sa.Column("permission_id", mysql.CHAR(36), primary_key=True),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["permission_id"], ["permissions.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("role_id", "permission_id", name="uq_role_permission"),
    )
    op.create_table(
        "tenant_configurations",
        id_col(),
        sa.Column("organization_id", mysql.CHAR(36), nullable=False),
        sa.Column("timezone", sa.String(80), nullable=False, server_default="Africa/Nairobi"),
        sa.Column("locale", sa.String(20), nullable=False, server_default="en-KE"),
        sa.Column("settings", mysql.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("organization_id", name="uq_tenant_config_org"),
    )
    op.create_table(
        "database_connections",
        id_col(),
        sa.Column("organization_id", mysql.CHAR(36), nullable=False),
        sa.Column("mode", sa.String(20), nullable=False, server_default="shared"),
        sa.Column("connection_url", sa.Text()),
        sa.Column("secret_ref", sa.String(255)),
        sa.Column("schema_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("is_healthy", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("last_health_check_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("organization_id", name="uq_db_connection_org"),
    )
    op.create_table(
        "refresh_sessions",
        id_col(),
        sa.Column("user_id", mysql.CHAR(36), nullable=False),
        sa.Column("organization_id", mysql.CHAR(36), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("token_hash", name="uq_refresh_token_hash"),
    )
    op.bulk_insert(
        sa.table("permissions", sa.column("id", mysql.CHAR(36)), sa.column("code", sa.String()), sa.column("name", sa.String())),
        [
            {"id": "00000000-0000-0000-0000-000000000001", "code": "organization.read", "name": "Read organization"},
            {"id": "00000000-0000-0000-0000-000000000002", "code": "users.read", "name": "Read users"},
            {"id": "00000000-0000-0000-0000-000000000003", "code": "roles.read", "name": "Read roles"},
            {"id": "00000000-0000-0000-0000-000000000004", "code": "roles.manage", "name": "Manage roles"},
            {"id": "00000000-0000-0000-0000-000000000005", "code": "permissions.read", "name": "Read permissions"},
        ],
    )


def downgrade() -> None:
    for table in ["refresh_sessions", "database_connections", "tenant_configurations", "role_permissions", "membership_roles", "roles", "memberships", "permissions", "users", "organizations"]:
        op.drop_table(table)
