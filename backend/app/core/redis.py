from collections.abc import AsyncIterator

from redis.asyncio import Redis

from app.core.config import get_settings


async def get_redis() -> AsyncIterator[Redis]:
    """Request-scoped Redis client.

    A client per request avoids sharing a connection pool across event loops, which breaks
    on serverless runtimes. Only the readiness check uses Redis for now, so the cost is small.
    """
    client = Redis.from_url(
        get_settings().redis_url,
        socket_connect_timeout=2,
        socket_timeout=2,
        decode_responses=True,
    )
    try:
        yield client
    finally:
        await client.aclose()
