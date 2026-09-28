from collections.abc import AsyncIterator
from functools import lru_cache

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from app.core.config import get_settings


@lru_cache
def get_engine() -> AsyncEngine:
    settings = get_settings()
    if settings.database_null_pool:
        return create_async_engine(
            settings.database_url, echo=settings.database_echo, poolclass=NullPool
        )
    return create_async_engine(
        settings.database_url, echo=settings.database_echo, pool_pre_ping=True
    )


@lru_cache
def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(get_engine(), expire_on_commit=False)


async def get_db() -> AsyncIterator[AsyncSession]:
    """Request-scoped session. Services commit explicitly; anything uncommitted rolls back."""
    async with get_sessionmaker()() as session:
        yield session
