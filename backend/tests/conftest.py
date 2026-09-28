"""Shared fixtures.

By default tests run against in-memory SQLite. Set TEST_DATABASE_URL to a PostgreSQL
async URL (as CI does) to run the same suite against PostgreSQL. Tables are recreated
for every test, so that database must be disposable.
"""

import os

# Must happen before any `app` import: settings are read at import time.
os.environ["ENVIRONMENT"] = "test"
os.environ["DATABASE_URL"] = os.environ.get("TEST_DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ["JWT_SECRET"] = "test-only-secret-not-used-outside-the-test-suite"
os.environ["REDIS_URL"] = "redis://localhost:6379/15"
os.environ["LOG_JSON"] = "false"

from collections.abc import AsyncIterator, Callable
from dataclasses import dataclass
from typing import Any

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import event, select
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool, StaticPool

from app.core.config import Settings, get_settings
from app.core.redis import get_redis
from app.core.security import hash_password
from app.db.base import Base
from app.db.seed import ensure_roles
from app.db.session import get_db
from app.main import create_app
from app.models import Role, User

DEFAULT_PASSWORD = "correct-horse-battery-staple"


class FakeRedis:
    def __init__(self, *, healthy: bool = True) -> None:
        self.healthy = healthy

    async def ping(self) -> bool:
        if not self.healthy:
            from redis.exceptions import ConnectionError as RedisConnectionError

            raise RedisConnectionError("redis unavailable")
        return True


@pytest.fixture
async def engine() -> AsyncIterator[AsyncEngine]:
    url = os.environ["DATABASE_URL"]
    if url.startswith("sqlite"):
        engine = create_async_engine(
            url, poolclass=StaticPool, connect_args={"check_same_thread": False}
        )

        @event.listens_for(engine.sync_engine, "connect")
        def _enable_foreign_keys(dbapi_connection: Any, _: Any) -> None:
            dbapi_connection.execute("PRAGMA foreign_keys=ON")

    else:
        engine = create_async_engine(url, poolclass=NullPool)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    async with async_sessionmaker(engine)() as session:
        await ensure_roles(session)
        await session.commit()

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
def session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False)


@pytest.fixture
async def db_session(
    session_factory: async_sessionmaker[AsyncSession],
) -> AsyncIterator[AsyncSession]:
    async with session_factory() as session:
        yield session


@pytest.fixture
def settings() -> Settings:
    return get_settings()


@pytest.fixture
def fake_redis() -> FakeRedis:
    return FakeRedis()


@pytest.fixture
def app(
    session_factory: async_sessionmaker[AsyncSession], settings: Settings, fake_redis: FakeRedis
) -> FastAPI:
    application = create_app(settings)

    async def override_get_db() -> AsyncIterator[AsyncSession]:
        async with session_factory() as session:
            yield session

    application.dependency_overrides[get_db] = override_get_db
    application.dependency_overrides[get_redis] = lambda: fake_redis
    return application


@pytest.fixture
async def client(app: FastAPI) -> AsyncIterator[AsyncClient]:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


@dataclass
class AuthenticatedUser:
    user: User
    access_token: str
    refresh_token: str

    @property
    def headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.access_token}"}


UserFactory = Callable[..., Any]


@pytest.fixture
def create_user(db_session: AsyncSession) -> UserFactory:
    """Insert a user directly (bypassing the API) with the given role."""

    async def factory(
        *,
        email: str = "dev@example.com",
        username: str = "dev",
        role: str = "developer",
        password: str = DEFAULT_PASSWORD,
        is_active: bool = True,
    ) -> User:
        role_obj = await db_session.scalar(select(Role).where(Role.name == role))
        assert role_obj is not None
        user = User(
            email=email,
            username=username,
            hashed_password=hash_password(password),
            role=role_obj,
            is_active=is_active,
        )
        db_session.add(user)
        await db_session.commit()
        return user

    return factory


@pytest.fixture
def login_as(client: AsyncClient, create_user: UserFactory) -> UserFactory:
    """Create a user and log in through the API, returning their tokens."""

    async def factory(**kwargs: Any) -> AuthenticatedUser:
        user = await create_user(**kwargs)
        response = await client.post(
            "/api/auth/login",
            json={"email": user.email, "password": kwargs.get("password", DEFAULT_PASSWORD)},
        )
        assert response.status_code == 200, response.text
        body = response.json()
        return AuthenticatedUser(user, body["access_token"], body["refresh_token"])

    return factory
