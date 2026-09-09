"""Open session dependency used while the application has no login policy."""
from __future__ import annotations

import time
from dataclasses import dataclass

from fastapi import Depends, Request

from .auth import Principal, require_user


# ---------- public API ----------
@dataclass
class StartResult:
    allowed: bool
    reason: str | None
    is_unlimited: bool
    ttl_seconds: int
    session_expires_at: float  # unix ts


def start_session(user: Principal, request: Request) -> StartResult:
    now = time.time()
    return StartResult(
        allowed=True,
        reason=None,
        is_unlimited=True,
        ttl_seconds=0,
        session_expires_at=now,
    )


def enforce_active_session(request: Request, user: Principal = Depends(require_user)) -> Principal:
    return user
