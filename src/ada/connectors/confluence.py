"""Confluence API connector."""

from __future__ import annotations

from typing import Any

from ada.connectors.base import BaseConnector


class ConfluenceConnector(BaseConnector):
    """Client for Confluence REST API."""

    def __init__(self, base_url: str, email: str, api_token: str) -> None:
        import base64

        credentials = base64.b64encode(f"{email}:{api_token}".encode()).decode()
        super().__init__(
            base_url=base_url.rstrip("/"),
            token="",
            headers={
                "Authorization": f"Basic {credentials}",
            },
        )

    async def search(
        self, cql: str, limit: int = 25
    ) -> dict[str, Any]:
        return await self._get(
            "/rest/api/content/search",
            params={"cql": cql, "limit": limit},
        )

    async def get_page(self, page_id: str) -> dict[str, Any]:
        return await self._get(
            f"/rest/api/content/{page_id}",
            params={"expand": "body.storage,version"},
        )

    async def get_page_children(
        self, page_id: str, limit: int = 25
    ) -> dict[str, Any]:
        return await self._get(
            f"/rest/api/content/{page_id}/child/page",
            params={"limit": limit},
        )
