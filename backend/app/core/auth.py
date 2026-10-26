import uuid
from dataclasses import dataclass
from functools import lru_cache
from typing import Any

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient

from app.core.config import Settings, get_settings

_bearer = HTTPBearer(auto_error=False)
_ALGORITHMS = ["RS256", "ES256"]


@dataclass(frozen=True)
class AuthUser:
    id: uuid.UUID
    email: str | None


def _unauthorized(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def _issuer(settings: Settings) -> str:
    return f"{settings.supabase_url.rstrip('/')}/auth/v1"


@lru_cache
def _jwks_client(jwks_url: str) -> PyJWKClient:
    return PyJWKClient(jwks_url, cache_keys=True)


def _signing_key(token: str, settings: Settings) -> Any:
    client = _jwks_client(f"{_issuer(settings)}/.well-known/jwks.json")
    return client.get_signing_key_from_jwt(token).key


def verify_token(token: str, settings: Settings) -> AuthUser:
    """Validate a Supabase access token and return the user it identifies."""
    if not settings.supabase_url:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Auth is not configured")
    try:
        claims = jwt.decode(
            token,
            _signing_key(token, settings),
            algorithms=_ALGORITHMS,
            audience="authenticated",
            issuer=_issuer(settings),
            options={"require": ["exp", "sub"]},
        )
        return AuthUser(id=uuid.UUID(claims["sub"]), email=claims.get("email"))
    except (jwt.PyJWTError, ValueError) as exc:
        raise _unauthorized("Invalid or expired token") from exc


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    settings: Settings = Depends(get_settings),
) -> AuthUser:
    if credentials is None:
        raise _unauthorized("Missing bearer token")
    return verify_token(credentials.credentials, settings)
