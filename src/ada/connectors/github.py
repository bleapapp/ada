"""GitHub API connector."""

from __future__ import annotations

from typing import Any

from ada.connectors.base import BaseConnector


class GitHubConnector(BaseConnector):
    """Client for GitHub REST API."""

    def __init__(self, token: str) -> None:
        super().__init__(
            base_url="https://api.github.com",
            token=token,
            headers={"X-GitHub-Api-Version": "2022-11-28"},
        )

    async def get_repo(self, owner: str, repo: str) -> dict[str, Any]:
        return await self._get(f"/repos/{owner}/{repo}")

    async def list_issues(
        self, owner: str, repo: str, state: str = "open", per_page: int = 30
    ) -> list[dict[str, Any]]:
        return await self._get(
            f"/repos/{owner}/{repo}/issues",
            params={"state": state, "per_page": per_page},
        )

    async def get_pull_request(
        self, owner: str, repo: str, pr_number: int
    ) -> dict[str, Any]:
        return await self._get(f"/repos/{owner}/{repo}/pulls/{pr_number}")

    async def list_commits(
        self, owner: str, repo: str, sha: str = "main", per_page: int = 30
    ) -> list[dict[str, Any]]:
        return await self._get(
            f"/repos/{owner}/{repo}/commits",
            params={"sha": sha, "per_page": per_page},
        )
