"""Summarize SQL query results into natural language."""

from __future__ import annotations

import json
from typing import Any

from ada.llm.client import completion

SUMMARIZE_PROMPT = """\
You are a helpful data analyst. Given the original question and query results, \
provide a clear, concise summary in natural language.

- If the results are empty, say so clearly.
- If there are numbers, present them formatted nicely.
- Keep the summary brief (2-4 sentences).
- Do not include raw SQL or JSON in your response.
"""


async def summarize_results(
    question: str,
    results: list[dict[str, Any]],
    sql: str,
    model: str = "gpt-4o-mini",
) -> str:
    """Summarize SQL query results into a natural language answer."""
    if not results:
        return "The query returned no results."

    # Truncate large result sets for the LLM context
    display_results = results[:20]
    results_text = json.dumps(display_results, indent=2, default=str)
    if len(results) > 20:
        results_text += f"\n... and {len(results) - 20} more rows"

    messages = [
        {"role": "system", "content": SUMMARIZE_PROMPT},
        {
            "role": "user",
            "content": (
                f"Question: {question}\n\n"
                f"SQL executed: {sql}\n\n"
                f"Results ({len(results)} rows):\n{results_text}"
            ),
        },
    ]

    return await completion(messages=messages, model=model, temperature=0.2)
