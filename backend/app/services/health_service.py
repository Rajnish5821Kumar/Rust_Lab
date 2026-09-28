import logging

from redis.asyncio import Redis
from redis.exceptions import RedisError
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.health import CheckStatus

logger = logging.getLogger(__name__)


async def check_database(session: AsyncSession) -> CheckStatus:
    try:
        await session.execute(text("SELECT 1"))
    except (SQLAlchemyError, OSError):
        logger.exception("database readiness check failed")
        return "error"
    return "ok"


async def check_redis(redis: Redis) -> CheckStatus:
    try:
        await redis.ping()
    except (RedisError, OSError):
        logger.exception("redis readiness check failed")
        return "error"
    return "ok"
