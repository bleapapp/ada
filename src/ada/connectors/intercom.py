"""Intercom API connector."""

from __future__ import annotations

from typing import Any

from ada.connectors.base import BaseConnector


class IntercomConnector(BaseConnector):
    """Client for Intercom REST API."""

    def __init__(self, token: str) -> None:
        super().__init__(
            base_url="https://api.intercom.io",
            token=token,
            headers={"Intercom-Version": "2.11"},
        )

    async def search_conversations(
        self, query: str
    ) -> dict[str, Any]:
        return await self._post(
            "/conversations/search",
            json={
                "query": {
                    "operator": "AND",
                    "value": [
                        {
                            "field": "source.body",
                            "operator": "~",
                            "value": query,
                        }
                    ],
                }
            },
        )

    async def get_conversation(self, conversation_id: str) -> dict[str, Any]:
        return await self._get(f"/conversations/{conversation_id}")

    async def list_articles(self) -> dict[str, Any]:
        return await self._get("/articles")
