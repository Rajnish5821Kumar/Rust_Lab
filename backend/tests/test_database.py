import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.seed import DEFAULT_ROLES, ensure_roles
from app.models import RefreshToken, Role, User
from app.repositories.user_repository import UserFilters, UserRepository
from tests.conftest import UserFactory


async def test_default_roles_are_seeded(db_session: AsyncSession) -> None:
    names = set((await db_session.scalars(select(Role.name))).all())

    assert names == set(DEFAULT_ROLES)


async def test_ensure_roles_is_idempotent(db_session: AsyncSession) -> None:
    await ensure_roles(db_session)
    await ensure_roles(db_session)
    await db_session.commit()

    count = await db_session.scalar(select(func.count()).select_from(Role))
    assert count == len(DEFAULT_ROLES)


async def test_email_must_be_lowercase(db_session: AsyncSession) -> None:
    role = await db_session.scalar(select(Role).where(Role.name == "viewer"))
    db_session.add(User(email="Upper@Example.com", username="u", hashed_password="x", role=role))

    with pytest.raises(IntegrityError):
        await db_session.commit()


async def test_email_is_unique(db_session: AsyncSession, create_user: UserFactory) -> None:
    await create_user(email="dup@example.com", username="first")

    with pytest.raises(IntegrityError):
        await create_user(email="dup@example.com", username="second")


async def test_deleting_user_cascades_to_refresh_tokens(
    db_session: AsyncSession, create_user: UserFactory
) -> None:
    from app.core.time import utcnow

    user = await create_user()
    db_session.add(RefreshToken(user_id=user.id, token_hash="a" * 64, expires_at=utcnow()))
    await db_session.commit()

    await db_session.delete(user)
    await db_session.commit()

    assert await db_session.scalar(select(func.count()).select_from(RefreshToken)) == 0


async def test_role_cannot_be_deleted_while_in_use(
    db_session: AsyncSession, create_user: UserFactory
) -> None:
    await create_user(role="viewer")
    role = await db_session.scalar(select(Role).where(Role.name == "viewer"))
    assert role is not None

    await db_session.delete(role)
    with pytest.raises(IntegrityError):
        await db_session.commit()


async def test_user_repository_filters_by_active_state(
    db_session: AsyncSession, create_user: UserFactory
) -> None:
    await create_user(email="a@example.com", username="active")
    await create_user(email="i@example.com", username="inactive", is_active=False)

    users, total = await UserRepository(db_session).list(
        filters=UserFilters(is_active=False), offset=0, limit=10
    )

    assert total == 1
    assert [u.username for u in users] == ["inactive"]
