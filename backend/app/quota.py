"""MVP quota enforcement (in-memory, per-process):
- Users in the allowlist can log in unlimited times (no IP check either).
- Everyone else can log in ONCE ever (within this backend process).
- We also block re-use by IP: if the same IP tries to sign in with a second
  account, it's rejected (unless the new account is allowlisted).
- Every session auto-expires after SESSION_TTL_SECONDS from first activity.

State lives in module-level dicts; no DB dependency. Restarting the backend
resets the ledger, which is fine for an MVP.
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Optional

from fastapi import Depends, HTTPException, Request, status

from .auth import Principal, require_user
from .config import settings


# ---------- in-memory state ----------
_LOGIN_LEDGER: dict[str, dict] = {}     # subject -> {email, first_seen_at, ip}
_IP_LEDGER: dict[str, str] = {}         # ip -> subject that first used it
_SESSION_STARTS: dict[str, float] = {}  # subject -> unix ts of first activity in this run


def _allowlist() -> set[str]:
    return {
        e.strip().lower()
        for e in (settings.login_allowlist_emails or "").split(",")
        if e.strip()
    }


def _ip_allowlist() -> set[str]:
    return {
        i.strip()
        for i in (settings.login_allowlist_ips or "").split(",")
        if i.strip()
    }


def _identify(user: Principal) -> tuple[str, str]:
    claims = user.claims or {}
    email = (
        claims.get("email")
        or claims.get("preferred_username")
        or user.name
        or ""
    ).lower()
    subject = user.subject or email or "anonymous"
    return subject, email


def _is_unlimited(email: str) -> bool:
    return email.lower() in _allowlist()


def _client_ip(request: Request) -> str:
    # Trust the first hop in X-Forwarded-For when present (typical Vercel/Nginx setup).
    xff = request.headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip()
    real = request.headers.get("x-real-ip")
    if real:
        return real.strip()
    return request.client.host if request.client else "unknown"


# ---------- public API ----------
@dataclass
class StartResult:
    allowed: bool
    reason: Optional[str]
    is_unlimited: bool
    ttl_seconds: int
    session_expires_at: float  # unix ts


def start_session(user: Principal, request: Request) -> StartResult:
    if settings.entra_auth_disabled:
        return StartResult(True, None, True, settings.session_ttl_seconds,
                           time.time() + settings.session_ttl_seconds)

    subject, email = _identify(user)
    unlimited = _is_unlimited(email)
    ip = _client_ip(request)
    ip_exempt = ip in _ip_allowlist()

    already_subject = subject in _LOGIN_LEDGER
    ip_owner = _IP_LEDGER.get(ip)

    if not unlimited and not ip_exempt and settings.single_login_enforced:
        if already_subject:
            return StartResult(
                allowed=False,
                reason="This account has already been used. Only one login per user is allowed in this MVP.",
                is_unlimited=False,
                ttl_seconds=settings.session_ttl_seconds,
                session_expires_at=0.0,
            )
        if ip_owner and ip_owner != subject:
            return StartResult(
                allowed=False,
                reason="This device / network has already been used to sign in. Only one account per network is allowed in this MVP.",
                is_unlimited=False,
                ttl_seconds=settings.session_ttl_seconds,
                session_expires_at=0.0,
            )

    if not already_subject:
        _LOGIN_LEDGER[subject] = {"email": email, "first_seen_at": time.time(), "ip": ip}
    if not unlimited and not ip_exempt and ip_owner is None:
        _IP_LEDGER[ip] = subject

    now = time.time()
    _SESSION_STARTS[subject] = now
    return StartResult(
        allowed=True,
        reason=None,
        is_unlimited=unlimited or ip_exempt,
        ttl_seconds=settings.session_ttl_seconds,
        session_expires_at=now + settings.session_ttl_seconds,
    )


def enforce_active_session(request: Request, user: Principal = Depends(require_user)) -> Principal:
    """Reject requests once the per-session TTL has elapsed (unless unlimited)."""
    if settings.entra_auth_disabled:
        return user

    subject, email = _identify(user)
    if _is_unlimited(email) or _client_ip(request) in _ip_allowlist():
        return user

    started = _SESSION_STARTS.get(subject)
    if started is None:
        # First activity in this process without calling /session/start — start the clock now.
        _SESSION_STARTS[subject] = time.time()
        return user

    if time.time() - started > settings.session_ttl_seconds:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "session_expired")
    return user
