"""Webhook endpoints for real-time indexing from external services."""

from __future__ import annotations

from typing import Any

import structlog
from fastapi import APIRouter, BackgroundTasks, Request

from ada.connectors.tasks import index_document

logger = structlog.get_logger()

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/github")
async def github_webhook(
    request: Request, background_tasks: BackgroundTasks
) -> dict[str, str]:
    """Handle GitHub webhook events for indexing."""
    payload: dict[str, Any] = await request.json()
    event_type = request.headers.get("X-GitHub-Event", "unknown")

    logger.info("github_webhook_received", event_type=event_type)

    if event_type in ("push", "pull_request", "issues"):
        background_tasks.add_task(
            index_document,
            source="github",
            event_type=event_type,
            payload=payload,
        )

    return {"status": "accepted"}


@router.post("/jira")
async def jira_webhook(
    request: Request, background_tasks: BackgroundTasks
) -> dict[str, str]:
    """Handle Jira webhook events for indexing."""
    payload: dict[str, Any] = await request.json()
    event_type = payload.get("webhookEvent", "unknown")

    logger.info("jira_webhook_received", event_type=event_type)

    if event_type in ("jira:issue_created", "jira:issue_updated"):
        background_tasks.add_task(
            index_document,
            source="jira",
            event_type=event_type,
            payload=payload,
        )

    return {"status": "accepted"}


@router.post("/confluence")
async def confluence_webhook(
    request: Request, background_tasks: BackgroundTasks
) -> dict[str, str]:
    """Handle Confluence webhook events for indexing."""
    payload: dict[str, Any] = await request.json()
    event_type = payload.get("eventType", "unknown")

    logger.info("confluence_webhook_received", event_type=event_type)

    background_tasks.add_task(
        index_document,
        source="confluence",
        event_type=event_type,
        payload=payload,
    )

    return {"status": "accepted"}


@router.post("/slack")
async def slack_webhook(
    request: Request, background_tasks: BackgroundTasks
) -> dict[str, str]:
    """Handle Slack event subscriptions for indexing."""
    payload: dict[str, Any] = await request.json()

    # Handle Slack URL verification challenge
    if payload.get("type") == "url_verification":
        return {"challenge": payload.get("challenge", "")}

    event = payload.get("event", {})
    event_type = event.get("type", "unknown")

    logger.info("slack_webhook_received", event_type=event_type)

    if event_type in ("message", "message.channels"):
        background_tasks.add_task(
            index_document,
            source="slack",
            event_type=event_type,
            payload=payload,
        )

    return {"status": "accepted"}
