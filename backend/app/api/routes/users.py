from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import CurrentUser, DbSession, PaginationDep, require_roles
from app.core.config import RoleName
from app.models import User
from app.repositories.user_repository import UserFilters
from app.schemas.common import ErrorResponse, Page
from app.schemas.user import PasswordChange, UserAdminUpdate, UserProfileUpdate, UserRead
from app.services.user_service import UserService

router = APIRouter(
    prefix="/users",
    tags=["users"],
    responses={401: {"model": ErrorResponse}},
)

AdminUser = Annotated[User, Depends(require_roles("admin"))]
_SORT_PATTERN = r"^-?(created_at|email|username)$"


@router.get("/me", response_model=UserRead)
async def read_me(user: CurrentUser) -> UserRead:
    return UserRead.model_validate(user)


@router.patch("/me", response_model=UserRead, responses={409: {"model": ErrorResponse}})
async def update_me(data: UserProfileUpdate, user: CurrentUser, session: DbSession) -> UserRead:
    updated = await UserService(session).update_profile(user, data)
    return UserRead.model_validate(updated)


@router.post("/me/password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(data: PasswordChange, user: CurrentUser, session: DbSession) -> None:
    """Change the password and revoke all refresh tokens for this account."""
    await UserService(session).change_password(user, data)


@router.get("", response_model=Page[UserRead], responses={403: {"model": ErrorResponse}})
async def list_users(
    _: AdminUser,
    session: DbSession,
    pagination: PaginationDep,
    role: RoleName | None = None,
    is_active: bool | None = None,
    sort: Annotated[
        str, Query(pattern=_SORT_PATTERN, description="Field to sort by; prefix '-' for desc")
    ] = "created_at",
) -> Page[UserRead]:
    users, total = await UserService(session).list_users(
        filters=UserFilters(role=role, is_active=is_active),
        offset=pagination.offset,
        limit=pagination.limit,
        sort=sort.removeprefix("-"),  # type: ignore[arg-type]  # validated by the pattern
        descending=sort.startswith("-"),
    )
    return Page(
        items=[UserRead.model_validate(u) for u in users],
        total=total,
        limit=pagination.limit,
        offset=pagination.offset,
    )


@router.patch(
    "/{user_id}",
    response_model=UserRead,
    responses={403: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
)
async def admin_update_user(
    user_id: int, data: UserAdminUpdate, admin: AdminUser, session: DbSession
) -> UserRead:
    updated = await UserService(session).admin_update(admin, user_id, data)
    return UserRead.model_validate(updated)
