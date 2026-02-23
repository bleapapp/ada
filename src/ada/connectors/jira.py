"""Jira API connector."""

from __future__ import annotations

from typing import Any

from ada.connectors.base import BaseConnector


class JiraConnector(BaseConnector):
    """Client for Jira REST API."""

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

    async def search_issues(
        self, jql: str, max_results: int = 50
    ) -> dict[str, Any]:
        return await self._get(
            "/rest/api/3/search",
            params={"jql": jql, "maxResults": max_results},
        )

    async def get_issue(self, issue_key: str) -> dict[str, Any]:
        return await self._get(f"/rest/api/3/issue/{issue_key}")

    async def get_issue_comments(self, issue_key: str) -> dict[str, Any]:
        return await self._get(f"/rest/api/3/issue/{issue_key}/comment")
