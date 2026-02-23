"""FastAPI dependencies for auth context."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi import Request


def get_tenant_id(request: Request) -> str:
    """Extract tenant_id from request state (set by AuthMiddleware)."""
    return request.state.tenant_id


def get_user_id(request: Request) -> str:
    """Extract user_id from request state (set by AuthMiddleware)."""
    return request.state.user_id


def get_roles(request: Request) -> list[str]:
    """Extract roles from request state (set by AuthMiddleware)."""
    return request.state.roles
