# Agent Guidelines for ADA

## Workflow
- **Opus 4.6**: Design, planning, architecture decisions
- **Sonnet 4.6**: Implementation, code generation, tests
- Create sequential, reviewable PRs pushed to `bleapapp/ada`
- Each PR should be independently mergeable

## Code Style
- Python 3.12+ with type hints on all function signatures
- Use `ruff` for linting and formatting (configured in `pyproject.toml`)
- Prefer `async/await` for I/O-bound operations
- Use Pydantic v2 models for all data validation
- Structured logging via `structlog`

## Testing
- Every module gets a corresponding test file in `tests/`
- Use `pytest` + `pytest-asyncio` + `httpx` for API tests
- Mock external services; never call real APIs in tests
- Aim for meaningful coverage, not 100% line coverage

## PR Checklist
1. `uv sync` succeeds
2. `uv run pytest` passes
3. `uv run ruff check src/ tests/` is clean
4. Commit messages are clear and conventional

## Security
- Never execute write queries against production databases
- Always enforce tenant isolation in queries
- Validate JWTs on every request (except health checks)
- Never log secrets, tokens, or PII
- All external API keys come from environment variables
