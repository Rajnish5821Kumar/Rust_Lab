"""User profile management and admin-only user administration."""

from collections.abc import Sequence

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import security
from app.core.errors import AuthenticationError, ConflictError, NotFoundError, PermissionDeniedError
from app.core.time import utcnow
from app.models import User
from app.repositories.token_repository import RefreshTokenRepository
from app.repositories.user_repository import (
    RoleRepository,
    UserFilters,
    UserRepository,
    UserSortField,
)
from app.schemas.user import PasswordChange, UserAdminUpdate, UserProfileUpdate


class UserService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._users = UserRepository(session)
        self._roles = RoleRepository(session)
        self._tokens = RefreshTokenRepository(session)

    async def update_profile(self, user: User, data: UserProfileUpdate) -> User:
        changes = data.model_dump(exclude_unset=True)
        new_username = changes.get("username")
        if new_username and new_username != user.username:
            if await self._users.get_by_username(new_username) is not None:
                raise ConflictError("This username is already taken")
            user.username = new_username
        if "full_name" in changes:
            user.full_name = changes["full_name"]
        await self._commit_unique()
        return user

    async def change_password(self, user: User, data: PasswordChange) -> None:
        if not security.verify_password(data.current_password, user.hashed_password):
            raise AuthenticationError("Current password is incorrect")
        user.hashed_password = security.hash_password(data.new_password)
        # Sign out every other session: existing refresh tokens stop working.
        await self._tokens.revoke_all_for_user(user.id, at=utcnow())
        await self._session.commit()

    async def list_users(
        self,
        *,
        filters: UserFilters,
        offset: int,
        limit: int,
        sort: UserSortField,
        descending: bool,
    ) -> tuple[Sequence[User], int]:
        return await self._users.list(
            filters=filters, offset=offset, limit=limit, sort=sort, descending=descending
        )

    async def admin_update(self, actor: User, user_id: int, data: UserAdminUpdate) -> User:
        target = await self._users.get_by_id(user_id)
        if target is None:
            raise NotFoundError("User not found")

        if target.id == actor.id and (
            (data.role is not None and data.role != "admin") or data.is_active is False
        ):
            # Prevents an admin from locking themselves (and possibly everyone) out.
            raise PermissionDeniedError("Admins cannot demote or deactivate their own account")

        if data.role is not None:
            role = await self._roles.get_by_name(data.role)
            if role is None:
                raise NotFoundError(f"Role {data.role!r} not found")
            target.role = role
        if data.is_active is not None:
            target.is_active = data.is_active
            if not data.is_active:
                await self._tokens.revoke_all_for_user(target.id, at=utcnow())
        await self._session.commit()
        return target

    async def _commit_unique(self) -> None:
        try:
            await self._session.commit()
        except IntegrityError as exc:
            await self._session.rollback()
            raise ConflictError("This username is already taken") from exc
