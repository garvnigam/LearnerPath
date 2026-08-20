"""JWT verification for Microsoft Entra External ID (customer/CIAM) tokens.

We fetch the tenant's OIDC discovery document + JWKS, cache them, and validate
the incoming Bearer token's signature, issuer, audience, and (optionally) scope.
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Optional

import httpx
import jwt
from fastapi import Depends, Header, HTTPException, status

from .config import settings


@dataclass
class Principal:
    subject: str
    phone: Optional[str]
    name: Optional[str]
    claims: dict


_JWKS_CACHE: dict = {"keys": None, "issuer": None, "fetched_at": 0.0}
_JWKS_TTL_SECONDS = 3600


def _oidc_config_url() -> str:
    if settings.entra_tenant_subdomain and settings.entra_tenant_id:
        return (
            f"https://{settings.entra_tenant_subdomain}.ciamlogin.com/"
            f"{settings.entra_tenant_id}/v2.0/.well-known/openid-configuration"
        )
    raise RuntimeError(
        "Entra External ID is not configured: set ENTRA_TENANT_SUBDOMAIN and ENTRA_TENANT_ID"
    )


def _refresh_jwks(force: bool = False) -> None:
    now = time.time()
    if not force and _JWKS_CACHE["keys"] and (now - _JWKS_CACHE["fetched_at"] < _JWKS_TTL_SECONDS):
        return
    with httpx.Client(timeout=10.0) as client:
        oidc = client.get(_oidc_config_url()).json()
        jwks = client.get(oidc["jwks_uri"]).json()
    _JWKS_CACHE["keys"] = {k["kid"]: k for k in jwks.get("keys", [])}
    _JWKS_CACHE["issuer"] = oidc.get("issuer")
    _JWKS_CACHE["fetched_at"] = now


def _get_signing_key(kid: str):
    _refresh_jwks()
    key = _JWKS_CACHE["keys"].get(kid)
    if not key:
        _refresh_jwks(force=True)
        key = _JWKS_CACHE["keys"].get(kid)
    if not key:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Unknown token signing key")
    return jwt.algorithms.RSAAlgorithm.from_jwk(key)


def _decode_token(token: str) -> dict:
    try:
        header = jwt.get_unverified_header(token)
    except jwt.PyJWTError as e:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, f"Malformed token: {e}")

    kid = header.get("kid")
    if not kid:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token missing kid header")

    signing_key = _get_signing_key(kid)
    audience = settings.entra_api_client_id or None

    try:
        claims = jwt.decode(
            token,
            signing_key,
            algorithms=["RS256"],
            audience=audience,
            issuer=_JWKS_CACHE["issuer"],
            options={"require": ["exp", "iss", "sub"]},
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token expired")
    except jwt.InvalidAudienceError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token audience mismatch")
    except jwt.InvalidIssuerError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token issuer mismatch")
    except jwt.PyJWTError as e:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, f"Token validation failed: {e}")

    if settings.entra_required_scope:
        scp = claims.get("scp", "")
        if settings.entra_required_scope not in scp.split():
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Missing required scope")

    return claims


async def require_user(authorization: Optional[str] = Header(default=None)) -> Principal:
    if settings.entra_auth_disabled:
        return Principal(subject="anonymous", phone=None, name=None, claims={})

    if not settings.entra_tenant_id or not settings.entra_tenant_subdomain or not settings.entra_api_client_id:
        # Auth not configured yet — behave like the escape hatch so dev/demo still works.
        return Principal(subject="anonymous", phone=None, name=None, claims={})

    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing bearer token")

    token = authorization.split(" ", 1)[1].strip()
    claims = _decode_token(token)
    return Principal(
        subject=str(claims.get("sub", "")),
        phone=claims.get("phone_number") or claims.get("phoneNumber"),
        name=claims.get("name") or claims.get("preferred_username"),
        claims=claims,
    )


CurrentUser = Depends(require_user)
