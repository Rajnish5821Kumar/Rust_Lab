from collections.abc import Awaitable, Callable
from typing import Annotated

import jwt
from fastapi import Depends, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import RoleName, Settings, get_settings
from app.core.errors import AuthenticationError, PermissionDeniedError
from app.core.redis import get_redis
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models import User
from app.repositories.user_repository import UserRepository

DbSession = Annotated[AsyncSession, Depends(get_db)]
SettingsDep = Annotated[Settings, Depends(get_settings)]
RedisDep = Annotated[Redis, Depends(get_redis)]

_bearer = HTTPBearer(auto_error=False, description="Access token from POST /api/auth/login")


async def get_current_user(
    session: DbSession,
    settings: SettingsDep,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> User:
    if credentials is None:
        raise AuthenticationError("Not authenticated")
    try:
        claims = decode_access_token(credentials.credentials, settings)
        user_id = int(claims.subject)
    except (jwt.InvalidTokenError, ValueError) as exc:
        raise AuthenticationError("Invalid or expired access token") from exc

    # Looked up on every request so deactivation and role changes apply immediately.
    user = await UserRepository(session).get_by_id(user_id)
    if user is None or not user.is_active:
        raise AuthenticationError("Invalid or expired access token")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_roles(*roles: RoleName) -> Callable[[User], Awaitable[User]]:
    allowed = frozenset(roles)

    async def dependency(user: CurrentUser) -> User:
        if user.role.name not in allowed:
            raise PermissionDeniedError("You do not have permission to perform this action")
        return user

    return dependency


class Pagination:
    def __init__(
        self,
        limit: Annotated[int, Query(ge=1, le=100)] = 20,
        offset: Annotated[int, Query(ge=0)] = 0,
    ) -> None:
        self.limit = limit
        self.offset = offset


PaginationDep = Annotated[Pagination, Depends()]
