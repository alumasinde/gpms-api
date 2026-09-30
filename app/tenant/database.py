from collections.abc import AsyncIterator

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import get_platform_db
from app.core.exceptions import ConflictError
from app.models import DatabaseConnection
from app.tenant.context import TenantContext


class TenantDatabaseResolver:
    """Resolve the tenant application database without changing domain services.

    Shared mode uses the platform/shared connection in Phase 1. Dedicated mode
    can use a registered connection URL. In production, prefer `secret_ref` and
    resolve credentials from a secrets manager instead of storing them in the DB.
    """

    def __init__(self) -> None:
        self._engines: dict[str, AsyncEngine] = {}

    async def session(self, context: TenantContext) -> AsyncIterator[AsyncSession]:
        if context.storage_mode == "shared" or not context.database_url:
            async for session in get_platform_db():
                yield session
            return

        engine = self._engines.get(context.organization_id)
        if engine is None:
            engine = create_async_engine(context.database_url, pool_pre_ping=True, pool_recycle=1800)
            self._engines[context.organization_id] = engine
        factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        async with factory() as session:
            yield session

    async def close(self) -> None:
        for engine in self._engines.values():
            await engine.dispose()
        self._engines.clear()


async def resolve_tenant_database_url(db: AsyncSession, organization_id: str) -> str | None:
    connection = await db.scalar(
        select(DatabaseConnection).where(DatabaseConnection.organization_id == organization_id)
    )
    if not connection or connection.mode == "shared":
        return None
    if not connection.connection_url:
        raise ConflictError("Dedicated tenant database is not configured")
    return connection.connection_url
