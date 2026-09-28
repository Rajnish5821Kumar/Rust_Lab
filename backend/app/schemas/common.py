from typing import Any

from pydantic import BaseModel, Field


class ErrorBody(BaseModel):
    code: str = Field(examples=["not_found"])
    message: str
    details: Any = None
    request_id: str | None = None


class ErrorResponse(BaseModel):
    """Shape of every non-2xx response produced by the API."""

    error: ErrorBody


class Page[T](BaseModel):
    items: list[T]
    total: int
    limit: int
    offset: int
