"""Registration, login and refresh-token rotation."""

import logging
from datetime import timedelta

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import security
from app.core.config import Settings
from app.core.errors import AuthenticationError, ConflictError
from app.core.time import ensure_aware, utcnow
from app.models import RefreshToken, User
from app.repositories.token_repository import RefreshTokenRepository
from app.repositories.user_repository import RoleRepository, UserRepository
from app.schemas.auth import TokenPair
from app.schemas.user import UserCreate

logger = logging.getLogger(__name__)

INVALID_CREDENTIALS = "Invalid email or password"
INVALID_REFRESH_TOKEN = "Invalid or expired refresh token"  # noqa: S105


class AuthService:
    def __init__(self, session: AsyncSession, settings: Settings) -> None:
        self._session = session
        self._settings = settings
        self._users = UserRepository(session)
        self._roles = RoleRepository(session)
        self._tokens = RefreshTokenRepository(session)

    async def register(self, data: UserCreate) -> User:
        if await self._users.get_by_email(data.email) is not None:
            raise ConflictError("An account with this email already exists")
        if await self._users.get_by_username(data.username) is not None:
            raise ConflictError("This username is already taken")

        role_name = (
            "admin"
            if data.email == self._settings.bootstrap_admin_email
            else self._settings.default_user_role
        )
        role = await self._roles.get_by_name(role_name)
        if role is None:
            raise RuntimeError(f"Role {role_name!r} is missing; run database migrations")

        user = User(
            email=data.email,
            username=data.username,
            full_name=data.full_name,
            hashed_password=security.hash_password(data.password),
            role=role,
        )
        self._users.add(user)
        try:
            await self._session.commit()
        except IntegrityError as exc:
            # Lost a race with a concurrent registration for the same email/username.
            await self._session.rollback()
            raise ConflictError("An account with this email or username already exists") from exc
        logger.info("user registered", extra={"user_id": user.id, "role": role_name})
        return user

    async def login(self, email: str, password: str) -> TokenPair:
        user = await self._users.get_by_email(email)
        if user is None:
            security.verify_dummy_password(password)
            raise AuthenticationError(INVALID_CREDENTIALS)
        if not security.verify_password(password, user.hashed_password):
            raise AuthenticationError(INVALID_CREDENTIALS)
        if not user.is_active:
            raise AuthenticationError("This account has been deactivated")

        if security.password_needs_rehash(user.hashed_password):
            user.hashed_password = security.hash_password(password)
        user.last_login_at = utcnow()
        tokens = self._issue_tokens(user)
        await self._session.commit()
        return tokens

    async def refresh(self, refresh_token: str) -> TokenPair:
        now = utcnow()
        record = await self._tokens.get_by_hash_for_update(
            security.hash_refresh_token(refresh_token)
        )
        if record is None:
            raise AuthenticationError(INVALID_REFRESH_TOKEN)

        if record.revoked_at is not None:
            # A rotated-out token was presented again: assume it was stolen and
            # revoke every session for this user.
            await self._tokens.revoke_all_for_user(record.user_id, at=now)
            await self._session.commit()
            logger.warning("refresh token reuse detected", extra={"user_id": record.user_id})
            raise AuthenticationError(INVALID_REFRESH_TOKEN)

        if ensure_aware(record.expires_at) <= now:
            raise AuthenticationError(INVALID_REFRESH_TOKEN)

        user = await self._users.get_by_id(record.user_id)
        if user is None or not user.is_active:
            raise AuthenticationError(INVALID_REFRESH_TOKEN)

        record.revoked_at = now
        tokens = self._issue_tokens(user)
        await self._session.commit()
        return tokens

    async def logout(self, refresh_token: str) -> None:
        """Revoke the given refresh token. Unknown or already revoked tokens are ignored."""
        record = await self._tokens.get_by_hash_for_update(
            security.hash_refresh_token(refresh_token)
        )
        if record is not None and record.revoked_at is None:
            record.revoked_at = utcnow()
            await self._session.commit()

    def _issue_tokens(self, user: User) -> TokenPair:
        """Create a token pair; the caller commits the new refresh-token row."""
        access_token, expires_in = security.create_access_token(str(user.id), self._settings)
        refresh_token = security.generate_refresh_token()
        self._tokens.add(
            RefreshToken(
                user_id=user.id,
                token_hash=security.hash_refresh_token(refresh_token),
                expires_at=utcnow() + timedelta(days=self._settings.refresh_token_expire_days),
            )
        )
        return TokenPair(
            access_token=access_token, refresh_token=refresh_token, expires_in=expires_in
        )
