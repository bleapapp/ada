"""Base connector class for external service integrations."""

from __future__ import annotations

from typing import Any

import httpx
import structlog

logger = structlog.get_logger()


class BaseConnector:
    """Base class for all httpx-based API connectors."""

    def __init__(
        self,
        base_url: str,
        token: str,
        headers: dict[str, str] | None = None,
    ) -> None:
        default_headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        }
        if headers:
            default_headers.update(headers)

        self._client = httpx.AsyncClient(
            base_url=base_url,
            headers=default_headers,
            timeout=30.0,
        )

    async def _get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        response = await self._client.get(path, params=params)
        response.raise_for_status()
        return response.json()

    async def _post(self, path: str, json: dict[str, Any] | None = None) -> Any:
        response = await self._client.post(path, json=json)
        response.raise_for_status()
        return response.json()

    async def close(self) -> None:
        await self._client.aclose()
