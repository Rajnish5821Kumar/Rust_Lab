from httpx import AsyncClient

from tests.conftest import FakeRedis


async def test_health_returns_expected_payload(client: AsyncClient) -> None:
    response = await client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "devvault"}


async def test_readiness_ok_when_dependencies_available(client: AsyncClient) -> None:
    response = await client.get("/api/health/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "checks": {"database": "ok", "redis": "ok"}}


async def test_readiness_reports_503_when_redis_is_down(
    client: AsyncClient, fake_redis: FakeRedis
) -> None:
    fake_redis.healthy = False

    response = await client.get("/api/health/ready")

    assert response.status_code == 503
    assert response.json() == {"status": "error", "checks": {"database": "ok", "redis": "error"}}


async def test_openapi_schema_is_served(client: AsyncClient) -> None:
    response = await client.get("/api/openapi.json")

    assert response.status_code == 200
    paths = response.json()["paths"]
    assert "/api/health" in paths
    assert "/api/auth/login" in paths
