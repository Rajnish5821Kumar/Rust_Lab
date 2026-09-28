"""Password hashing and token primitives.

Access tokens are short-lived JWTs. Refresh tokens are opaque random strings;
only their SHA-256 digest is stored, so a database leak does not leak usable tokens.
"""

import hashlib
import secrets
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

from app.core.config import Settings
from app.core.time import utcnow

ACCESS_TOKEN_TYPE = "access"  # noqa: S105 - a claim value, not a secret

_password_hasher = PasswordHasher()
# Used to keep login timing similar whether or not the account exists.
_DUMMY_HASH = _password_hasher.hash(secrets.token_urlsafe(16))


def hash_password(password: str) -> str:
    return _password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return _password_hasher.verify(password_hash, password)
    except (VerificationError, InvalidHashError):
        return False


def verify_dummy_password(password: str) -> None:
    verify_password(password, _DUMMY_HASH)


def password_needs_rehash(password_hash: str) -> bool:
    return _password_hasher.check_needs_rehash(password_hash)


@dataclass(frozen=True, slots=True)
class AccessTokenClaims:
    subject: str
    token_id: str
    issued_at: datetime
    expires_at: datetime


def create_access_token(
    subject: str, settings: Settings, *, now: datetime | None = None
) -> tuple[str, int]:
    """Return the encoded token and its lifetime in seconds."""
    issued_at = now or utcnow()
    lifetime = timedelta(minutes=settings.access_token_expire_minutes)
    payload = {
        "sub": subject,
        "type": ACCESS_TOKEN_TYPE,
        "iss": settings.jwt_issuer,
        "iat": issued_at,
        "exp": issued_at + lifetime,
        "jti": uuid.uuid4().hex,
    }
    token = jwt.encode(
        payload, settings.jwt_secret.get_secret_value(), algorithm=settings.jwt_algorithm
    )
    return token, int(lifetime.total_seconds())


def decode_access_token(token: str, settings: Settings) -> AccessTokenClaims:
    """Decode and validate an access token. Raises `jwt.InvalidTokenError` on any problem."""
    payload = jwt.decode(
        token,
        settings.jwt_secret.get_secret_value(),
        algorithms=[settings.jwt_algorithm],
        issuer=settings.jwt_issuer,
        options={"require": ["sub", "type", "iss", "iat", "exp", "jti"]},
    )
    if payload["type"] != ACCESS_TOKEN_TYPE:
        raise jwt.InvalidTokenError("Unexpected token type")
    return AccessTokenClaims(
        subject=str(payload["sub"]),
        token_id=str(payload["jti"]),
        issued_at=datetime.fromtimestamp(payload["iat"], tz=UTC),
        expires_at=datetime.fromtimestamp(payload["exp"], tz=UTC),
    )


def generate_refresh_token() -> str:
    return secrets.token_urlsafe(48)


def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
