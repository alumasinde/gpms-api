from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings

settings = get_settings()
engine = create_async_engine(
    settings.platform_database_url,
    pool_pre_ping=True,
    pool_recycle=settings.mysql_pool_recycle,
    pool_size=settings.mysql_pool_size,
    max_overflow=settings.mysql_max_overflow,
    pool_timeout=settings.mysql_pool_timeout,
)
SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_platform_db() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session
