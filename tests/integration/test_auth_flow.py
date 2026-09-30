import os
from uuid import uuid4

import pytest

from app.core.database import SessionLocal
from app.models import DatabaseConnection, Organization, User
from app.schemas.auth import RegisterRequest
from app.services import auth as auth_service

pytestmark = pytest.mark.skipif(
    not os.getenv("RUN_DB_TESTS"),
    reason="Set RUN_DB_TESTS=1 with a configured MySQL environment to run integration tests",
)


@pytest.mark.asyncio
async def test_registration_and_login_by_email_and_username():
    suffix = uuid4().hex[:10]
    data = RegisterRequest(
        organization_name=f"Integration Test {suffix}",
        organization_code=f"itest-{suffix}",
        first_name="Integration",
        last_name="Tester",
        email=f"integration-{suffix}@example.com",
        username=f"itest-{suffix}",
        password="VeryStrongPassword123!",
    )

    async with SessionLocal() as db:
        user, organization = await auth_service.register(db, data)
        connection = await db.get(DatabaseConnection, organization.id)
        assert connection is not None
        assert connection.organization_id == organization.id
        assert connection.mode == "shared"

        access_by_email, refresh_by_email = await auth_service.login(
            db, data.email, data.password, organization.id,
        )
        access_by_username, refresh_by_username = await auth_service.login(
            db, data.username, data.password, organization.id,
        )

        assert access_by_email
        assert refresh_by_email
        assert access_by_username
        assert refresh_by_username

        user_row = await db.get(User, user.id)
        org_row = await db.get(Organization, organization.id)
        assert user_row is not None
        assert org_row is not None

        await db.delete(user_row)
        await db.delete(org_row)
        await db.commit()
