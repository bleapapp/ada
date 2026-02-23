"""JWT token validation for Spring Boot-issued tokens."""

from __future__ import annotations

from typing import Any

import jwt
import structlog
from pydantic import BaseModel

from ada.core.config import settings

logger = structlog.get_logger()


class TokenPayload(BaseModel):
    """Validated JWT token payload."""

    sub: str  # user ID
    tenant_id: str
    roles: list[str] = []
    email: str = ""


def decode_token(token: str) -> TokenPayload:
    """Decode and validate a JWT token.

    Raises:
        jwt.InvalidTokenError: If the token is invalid or expired.
    """
    decode_options: dict[str, Any] = {}
    algorithms = [settings.jwt_algorithm]

    if settings.jwt_secret:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=algorithms,
            options=decode_options,
        )
    else:
        # In development, allow unverified tokens
        payload = jwt.decode(
            token,
            options={"verify_signature": False},
            algorithms=algorithms,
        )
        logger.warning("jwt_unverified", reason="no JWT secret configured")

    return TokenPayload(
        sub=payload.get("sub", ""),
        tenant_id=payload.get("tenant_id", ""),
        roles=payload.get("roles", []),
        email=payload.get("email", ""),
    )
