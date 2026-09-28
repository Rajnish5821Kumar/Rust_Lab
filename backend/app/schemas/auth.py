from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.user import PASSWORD_MAX_LENGTH, NormalizedEmail


class LoginRequest(BaseModel):
    email: NormalizedEmail
    password: str = Field(max_length=PASSWORD_MAX_LENGTH)


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=1, max_length=256)


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: Literal["bearer"] = "bearer"  # noqa: S105
    expires_in: int = Field(description="Access token lifetime in seconds")
