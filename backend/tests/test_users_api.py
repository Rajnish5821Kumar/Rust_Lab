from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import DEFAULT_PASSWORD, UserFactory


async def test_me_requires_authentication(client: AsyncClient) -> None:
    response = await client.get("/api/users/me")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "authentication_failed"


async def test_me_rejects_garbage_token(client: AsyncClient) -> None:
    response = await client.get("/api/users/me", headers={"Authorization": "Bearer not-a-jwt"})

    assert response.status_code == 401


async def test_me_returns_current_user(client: AsyncClient, login_as: UserFactory) -> None:
    session = await login_as(email="me@example.com", username="me-user")

    response = await client.get("/api/users/me", headers=session.headers)

    assert response.status_code == 200
    assert response.json()["email"] == "me@example.com"
    assert response.json()["role"] == "developer"
    assert response.json()["created_at"].endswith("Z")
    assert response.json()["last_login_at"].endswith("Z")


async def test_deactivated_user_access_token_stops_working(
    client: AsyncClient, login_as: UserFactory, db_session: AsyncSession
) -> None:
    session = await login_as()
    session.user.is_active = False
    db_session.add(session.user)
    await db_session.commit()

    response = await client.get("/api/users/me", headers=session.headers)

    assert response.status_code == 401


async def test_update_profile(client: AsyncClient, login_as: UserFactory) -> None:
    session = await login_as()

    response = await client.patch(
        "/api/users/me",
        headers=session.headers,
        json={"full_name": "Dev Eloper", "username": "New.Name"},
    )

    assert response.status_code == 200
    assert response.json()["full_name"] == "Dev Eloper"
    assert response.json()["username"] == "new.name"


async def test_update_profile_rejects_taken_username(
    client: AsyncClient, login_as: UserFactory, create_user: UserFactory
) -> None:
    await create_user(email="other@example.com", username="taken")
    session = await login_as()

    response = await client.patch(
        "/api/users/me", headers=session.headers, json={"username": "taken"}
    )

    assert response.status_code == 409


async def test_change_password_revokes_sessions(client: AsyncClient, login_as: UserFactory) -> None:
    session = await login_as()
    new_password = "an-entirely-new-password"

    changed = await client.post(
        "/api/users/me/password",
        headers=session.headers,
        json={"current_password": DEFAULT_PASSWORD, "new_password": new_password},
    )
    assert changed.status_code == 204

    refresh = await client.post("/api/auth/refresh", json={"refresh_token": session.refresh_token})
    old_login = await client.post(
        "/api/auth/login", json={"email": session.user.email, "password": DEFAULT_PASSWORD}
    )
    new_login = await client.post(
        "/api/auth/login", json={"email": session.user.email, "password": new_password}
    )
    assert refresh.status_code == 401
    assert old_login.status_code == 401
    assert new_login.status_code == 200


async def test_change_password_requires_current_password(
    client: AsyncClient, login_as: UserFactory
) -> None:
    session = await login_as()

    response = await client.post(
        "/api/users/me/password",
        headers=session.headers,
        json={"current_password": "wrong-password", "new_password": "an-entirely-new-password"},
    )

    assert response.status_code == 401


async def test_list_users_forbidden_for_non_admin(
    client: AsyncClient, login_as: UserFactory
) -> None:
    session = await login_as(role="developer")

    response = await client.get("/api/users", headers=session.headers)

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "permission_denied"


async def test_admin_lists_users_with_pagination_filter_and_sort(
    client: AsyncClient, login_as: UserFactory, create_user: UserFactory
) -> None:
    admin = await login_as(email="admin@example.com", username="admin", role="admin")
    for name in ("carol", "bob", "dave"):
        await create_user(email=f"{name}@example.com", username=name, role="viewer")

    page = await client.get(
        "/api/users",
        headers=admin.headers,
        params={"role": "viewer", "sort": "-username", "limit": 2, "offset": 0},
    )

    assert page.status_code == 200
    body = page.json()
    assert body["total"] == 3
    assert body["limit"] == 2
    assert [u["username"] for u in body["items"]] == ["dave", "carol"]

    second = await client.get(
        "/api/users",
        headers=admin.headers,
        params={"role": "viewer", "sort": "-username", "limit": 2, "offset": 2},
    )
    assert [u["username"] for u in second.json()["items"]] == ["bob"]


async def test_list_users_rejects_unknown_sort_field(
    client: AsyncClient, login_as: UserFactory
) -> None:
    admin = await login_as(role="admin")

    response = await client.get(
        "/api/users", headers=admin.headers, params={"sort": "hashed_password"}
    )

    assert response.status_code == 422


async def test_admin_changes_user_role(
    client: AsyncClient, login_as: UserFactory, create_user: UserFactory
) -> None:
    admin = await login_as(email="admin@example.com", username="admin", role="admin")
    target = await create_user(email="v@example.com", username="viewer1", role="viewer")

    response = await client.patch(
        f"/api/users/{target.id}", headers=admin.headers, json={"role": "developer"}
    )

    assert response.status_code == 200
    assert response.json()["role"] == "developer"


async def test_admin_cannot_demote_self(client: AsyncClient, login_as: UserFactory) -> None:
    admin = await login_as(role="admin")

    response = await client.patch(
        f"/api/users/{admin.user.id}", headers=admin.headers, json={"role": "viewer"}
    )

    assert response.status_code == 403


async def test_admin_deactivating_user_revokes_their_sessions(
    client: AsyncClient, login_as: UserFactory
) -> None:
    admin = await login_as(email="admin@example.com", username="admin", role="admin")
    victim = await login_as(email="v@example.com", username="victim", role="viewer")

    response = await client.patch(
        f"/api/users/{victim.user.id}", headers=admin.headers, json={"is_active": False}
    )
    refresh = await client.post("/api/auth/refresh", json={"refresh_token": victim.refresh_token})

    assert response.status_code == 200
    assert response.json()["is_active"] is False
    assert refresh.status_code == 401


async def test_admin_update_unknown_user_returns_404(
    client: AsyncClient, login_as: UserFactory
) -> None:
    admin = await login_as(role="admin")

    response = await client.patch(
        "/api/users/99999", headers=admin.headers, json={"role": "viewer"}
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"
