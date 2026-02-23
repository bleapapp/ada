"""Slack API connector."""

from __future__ import annotations

from typing import Any

from ada.connectors.base import BaseConnector


class SlackConnector(BaseConnector):
    """Client for Slack Web API."""

    def __init__(self, token: str) -> None:
        super().__init__(
            base_url="https://slack.com/api",
            token=token,
        )

    async def list_channels(self, limit: int = 100) -> dict[str, Any]:
        return await self._get(
            "/conversations.list", params={"limit": limit}
        )

    async def get_channel_history(
        self, channel_id: str, limit: int = 100
    ) -> dict[str, Any]:
        return await self._get(
            "/conversations.history",
            params={"channel": channel_id, "limit": limit},
        )

    async def search_messages(
        self, query: str, count: int = 20
    ) -> dict[str, Any]:
        return await self._get(
            "/search.messages",
            params={"query": query, "count": count},
        )
