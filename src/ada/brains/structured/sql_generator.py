"""Text-to-SQL pipeline using LLM."""

from __future__ import annotations

import re

import structlog

from ada.llm.client import completion

logger = structlog.get_logger()

SYSTEM_PROMPT = """\
You are a SQL expert. Given a natural language question and database schema context, \
generate a safe, read-only SQL query to answer the question.

Rules:
1. ONLY generate SELECT statements. Never generate INSERT, UPDATE, DELETE, DROP, \
ALTER, CREATE, TRUNCATE, or any DDL/DML.
2. Always include a WHERE clause for tenant_id = {{tenant_id}} if the table has a \
tenant_id column.
3. Use column aliases to make results readable.
4. Limit results to 100 rows unless the user explicitly asks for more.
5. Return ONLY the SQL query, wrapped in ```sql ... ``` code block. No explanation.
"""


def _extract_sql(response: str) -> str | None:
    """Extract SQL from a markdown code block."""
    match = re.search(r"```sql\s*\n?(.*?)```", response, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    # Fallback: try to find a SELECT statement directly
    match = re.search(r"(SELECT\s.+)", response, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return None


def _validate_read_only(sql: str) -> bool:
    """Ensure the SQL is a read-only SELECT statement."""
    normalized = sql.strip().upper()
    forbidden = [
        "INSERT", "UPDATE", "DELETE", "DROP", "ALTER",
        "CREATE", "TRUNCATE", "GRANT", "REVOKE", "EXEC",
    ]
    # Check that it starts with SELECT or WITH (for CTEs)
    if not (normalized.startswith("SELECT") or normalized.startswith("WITH")):
        return False
    return all(not re.search(rf"\b{keyword}\b", normalized) for keyword in forbidden)


async def generate_sql(
    question: str,
    schema_context: str,
    tenant_id: str,
    model: str = "gpt-4o-mini",
) -> str | None:
    """Generate a read-only SQL query from a natural language question.

    Returns the SQL string or None if generation/validation fails.
    """
    system = SYSTEM_PROMPT.replace("{{tenant_id}}", tenant_id)
    messages = [
        {"role": "system", "content": system},
        {
            "role": "user",
            "content": f"Schema:\n{schema_context}\n\nQuestion: {question}",
        },
    ]

    response = await completion(messages=messages, model=model, temperature=0.0)
    sql = _extract_sql(response)

    if sql is None:
        logger.warning("sql_generation_failed", question=question, response=response)
        return None

    if not _validate_read_only(sql):
        logger.error("sql_not_read_only", sql=sql, question=question)
        return None

    logger.info("sql_generated", question=question, sql=sql)
    return sql
