from fastapi import APIRouter, Response, status

from app.api.deps import DbSession, RedisDep, SettingsDep
from app.schemas.health import HealthResponse, ReadinessResponse
from app.services.health_service import check_database, check_redis

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse, summary="Liveness check")
async def health(settings: SettingsDep) -> HealthResponse:
    """Returns immediately without touching dependencies; used for liveness probes."""
    return HealthResponse(status="ok", service=settings.app_name)


@router.get(
    "/health/ready",
    response_model=ReadinessResponse,
    responses={503: {"model": ReadinessResponse, "description": "A dependency is unavailable"}},
    summary="Readiness check (database and Redis)",
)
async def readiness(response: Response, session: DbSession, redis: RedisDep) -> ReadinessResponse:
    checks = {"database": await check_database(session), "redis": await check_redis(redis)}
    healthy = all(result == "ok" for result in checks.values())
    if not healthy:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return ReadinessResponse(status="ok" if healthy else "error", checks=checks)
