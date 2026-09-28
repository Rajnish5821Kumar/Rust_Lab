from typing import Any

import httpx


class ApiError(Exception):
    """Raised when the DevVault API is unreachable or returns an error."""


class DevVaultClient:
    def __init__(
        self,
        base_url: str,
        *,
        timeout: float = 5.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self._client = httpx.Client(base_url=base_url, timeout=timeout, transport=transport)

    def __enter__(self) -> "DevVaultClient":
        return self

    def __exit__(self, *_: object) -> None:
        self._client.close()

    def health(self) -> dict[str, Any]:
        return self._get("/api/health")

    def readiness(self) -> dict[str, Any]:
        # 503 is a meaningful answer here (a dependency is down), not a transport failure.
        return self._get("/api/health/ready", accept={200, 503})

    def _get(self, path: str, *, accept: set[int] | None = None) -> dict[str, Any]:
        accept = accept or {200}
        try:
            response = self._client.get(path)
        except httpx.HTTPError as exc:
            raise ApiError(f"Could not reach {self._client.base_url}: {exc}") from exc
        if response.status_code not in accept:
            raise ApiError(f"{path} returned HTTP {response.status_code}")
        try:
            data = response.json()
        except ValueError as exc:
            raise ApiError(f"{path} did not return JSON") from exc
        if not isinstance(data, dict):
            raise ApiError(f"{path} returned an unexpected payload")
        return data
