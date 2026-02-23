"""Tests for integration connectors and webhook endpoints."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from ada.connectors.tasks import (
    _extract_confluence_document,
    _extract_github_document,
    _extract_jira_document,
    _extract_slack_document,
)
from ada.main import app

# --- Document extraction tests ---


class TestGitHubExtractor:
    def test_push_event(self) -> None:
        payload = {
            "ref": "refs/heads/main",
            "commits": [{"message": "fix: bug"}, {"message": "feat: new"}],
        }
        doc = _extract_github_document("push", payload)
        assert doc is not None
        assert doc["source"] == "github"
        assert "fix: bug" in doc["text"]

    def test_push_no_commits(self) -> None:
        assert _extract_github_document("push", {"commits": []}) is None

    def test_pull_request_event(self) -> None:
        payload = {"pull_request": {"title": "Add feature", "body": "Details here"}}
        doc = _extract_github_document("pull_request", payload)
        assert doc is not None
        assert doc["title"] == "Add feature"

    def test_issues_event(self) -> None:
        payload = {"issue": {"title": "Bug report", "body": "Steps to repro"}}
        doc = _extract_github_document("issues", payload)
        assert doc is not None
        assert doc["title"] == "Bug report"

    def test_unknown_event(self) -> None:
        assert _extract_github_document("unknown", {}) is None


class TestJiraExtractor:
    def test_issue_event(self) -> None:
        payload = {
            "issue": {
                "fields": {
                    "summary": "Task title",
                    "description": "Task description",
                }
            }
        }
        doc = _extract_jira_document("jira:issue_created", payload)
        assert doc is not None
        assert doc["title"] == "Task title"
        assert doc["source"] == "jira"


class TestConfluenceExtractor:
    def test_page_event(self) -> None:
        payload = {
            "page": {
                "title": "How to deploy",
                "body": {"storage": {"value": "<p>Deploy steps</p>"}},
            }
        }
        doc = _extract_confluence_document("page_updated", payload)
        assert doc is not None
        assert doc["title"] == "How to deploy"


class TestSlackExtractor:
    def test_message_event(self) -> None:
        payload = {
            "event": {"type": "message", "text": "Hello team", "channel": "C123"}
        }
        doc = _extract_slack_document("message", payload)
        assert doc is not None
        assert doc["text"] == "Hello team"

    def test_empty_message(self) -> None:
        payload = {"event": {"type": "message", "text": "", "channel": "C123"}}
        assert _extract_slack_document("message", payload) is None


# --- Webhook endpoint tests ---


@pytest.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


class TestWebhookEndpoints:
    @patch("ada.api.webhooks.index_document", new_callable=AsyncMock)
    async def test_github_webhook(
        self, _mock_task: AsyncMock, client: AsyncClient
    ) -> None:
        response = await client.post(
            "/webhooks/github",
            json={"commits": [{"message": "test"}]},
            headers={"X-GitHub-Event": "push"},
        )
        assert response.status_code == 200
        assert response.json() == {"status": "accepted"}

    @patch("ada.api.webhooks.index_document", new_callable=AsyncMock)
    async def test_jira_webhook(
        self, _mock_task: AsyncMock, client: AsyncClient
    ) -> None:
        response = await client.post(
            "/webhooks/jira",
            json={"webhookEvent": "jira:issue_created", "issue": {}},
        )
        assert response.status_code == 200

    @patch("ada.api.webhooks.index_document", new_callable=AsyncMock)
    async def test_slack_url_verification(
        self, _mock_task: AsyncMock, client: AsyncClient
    ) -> None:
        response = await client.post(
            "/webhooks/slack",
            json={"type": "url_verification", "challenge": "abc123"},
        )
        assert response.status_code == 200
        assert response.json()["challenge"] == "abc123"

    @patch("ada.api.webhooks.index_document", new_callable=AsyncMock)
    async def test_confluence_webhook(
        self, _mock_task: AsyncMock, client: AsyncClient
    ) -> None:
        response = await client.post(
            "/webhooks/confluence",
            json={"eventType": "page_updated", "page": {}},
        )
        assert response.status_code == 200
