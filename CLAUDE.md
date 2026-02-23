# ADA - Autonomous Decision Agent

## Project Overview
ADA is Bleap's AI-powered internal backoffice intelligence engine. It connects to structured data (BigQuery/Postgres) and unstructured data (Confluence, Jira, Slack, GitHub, Intercom) to answer questions, write queries, and support multiple backoffice roles with strict RBAC.

## Tech Stack
- **Language**: Python 3.12+
- **Framework**: FastAPI + Uvicorn
- **Package Manager**: uv
- **LLM**: LiteLLM (model-agnostic)
- **Vector DB**: Qdrant
- **Databases**: BigQuery, Postgres (read-only query execution)
- **Auth**: JWT validation (tokens from Spring Boot)
- **Testing**: pytest
- **Linting**: ruff

## Project Structure
```
src/ada/           # Main package
  api/             # FastAPI routes
  core/            # Config, dependencies, constants
  llm/             # LiteLLM wrapper, router
  brains/          # Structured (SQL) and Unstructured (RAG) brains
  connectors/      # External service clients (GitHub, Jira, Slack, etc.)
  auth/            # JWT validation, RBAC middleware
  models/          # Pydantic models
tests/             # Test suite mirroring src structure
```

## Commands
- `uv sync` — install dependencies
- `uv run pytest` — run tests
- `uv run pytest tests/path/test_file.py::test_name` — run single test
- `uv run ruff check src/ tests/` — lint
- `uv run ruff format src/ tests/` — format
- `uv run uvicorn ada.main:app --reload` — run dev server

## Conventions
- Use `pydantic-settings` for all configuration (env vars)
- All API routes return Pydantic models
- SQL queries are always read-only with tenant filtering
- Every connector uses `httpx.AsyncClient`
- RBAC is enforced at middleware level, not per-endpoint
- Tests use pytest with `httpx.AsyncClient` (via `pytest-asyncio`)
- Imports are absolute from `ada` package root
- No `print()` — use `structlog` for logging
