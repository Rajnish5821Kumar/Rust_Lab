from typing import Any

from fastapi import APIRouter, status

from app.api.deps import DbSession, SettingsDep
from app.schemas.auth import LoginRequest, RefreshRequest, TokenPair
from app.schemas.common import ErrorResponse
from app.schemas.user import UserCreate, UserRead
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])

_UNAUTHORIZED: dict[int | str, dict[str, Any]] = {401: {"model": ErrorResponse}}


@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    responses={409: {"model": ErrorResponse}},
)
async def register(data: UserCreate, session: DbSession, settings: SettingsDep) -> UserRead:
    user = await AuthService(session, settings).register(data)
    return UserRead.model_validate(user)


@router.post("/login", response_model=TokenPair, responses=_UNAUTHORIZED)
async def login(data: LoginRequest, session: DbSession, settings: SettingsDep) -> TokenPair:
    return await AuthService(session, settings).login(data.email, data.password)


@router.post("/refresh", response_model=TokenPair, responses=_UNAUTHORIZED)
async def refresh(data: RefreshRequest, session: DbSession, settings: SettingsDep) -> TokenPair:
    """Exchange a refresh token for a new pair. The presented token is revoked (rotation)."""
    return await AuthService(session, settings).refresh(data.refresh_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(data: RefreshRequest, session: DbSession, settings: SettingsDep) -> None:
    """Revoke a refresh token. Access tokens remain valid until they expire (minutes)."""
    await AuthService(session, settings).logout(data.refresh_token)
