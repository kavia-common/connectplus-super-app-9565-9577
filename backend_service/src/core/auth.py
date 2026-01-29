from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.core.settings import get_settings

bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class AuthUser:
    """Authenticated principal extracted from JWT.

    Note: This is a minimal stub to unblock domain APIs. Replace with full auth later.
    """

    user_id: str
    roles: List[str]


def _unauthorized(detail: str = "Not authenticated") -> HTTPException:
    return HTTPException(status_code=401, detail=detail)


def _forbidden(detail: str = "Not authorized") -> HTTPException:
    return HTTPException(status_code=403, detail=detail)


# PUBLIC_INTERFACE
def get_current_user(
    creds: Optional[HTTPAuthorizationCredentials] = Depends(bearer),
) -> AuthUser:
    """Resolve current user from a Bearer JWT.

    Token payload expectations (minimal):
    - sub: user id string
    - roles: list[str] (optional, defaults to ["user"])

    Returns:
        AuthUser: authenticated user.

    Raises:
        HTTPException: 401 when token missing/invalid.
    """
    if creds is None:
        raise _unauthorized()

    token = creds.credentials
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except jwt.PyJWTError:
        raise _unauthorized("Invalid token")

    user_id = payload.get("sub")
    if not user_id:
        raise _unauthorized("Token missing subject")

    roles = payload.get("roles") or ["user"]
    if not isinstance(roles, list):
        roles = ["user"]

    return AuthUser(user_id=str(user_id), roles=[str(r) for r in roles])


# PUBLIC_INTERFACE
def require_roles(required: List[str]):
    """Dependency factory enforcing that the current user has at least one required role.

    Args:
        required: List of allowed roles.

    Returns:
        Dependency callable returning AuthUser.
    """

    def _dep(user: AuthUser = Depends(get_current_user)) -> AuthUser:
        if any(r in user.roles for r in required):
            return user
        raise _forbidden()

    return _dep
