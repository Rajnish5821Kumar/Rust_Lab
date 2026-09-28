from datetime import timedelta

from fastapi import FastAPI
from httpx import AsyncClient
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.security import hash_refresh_token
from app.core.time import utcnow
from app.models import RefreshToken, User
from tests.conftest import DEFAULT_PASSWORD, UserFactory

REGISTRATION = {
    "email": "Alice@Example.com",
    "username": "Alice",
    "password": DEFAULT_PASSWORD,
    "full_name": "Alice Example",
}


async def test_register_creates_user_with_default_role(client: AsyncClient) -> None:
    response = await client.post("/api/auth/register", json=REGISTRATION)

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "alice@example.com"
    assert body["username"] == "alice"
    assert body["role"] == "viewer"
    assert body["is_active"] is True
    assert "password" not in body
    assert "hashed_password" not in body


async def test_register_stores_hashed_password(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    await client.post("/api/auth/register", json=REGISTRATION)

    user = await db_session.scalar(select(User).where(User.email == "alice@example.com"))
    assert user is not None
    assert user.hashed_password != DEFAULT_PASSWORD
    assert user.hashed_password.startswith("$argon2")


async def test_register_rejects_duplicate_email_case_insensitively(client: AsyncClient) -> None:
    await client.post("/api/auth/register", json=REGISTRATION)

    response = await client.post(
        "/api/auth/register",
        json={**REGISTRATION, "email": "ALICE@example.com", "username": "alice2"},
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "conflict"


async def test_register_rejects_duplicate_username(client: AsyncClient) -> None:
    await client.post("/api/auth/register", json=REGISTRATION)

    response = await client.post(
        "/api/auth/register", json={**REGISTRATION, "email": "other@example.com"}
    )

    assert response.status_code == 409


async def test_register_validation_error_does_not_echo_password(client: AsyncClient) -> None:
    response = await client.post(
        "/api/auth/register", json={**REGISTRATION, "password": "short-pw"}
    )

    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "validation_error"
    assert error["details"][0]["loc"] == ["body", "password"]
    assert error["request_id"] == response.headers["X-Request-ID"]
    assert "short-pw" not in response.text


async def test_register_rejects_invalid_username(client: AsyncClient) -> None:
    response = await client.post("/api/auth/register", json={**REGISTRATION, "username": "a b"})

    assert response.status_code == 422


async def test_bootstrap_admin_email_registers_as_admin(
    app: FastAPI, client: AsyncClient, settings: Settings
) -> None:
    app.dependency_overrides[get_settings] = lambda: settings.model_copy(
        update={"bootstrap_admin_email": "alice@example.com"}
    )

    response = await client.post("/api/auth/register", json=REGISTRATION)

    assert response.json()["role"] == "admin"


async def test_login_returns_token_pair(client: AsyncClient, create_user: UserFactory) -> None:
    await create_user(email="dev@example.com")

    response = await client.post(
        "/api/auth/login", json={"email": "DEV@example.com", "password": DEFAULT_PASSWORD}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["expires_in"] > 0
    assert body["access_token"] and body["refresh_token"]


async def test_login_records_last_login(
    client: AsyncClient, create_user: UserFactory, db_session: AsyncSession
) -> None:
    user = await create_user()
    assert user.last_login_at is None

    await client.post("/api/auth/login", json={"email": user.email, "password": DEFAULT_PASSWORD})

    await db_session.refresh(user)
    assert user.last_login_at is not None


async def test_login_failure_is_identical_for_unknown_email_and_wrong_password(
    client: AsyncClient, create_user: UserFactory
) -> None:
    await create_user(email="dev@example.com")

    wrong_password = await client.post(
        "/api/auth/login", json={"email": "dev@example.com", "password": "not-the-password"}
    )
    unknown_user = await client.post(
        "/api/auth/login", json={"email": "nobody@example.com", "password": "not-the-password"}
    )

    assert wrong_password.status_code == unknown_user.status_code == 401
    assert wrong_password.json()["error"]["message"] == unknown_user.json()["error"]["message"]
    assert wrong_password.headers["WWW-Authenticate"] == "Bearer"


async def test_inactive_user_cannot_log_in(client: AsyncClient, create_user: UserFactory) -> None:
    await create_user(is_active=False)

    response = await client.post(
        "/api/auth/login", json={"email": "dev@example.com", "password": DEFAULT_PASSWORD}
    )

    assert response.status_code == 401


async def test_refresh_rotates_tokens(client: AsyncClient, login_as: UserFactory) -> None:
    session = await login_as()

    response = await client.post("/api/auth/refresh", json={"refresh_token": session.refresh_token})

    assert response.status_code == 200
    new_refresh = response.json()["refresh_token"]
    assert new_refresh != session.refresh_token

    # The new access token works.
    me = await client.get(
        "/api/users/me", headers={"Authorization": f"Bearer {response.json()['access_token']}"}
    )
    assert me.status_code == 200


async def test_reusing_rotated_refresh_token_revokes_all_sessions(
    client: AsyncClient, login_as: UserFactory
) -> None:
    session = await login_as()
    rotated = await client.post("/api/auth/refresh", json={"refresh_token": session.refresh_token})
    latest_refresh = rotated.json()["refresh_token"]

    reuse = await client.post("/api/auth/refresh", json={"refresh_token": session.refresh_token})
    assert reuse.status_code == 401

    # The legitimately rotated token is revoked too, forcing a fresh login.
    after = await client.post("/api/auth/refresh", json={"refresh_token": latest_refresh})
    assert after.status_code == 401


async def test_expired_refresh_token_is_rejected(
    client: AsyncClient, login_as: UserFactory, db_session: AsyncSession
) -> None:
    session = await login_as()
    await db_session.execute(
        update(RefreshToken)
        .where(RefreshToken.token_hash == hash_refresh_token(session.refresh_token))
        .values(expires_at=utcnow() - timedelta(seconds=1))
    )
    await db_session.commit()

    response = await client.post("/api/auth/refresh", json={"refresh_token": session.refresh_token})

    assert response.status_code == 401


async def test_unknown_refresh_token_is_rejected(client: AsyncClient) -> None:
    response = await client.post("/api/auth/refresh", json={"refresh_token": "made-up"})

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "authentication_failed"


async def test_logout_revokes_refresh_token(client: AsyncClient, login_as: UserFactory) -> None:
    session = await login_as()

    logout = await client.post("/api/auth/logout", json={"refresh_token": session.refresh_token})
    refresh = await client.post("/api/auth/refresh", json={"refresh_token": session.refresh_token})

    assert logout.status_code == 204
    assert refresh.status_code == 401


async def test_logout_is_idempotent(client: AsyncClient, login_as: UserFactory) -> None:
    session = await login_as()
    payload = {"refresh_token": session.refresh_token}

    first = await client.post("/api/auth/logout", json=payload)
    second = await client.post("/api/auth/logout", json=payload)

    assert first.status_code == second.status_code == 204


async def test_refresh_tokens_are_stored_hashed(
    login_as: UserFactory, db_session: AsyncSession
) -> None:
    session = await login_as()

    stored = (await db_session.scalars(select(RefreshToken.token_hash))).all()

    assert session.refresh_token not in stored
    assert hash_refresh_token(session.refresh_token) in stored
