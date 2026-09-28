from datetime import timedelta

import jwt
import pytest
from pydantic import SecretStr

from app.core.config import Settings
from app.core.security import (
    create_access_token,
    decode_access_token,
    generate_refresh_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)
from app.core.time import utcnow


def test_password_hash_roundtrip() -> None:
    hashed = hash_password("a-long-enough-password")

    assert hashed != "a-long-enough-password"
    assert hashed.startswith("$argon2")
    assert verify_password("a-long-enough-password", hashed)
    assert not verify_password("wrong-password", hashed)


def test_password_hashes_are_salted() -> None:
    assert hash_password("same-password-twice") != hash_password("same-password-twice")


def test_verify_password_rejects_malformed_hash() -> None:
    assert not verify_password("anything", "not-a-real-hash")


def test_access_token_roundtrip(settings: Settings) -> None:
    token, expires_in = create_access_token("42", settings)

    claims = decode_access_token(token, settings)

    assert claims.subject == "42"
    assert expires_in == settings.access_token_expire_minutes * 60
    assert claims.expires_at - claims.issued_at == timedelta(seconds=expires_in)


def test_expired_access_token_is_rejected(settings: Settings) -> None:
    issued = utcnow() - timedelta(minutes=settings.access_token_expire_minutes + 1)
    token, _ = create_access_token("42", settings, now=issued)

    with pytest.raises(jwt.ExpiredSignatureError):
        decode_access_token(token, settings)


def test_token_signed_with_other_secret_is_rejected(settings: Settings) -> None:
    other = settings.model_copy(update={"jwt_secret": SecretStr("x" * 48)})
    token, _ = create_access_token("42", other)

    with pytest.raises(jwt.InvalidSignatureError):
        decode_access_token(token, settings)


def test_token_with_wrong_type_is_rejected(settings: Settings) -> None:
    now = utcnow()
    token = jwt.encode(
        {
            "sub": "42",
            "type": "refresh",
            "iss": settings.jwt_issuer,
            "iat": now,
            "exp": now + timedelta(minutes=5),
            "jti": "abc",
        },
        settings.jwt_secret.get_secret_value(),
        algorithm=settings.jwt_algorithm,
    )

    with pytest.raises(jwt.InvalidTokenError, match="Unexpected token type"):
        decode_access_token(token, settings)


def test_token_with_unsigned_algorithm_is_rejected(settings: Settings) -> None:
    now = utcnow()
    token = jwt.encode(
        {"sub": "1", "type": "access", "iss": "devvault", "iat": now, "exp": now, "jti": "a"},
        key=None,
        algorithm="none",
    )

    with pytest.raises(jwt.InvalidTokenError):
        decode_access_token(token, settings)


def test_refresh_tokens_are_random_and_hash_deterministically() -> None:
    first, second = generate_refresh_token(), generate_refresh_token()

    assert first != second
    assert len(first) >= 64
    assert hash_refresh_token(first) == hash_refresh_token(first)
    assert hash_refresh_token(first) != hash_refresh_token(second)
    assert len(hash_refresh_token(first)) == 64
