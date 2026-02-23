"""Tests for the structured data brain (Text-to-SQL pipeline)."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, patch

import pytest

from ada.brains.structured.schema_store import ColumnSchema, SchemaStore, TableSchema
from ada.brains.structured.sql_generator import (
    _extract_sql,
    _validate_read_only,
    generate_sql,
)
from ada.brains.structured.summarizer import summarize_results

if TYPE_CHECKING:
    from pathlib import Path


# --- Schema Store tests ---


class TestSchemaStore:
    def setup_method(self) -> None:
        self.store = SchemaStore()
        self.table = TableSchema(
            name="users",
            database="postgres",
            dataset="public",
            description="User accounts table",
            columns=[
                ColumnSchema(name="id", type="uuid", description="Primary key"),
                ColumnSchema(name="email", type="varchar", description="User email"),
                ColumnSchema(name="tenant_id", type="uuid", description="Tenant FK"),
            ],
        )

    def test_register_and_get(self) -> None:
        self.store.register(self.table)
        result = self.store.get_table("postgres.public.users")
        assert result is not None
        assert result.name == "users"

    def test_get_by_name(self) -> None:
        self.store.register(self.table)
        result = self.store.get_table("users")
        assert result is not None

    def test_get_nonexistent(self) -> None:
        assert self.store.get_table("nonexistent") is None

    def test_get_all(self) -> None:
        self.store.register(self.table)
        bq_table = TableSchema(name="events", database="bigquery", dataset="analytics")
        self.store.register(bq_table)
        assert len(self.store.get_all()) == 2
        assert len(self.store.get_all(database="postgres")) == 1

    def test_context_prompt(self) -> None:
        self.store.register(self.table)
        prompt = self.store.get_context_prompt()
        assert "users" in prompt
        assert "email" in prompt
        assert "tenant_id" in prompt

    def test_context_prompt_empty(self) -> None:
        assert self.store.get_context_prompt() == "No schema information available."

    def test_load_from_yaml(self, tmp_path: Path) -> None:
        yaml_content = """
tables:
  - name: orders
    database: postgres
    dataset: public
    description: Customer orders
    columns:
      - name: id
        type: uuid
        description: Order ID
      - name: total
        type: decimal
        description: Order total
"""
        yaml_file = tmp_path / "schema.yaml"
        yaml_file.write_text(yaml_content)
        self.store.load_from_yaml(yaml_file)
        table = self.store.get_table("orders")
        assert table is not None
        assert len(table.columns) == 2


# --- SQL Generator tests ---


class TestExtractSql:
    def test_extract_from_code_block(self) -> None:
        response = '```sql\nSELECT * FROM users;\n```'
        assert _extract_sql(response) == "SELECT * FROM users;"

    def test_extract_from_raw_select(self) -> None:
        response = "SELECT count(*) FROM orders WHERE tenant_id = 'abc'"
        result = _extract_sql(response)
        assert result is not None
        assert result.startswith("SELECT")

    def test_extract_returns_none(self) -> None:
        assert _extract_sql("I don't know how to answer that.") is None


class TestValidateReadOnly:
    def test_select_is_valid(self) -> None:
        assert _validate_read_only("SELECT * FROM users") is True

    def test_with_cte_is_valid(self) -> None:
        sql = "WITH active AS (SELECT * FROM users WHERE active) SELECT * FROM active"
        assert _validate_read_only(sql) is True

    def test_insert_is_invalid(self) -> None:
        assert _validate_read_only("INSERT INTO users VALUES (1)") is False

    def test_delete_is_invalid(self) -> None:
        assert _validate_read_only("DELETE FROM users") is False

    def test_drop_is_invalid(self) -> None:
        assert _validate_read_only("DROP TABLE users") is False

    def test_update_is_invalid(self) -> None:
        assert _validate_read_only("UPDATE users SET name = 'x'") is False

    def test_select_with_embedded_delete_is_invalid(self) -> None:
        sql = "SELECT * FROM users; DELETE FROM users"
        assert _validate_read_only(sql) is False


class TestGenerateSql:
    @pytest.fixture
    def mock_completion(self):
        with patch(
            "ada.brains.structured.sql_generator.completion",
            new_callable=AsyncMock,
        ) as mock:
            yield mock

    async def test_generates_valid_sql(self, mock_completion: AsyncMock) -> None:
        mock_completion.return_value = (
            "```sql\nSELECT count(*) as user_count FROM users "
            "WHERE tenant_id = 'tenant-123'\n```"
        )
        result = await generate_sql(
            question="How many users?",
            schema_context="Table: users (id, email, tenant_id)",
            tenant_id="tenant-123",
        )
        assert result is not None
        assert "SELECT" in result

    async def test_rejects_non_read_only(self, mock_completion: AsyncMock) -> None:
        mock_completion.return_value = "```sql\nDELETE FROM users\n```"
        result = await generate_sql(
            question="Delete all users",
            schema_context="Table: users",
            tenant_id="t1",
        )
        assert result is None

    async def test_returns_none_on_garbage(self, mock_completion: AsyncMock) -> None:
        mock_completion.return_value = "I cannot help with that."
        result = await generate_sql(
            question="Something weird",
            schema_context="Table: users",
            tenant_id="t1",
        )
        assert result is None


# --- Summarizer tests ---


class TestSummarizer:
    @pytest.fixture
    def mock_completion(self):
        with patch(
            "ada.brains.structured.summarizer.completion",
            new_callable=AsyncMock,
        ) as mock:
            yield mock

    async def test_summarize_empty_results(self, mock_completion: AsyncMock) -> None:
        result = await summarize_results(
            question="How many?", results=[], sql="SELECT count(*) FROM users"
        )
        assert result == "The query returned no results."
        mock_completion.assert_not_called()

    async def test_summarize_with_results(self, mock_completion: AsyncMock) -> None:
        mock_completion.return_value = "There are 42 active users."
        result = await summarize_results(
            question="How many active users?",
            results=[{"count": 42}],
            sql="SELECT count(*) FROM users WHERE active = true",
        )
        assert result == "There are 42 active users."
