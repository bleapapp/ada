"""Schema metadata store for database tables.

Provides table/column descriptions used as context for the Text-to-SQL pipeline.
Schema definitions are loaded from YAML files to keep them version-controlled
and reviewable separately from code.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pathlib import Path

import yaml
from pydantic import BaseModel


class ColumnSchema(BaseModel):
    name: str
    type: str
    description: str = ""


class TableSchema(BaseModel):
    name: str
    database: str  # "bigquery" or "postgres"
    dataset: str = ""  # BigQuery dataset or Postgres schema
    description: str = ""
    columns: list[ColumnSchema] = []


class SchemaStore:
    """In-memory store of table schemas for Text-to-SQL context."""

    def __init__(self) -> None:
        self._tables: dict[str, TableSchema] = {}

    def register(self, table: TableSchema) -> None:
        if table.dataset:
            key = f"{table.database}.{table.dataset}.{table.name}"
        else:
            key = f"{table.database}.{table.name}"
        self._tables[key] = table

    def get_table(self, name: str) -> TableSchema | None:
        """Look up a table by full key or by table name."""
        if name in self._tables:
            return self._tables[name]
        for table in self._tables.values():
            if table.name == name:
                return table
        return None

    def get_all(self, database: str | None = None) -> list[TableSchema]:
        tables = list(self._tables.values())
        if database:
            tables = [t for t in tables if t.database == database]
        return tables

    def get_context_prompt(self, database: str | None = None) -> str:
        """Generate a text description of all schemas for LLM context."""
        tables = self.get_all(database)
        if not tables:
            return "No schema information available."

        lines: list[str] = []
        for table in tables:
            header = f"Table: {table.name}"
            if table.dataset:
                header += f" (dataset: {table.dataset})"
            header += f" [{table.database}]"
            lines.append(header)
            if table.description:
                lines.append(f"  Description: {table.description}")
            for col in table.columns:
                col_line = f"  - {col.name} ({col.type})"
                if col.description:
                    col_line += f": {col.description}"
                lines.append(col_line)
            lines.append("")
        return "\n".join(lines)

    def load_from_yaml(self, path: Path) -> None:
        """Load table schemas from a YAML file."""
        data: Any = yaml.safe_load(path.read_text())
        if not isinstance(data, dict) or "tables" not in data:
            return
        for table_data in data["tables"]:
            self.register(TableSchema(**table_data))


# Global singleton
schema_store = SchemaStore()
