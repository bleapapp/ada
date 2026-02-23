"""Intent router that classifies user queries as structured (SQL) or unstructured (RAG)."""

from enum import StrEnum

from ada.llm.client import completion

CLASSIFICATION_PROMPT = """\
You are an intent classifier for a backoffice intelligence system.
Classify the user's query into one of two categories:

- STRUCTURED: Questions that can be answered by querying databases (SQL). \
These involve metrics, counts, aggregations, specific records, financial data, \
user statistics, or any quantitative data from structured tables.

- UNSTRUCTURED: Questions that require searching through documents, wikis, \
tickets, conversations, or code. These involve processes, documentation, \
how-to questions, historical context, or qualitative information.

Respond with ONLY the word STRUCTURED or UNSTRUCTURED, nothing else."""


class Intent(StrEnum):
    STRUCTURED = "structured"
    UNSTRUCTURED = "unstructured"


async def classify_intent(query: str, model: str = "gpt-4o-mini") -> Intent:
    """Classify a user query as structured (SQL-answerable) or unstructured (RAG)."""
    messages = [
        {"role": "system", "content": CLASSIFICATION_PROMPT},
        {"role": "user", "content": query},
    ]
    response = await completion(messages=messages, model=model, temperature=0.0, max_tokens=20)
    normalized = response.strip().upper()
    if normalized.startswith("UNSTRUCTURED"):
        return Intent.UNSTRUCTURED
    if normalized.startswith("STRUCTURED"):
        return Intent.STRUCTURED
    return Intent.UNSTRUCTURED
