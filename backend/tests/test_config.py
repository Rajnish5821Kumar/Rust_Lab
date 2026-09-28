import pytest
from pydantic import ValidationError

from app.core.config import Settings

BASE = {"database_url": "sqlite+aiosqlite:///:memory:", "jwt_secret": "s" * 32}


def make_settings(**overrides: object) -> Settings:
    return Settings(_env_file=None, **{**BASE, **overrides})  # type: ignore[arg-type]


def test_short_jwt_secret_is_rejected() -> None:
    with pytest.raises(ValidationError, match="jwt_secret"):
        make_settings(jwt_secret="too-short")


def test_database_url_is_required(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)

    with pytest.raises(ValidationError, match="database_url"):
        Settings(_env_file=None, jwt_secret="s" * 32)


def test_cors_origins_accept_comma_separated_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CORS_ORIGINS", "http://a.test, http://b.test ,")

    assert make_settings().cors_origins == ["http://a.test", "http://b.test"]


def test_bootstrap_admin_email_is_normalized() -> None:
    assert make_settings(bootstrap_admin_email="  Admin@Example.COM ").bootstrap_admin_email == (
        "admin@example.com"
    )
    assert make_settings(bootstrap_admin_email="").bootstrap_admin_email is None


def test_jwt_secret_is_not_exposed_in_repr() -> None:
    settings = make_settings(jwt_secret="super-secret-value-that-is-long-enough")

    assert "super-secret-value" not in repr(settings)
