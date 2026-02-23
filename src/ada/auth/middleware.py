"""RBAC middleware for FastAPI."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import jwt
import structlog
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import JSONResponse, Response

from ada.auth.jwt import decode_token

if TYPE_CHECKING:
    from fastapi import Request

logger = structlog.get_logger()

# Paths that don't require authentication
PUBLIC_PATHS = {"/health", "/docs", "/openapi.json", "/redoc"}
PUBLIC_PREFIXES = ("/webhooks/",)


class AuthMiddleware(BaseHTTPMiddleware):
    """Middleware that validates JWT tokens and enforces RBAC."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # Skip auth for public paths
        if _is_public_path(request.url.path):
            return await call_next(request)

        # Extract token from Authorization header
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=401,
                content={"detail": "Missing or invalid Authorization header"},
            )

        token = auth_header[7:]  # Strip "Bearer "

        try:
            payload = decode_token(token)
        except jwt.InvalidTokenError as e:
            logger.warning("auth_failed", error=str(e))
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid or expired token"},
            )

        if not payload.tenant_id:
            return JSONResponse(
                status_code=403,
                content={"detail": "No tenant_id in token"},
            )

        # Attach auth context to request state
        request.state.user_id = payload.sub
        request.state.tenant_id = payload.tenant_id
        request.state.roles = payload.roles
        request.state.email = payload.email

        return await call_next(request)


class RBACMiddleware(BaseHTTPMiddleware):
    """Middleware that checks role-based access for specific routes."""

    def __init__(self, app: Any, role_rules: dict[str, list[str]] | None = None) -> None:
        super().__init__(app)
        # Map of path prefix -> required roles (any of the listed roles grants access)
        self._role_rules = role_rules or {}

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # Skip for public paths
        if _is_public_path(request.url.path):
            return await call_next(request)

        # Skip if no role rules configured
        if not self._role_rules:
            return await call_next(request)

        # Check if any rule matches the current path
        user_roles = getattr(request.state, "roles", [])
        for path_prefix, required_roles in self._role_rules.items():
            if request.url.path.startswith(path_prefix) and not any(
                role in user_roles for role in required_roles
            ):
                    logger.warning(
                        "rbac_denied",
                        path=request.url.path,
                        user_roles=user_roles,
                        required_roles=required_roles,
                    )
                    return JSONResponse(
                        status_code=403,
                        content={"detail": "Insufficient permissions"},
                    )

        return await call_next(request)


def _is_public_path(path: str) -> bool:
    """Check if a path is public (no auth required)."""
    if path in PUBLIC_PATHS:
        return True
    return any(path.startswith(prefix) for prefix in PUBLIC_PREFIXES)
