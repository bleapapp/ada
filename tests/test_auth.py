"""Tests for RBAC & Auth middleware."""

from __future__ import annotations

from unittest.mock import patch

import jwt as pyjwt
import pytest
from httpx import ASGITransport, AsyncClient

from ada.auth.jwt import TokenPayload, decode_token
from ada.auth.middleware import _is_public_path
from ada.main import app

TEST_SECRET = "test-secret-key"


def _make_token(
    sub: str = "user-1",
    tenant_id: str = "tenant-1",
    roles: list[str] | None = None,
    email: str = "user@example.com",
    secret: str = TEST_SECRET,
) -> str:
    payload = {
        "sub": sub,
        "tenant_id": tenant_id,
        "roles": roles or ["user"],
        "email": email,
    }
    return pyjwt.encode(payload, secret, algorithm="HS256")


# --- JWT decode tests ---


class TestDecodeToken:
    @patch("ada.auth.jwt.settings")
    def test_decode_valid_token(self, mock_settings: object) -> None:
        mock_settings.jwt_secret = TEST_SECRET  # type: ignore[attr-defined]
        mock_settings.jwt_algorithm = "HS256"  # type: ignore[attr-defined]
        token = _make_token()
        result = decode_token(token)
        assert isinstance(result, TokenPayload)
        assert result.sub == "user-1"
        assert result.tenant_id == "tenant-1"
        assert result.roles == ["user"]
        assert result.email == "user@example.com"

    @patch("ada.auth.jwt.settings")
    def test_decode_invalid_token(self, mock_settings: object) -> None:
        mock_settings.jwt_secret = TEST_SECRET  # type: ignore[attr-defined]
        mock_settings.jwt_algorithm = "HS256"  # type: ignore[attr-defined]
        with pytest.raises(pyjwt.InvalidTokenError):
            decode_token("invalid.token.here")

    @patch("ada.auth.jwt.settings")
    def test_decode_wrong_secret(self, mock_settings: object) -> None:
        mock_settings.jwt_secret = "wrong-secret"  # type: ignore[attr-defined]
        mock_settings.jwt_algorithm = "HS256"  # type: ignore[attr-defined]
        token = _make_token(secret=TEST_SECRET)
        with pytest.raises(pyjwt.InvalidTokenError):
            decode_token(token)

    @patch("ada.auth.jwt.settings")
    def test_decode_without_secret(self, mock_settings: object) -> None:
        mock_settings.jwt_secret = ""  # type: ignore[attr-defined]
        mock_settings.jwt_algorithm = "HS256"  # type: ignore[attr-defined]
        token = _make_token()
        result = decode_token(token)
        assert result.sub == "user-1"


# --- Public path tests ---


class TestPublicPaths:
    def test_health_is_public(self) -> None:
        assert _is_public_path("/health") is True

    def test_docs_is_public(self) -> None:
        assert _is_public_path("/docs") is True

    def test_webhooks_are_public(self) -> None:
        assert _is_public_path("/webhooks/github") is True
        assert _is_public_path("/webhooks/jira") is True

    def test_api_paths_not_public(self) -> None:
        assert _is_public_path("/api/query") is False
        assert _is_public_path("/chat") is False


# --- Middleware integration tests ---


@pytest.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


class TestAuthMiddleware:
    async def test_health_no_auth_required(self, client: AsyncClient) -> None:
        response = await client.get("/health")
        assert response.status_code == 200

    async def test_missing_auth_header(self, client: AsyncClient) -> None:
        response = await client.get("/nonexistent-protected")
        assert response.status_code == 401

    async def test_invalid_auth_header(self, client: AsyncClient) -> None:
        response = await client.get(
            "/nonexistent-protected",
            headers={"Authorization": "Basic abc"},
        )
        assert response.status_code == 401

    @patch("ada.auth.middleware.decode_token")
    async def test_invalid_token(
        self, mock_decode: object, client: AsyncClient
    ) -> None:
        mock_decode.side_effect = pyjwt.InvalidTokenError("expired")  # type: ignore[attr-defined]
        response = await client.get(
            "/nonexistent-protected",
            headers={"Authorization": "Bearer bad-token"},
        )
        assert response.status_code == 401

    @patch("ada.auth.middleware.decode_token")
    async def test_missing_tenant_id(
        self, mock_decode: object, client: AsyncClient
    ) -> None:
        mock_decode.return_value = TokenPayload(  # type: ignore[attr-defined]
            sub="user-1", tenant_id="", roles=["user"]
        )
        response = await client.get(
            "/nonexistent-protected",
            headers={"Authorization": "Bearer some-token"},
        )
        assert response.status_code == 403

    async def test_webhooks_no_auth_required(self, client: AsyncClient) -> None:
        response = await client.post(
            "/webhooks/github",
            json={},
            headers={"X-GitHub-Event": "ping"},
        )
        assert response.status_code == 200
