import re
from datetime import datetime
from typing import Annotated

from pydantic import AfterValidator, BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.core.config import RoleName
from app.core.time import ensure_aware

_USERNAME_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]{2,63}$")

PASSWORD_MIN_LENGTH = 12
PASSWORD_MAX_LENGTH = 128


def _normalize_username(value: str) -> str:
    value = value.strip().lower()
    if not _USERNAME_RE.fullmatch(value):
        raise ValueError(
            "must be 3-64 characters (letters, digits, '_', '.', '-') "
            "and start with a letter or digit"
        )
    return value


def _normalize_email(value: str) -> str:
    return value.strip().lower()


Username = Annotated[str, AfterValidator(_normalize_username)]
NormalizedEmail = Annotated[EmailStr, AfterValidator(_normalize_email)]
Password = Annotated[str, Field(min_length=PASSWORD_MIN_LENGTH, max_length=PASSWORD_MAX_LENGTH)]


class UserCreate(BaseModel):
    email: NormalizedEmail
    username: Username
    password: Password
    full_name: str | None = Field(default=None, max_length=255)


class UserProfileUpdate(BaseModel):
    username: Username | None = None
    full_name: str | None = Field(default=None, max_length=255)


class PasswordChange(BaseModel):
    current_password: str = Field(max_length=PASSWORD_MAX_LENGTH)
    new_password: Password


class UserAdminUpdate(BaseModel):
    role: RoleName | None = None
    is_active: bool | None = None


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    username: str
    full_name: str | None
    role: RoleName
    is_active: bool
    created_at: datetime
    last_login_at: datetime | None

    @field_validator("role", mode="before")
    @classmethod
    def _role_name(cls, value: object) -> object:
        # ORM objects carry a Role instance; expose only its name.
        return getattr(value, "name", value)

    @field_validator("created_at", "last_login_at", mode="after")
    @classmethod
    def _as_utc(cls, value: datetime | None) -> datetime | None:
        # SQLite returns naive datetimes; always emit explicit UTC offsets.
        return ensure_aware(value) if value is not None else None
