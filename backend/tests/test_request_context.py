import json
import logging

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.core.logging import JsonFormatter, RequestIdFilter, request_id_var


async def test_generates_request_id_when_absent(client: AsyncClient) -> None:
    response = await client.get("/api/health")

    assert len(response.headers["X-Request-ID"]) == 32


async def test_propagates_valid_incoming_request_id(client: AsyncClient) -> None:
    response = await client.get("/api/health", headers={"X-Request-ID": "trace-abc.123"})

    assert response.headers["X-Request-ID"] == "trace-abc.123"


async def test_replaces_unsafe_incoming_request_id(client: AsyncClient) -> None:
    response = await client.get("/api/health", headers={"X-Request-ID": "bad id\twith spaces"})

    assert response.headers["X-Request-ID"] != "bad id\twith spaces"
    assert len(response.headers["X-Request-ID"]) == 32


async def test_unknown_route_uses_error_envelope(client: AsyncClient) -> None:
    response = await client.get("/api/does-not-exist")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"
    assert response.json()["error"]["request_id"] == response.headers["X-Request-ID"]


async def test_unhandled_exception_returns_json_500_without_leaking_details(app: FastAPI) -> None:
    @app.get("/api/_boom")
    async def boom() -> None:
        raise RuntimeError("secret internal detail")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        response = await c.get("/api/_boom", headers={"X-Request-ID": "req-500"})

    assert response.status_code == 500
    assert response.json() == {
        "error": {
            "code": "internal_error",
            "message": "An unexpected error occurred",
            "details": None,
            "request_id": "req-500",
        }
    }
    assert "secret internal detail" not in response.text


def test_json_formatter_includes_request_id_and_extras() -> None:
    record = logging.LogRecord("devvault.test", logging.INFO, __file__, 1, "hello %s", ("x",), None)
    record.duration_ms = 12.5
    token = request_id_var.set("req-42")
    try:
        RequestIdFilter().filter(record)
    finally:
        request_id_var.reset(token)

    entry = json.loads(JsonFormatter().format(record))

    assert entry["message"] == "hello x"
    assert entry["request_id"] == "req-42"
    assert entry["duration_ms"] == 12.5
    assert entry["level"] == "INFO"


@pytest.mark.parametrize("header", ["X-Request-ID", "x-request-id"])
async def test_request_id_header_is_case_insensitive(client: AsyncClient, header: str) -> None:
    response = await client.get("/api/health", headers={header: "abc"})

    assert response.headers["X-Request-ID"] == "abc"
