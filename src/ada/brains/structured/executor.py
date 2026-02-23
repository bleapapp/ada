"""Read-only SQL query executor for Postgres and BigQuery."""

from __future__ import annotations

from typing import Any

import structlog
from google.cloud import bigquery
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

logger = structlog.get_logger()


class PostgresExecutor:
    """Execute read-only queries against Postgres via SQLAlchemy async."""

    def __init__(self, database_url: str) -> None:
        self._engine: AsyncEngine = create_async_engine(
            database_url,
            pool_size=5,
            max_overflow=2,
            pool_pre_ping=True,
        )

    async def execute(self, sql: str) -> list[dict[str, Any]]:
        """Execute a read-only SQL query and return results as dicts."""
        async with self._engine.connect() as conn:
            # Force read-only transaction
            await conn.execute(text("SET TRANSACTION READ ONLY"))
            result = await conn.execute(text(sql))
            columns = list(result.keys())
            rows = result.fetchall()
            return [dict(zip(columns, row, strict=False)) for row in rows]

    async def close(self) -> None:
        await self._engine.dispose()


class BigQueryExecutor:
    """Execute read-only queries against BigQuery."""

    def __init__(self, project: str | None = None) -> None:
        self._client = bigquery.Client(project=project)

    def execute(self, sql: str) -> list[dict[str, Any]]:
        """Execute a BigQuery SQL query and return results as dicts."""
        job = self._client.query(sql)
        rows = job.result()
        return [dict(row) for row in rows]

    def close(self) -> None:
        self._client.close()
