"""Background indexing tasks for processing webhook events."""

from __future__ import annotations

from typing import Any

import structlog

logger = structlog.get_logger()


async def index_document(
    source: str,
    event_type: str,
    payload: dict[str, Any],
) -> None:
    """Process a webhook event and index the document for RAG.

    This is called as a FastAPI background task. In a production setup,
    this would be replaced by or delegated to a proper task queue (Celery/ARQ).
    """
    logger.info(
        "indexing_document",
        source=source,
        event_type=event_type,
    )

    # Extract document content based on source
    document = _extract_document(source, event_type, payload)
    if document is None:
        logger.warning("no_document_extracted", source=source, event_type=event_type)
        return

    # TODO: Chunk, embed, and upsert to Qdrant
    # This will be wired up when the full pipeline is integrated
    logger.info(
        "document_indexed",
        source=source,
        title=document.get("title", "untitled"),
    )


def _extract_document(
    source: str,
    event_type: str,
    payload: dict[str, Any],
) -> dict[str, Any] | None:
    """Extract a document from a webhook payload based on source type."""
    extractors = {
        "github": _extract_github_document,
        "jira": _extract_jira_document,
        "confluence": _extract_confluence_document,
        "slack": _extract_slack_document,
    }
    extractor = extractors.get(source)
    if extractor is None:
        return None
    return extractor(event_type, payload)


def _extract_github_document(
    event_type: str, payload: dict[str, Any]
) -> dict[str, Any] | None:
    if event_type == "push":
        commits = payload.get("commits", [])
        if not commits:
            return None
        texts = [f"{c.get('message', '')}" for c in commits]
        return {
            "title": f"Push to {payload.get('ref', 'unknown')}",
            "text": "\n".join(texts),
            "source": "github",
        }
    if event_type == "pull_request":
        pr = payload.get("pull_request", {})
        return {
            "title": pr.get("title", ""),
            "text": pr.get("body", "") or "",
            "source": "github",
        }
    if event_type == "issues":
        issue = payload.get("issue", {})
        return {
            "title": issue.get("title", ""),
            "text": issue.get("body", "") or "",
            "source": "github",
        }
    return None


def _extract_jira_document(
    event_type: str, payload: dict[str, Any]
) -> dict[str, Any] | None:
    issue = payload.get("issue", {})
    fields = issue.get("fields", {})
    return {
        "title": fields.get("summary", ""),
        "text": fields.get("description", "") or "",
        "source": "jira",
    }


def _extract_confluence_document(
    _event_type: str, payload: dict[str, Any]
) -> dict[str, Any] | None:
    page = payload.get("page", {})
    return {
        "title": page.get("title", ""),
        "text": page.get("body", {}).get("storage", {}).get("value", ""),
        "source": "confluence",
    }


def _extract_slack_document(
    _event_type: str, payload: dict[str, Any]
) -> dict[str, Any] | None:
    event = payload.get("event", {})
    text = event.get("text", "")
    if not text:
        return None
    return {
        "title": f"Slack message in {event.get('channel', 'unknown')}",
        "text": text,
        "source": "slack",
    }
