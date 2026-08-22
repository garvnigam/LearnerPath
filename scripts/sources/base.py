"""Shared helpers for course ingestion into the unified `courses` table.

Every source-specific ingestor imports `upsert_courses`, normalizes its data
into the schema, and calls it in batches. Idempotent (upserts on `source, url`).
"""
from __future__ import annotations

import os
import re
import sys
import time
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from supabase import Client, create_client

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / "backend" / ".env")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE = os.getenv("SUPABASE_SERVICE_ROLE")

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE:
    print("ERROR: SUPABASE_URL and SUPABASE_SERVICE_ROLE must be set in backend/.env")
    sys.exit(1)


def get_client() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE)


ALLOWED_LEVELS = {"beginner", "intermediate", "advanced"}
ALLOWED_PRICE_TYPES = {"free", "audit_free", "paid", "freemium"}


def map_level(raw: Optional[str]) -> str:
    if not raw:
        return "intermediate"
    r = str(raw).strip().lower()
    if r in ("beginner", "intro", "introductory", "elementary", "basic", "novice"):
        return "beginner"
    if r in ("advanced", "expert", "graduate", "phd"):
        return "advanced"
    if r in ("intermediate", "moderate"):
        return "intermediate"
    # generic hints
    if any(k in r for k in ("intro", "basic", "beginner")):
        return "beginner"
    if any(k in r for k in ("advanced", "expert", "graduate")):
        return "advanced"
    return "intermediate"


def map_price_type(raw: Optional[str], is_free: Optional[bool] = None) -> str:
    if is_free is True:
        return "free"
    if is_free is False:
        return "paid"
    if not raw:
        return "free"
    r = str(raw).strip().lower()
    if r in ALLOWED_PRICE_TYPES:
        return r
    if r in ("audit", "audit_free", "audit for free"):
        return "audit_free"
    if r in ("free",):
        return "free"
    if r in ("paid", "premium"):
        return "paid"
    return "free"


def clean_text(txt: Optional[str], max_len: int = 2000) -> Optional[str]:
    if not txt:
        return None
    # strip HTML tags cheaply
    txt = re.sub(r"<[^>]+>", " ", str(txt))
    txt = re.sub(r"\s+", " ", txt).strip()
    return txt[:max_len] if txt else None


def normalize_topics(items: Optional[list]) -> list[str]:
    out: list[str] = []
    if not items:
        return out
    for item in items:
        if isinstance(item, dict):
            v = item.get("name") or item.get("title") or item.get("value")
        else:
            v = str(item)
        if v:
            v = v.strip()
            if v and v.lower() not in {t.lower() for t in out}:
                out.append(v)
    return out


def build_row(**kwargs) -> dict:
    """Assemble a row dict, dropping None values (except required ones)."""
    required = {"source", "url", "title", "level", "price_type"}
    row = {k: v for k, v in kwargs.items() if v is not None or k in required}
    # Defaults for arrays
    for k in ("topics", "concepts", "subjects", "tags", "prerequisite_concepts", "subtitles"):
        row.setdefault(k, [])
    # Defaults for enums
    if row.get("level") not in ALLOWED_LEVELS:
        row["level"] = "intermediate"
    if row.get("price_type") not in ALLOWED_PRICE_TYPES:
        row["price_type"] = "free"
    return row


def upsert_courses(supabase: Client, rows: list[dict], batch_size: int = 50, max_retries: int = 5) -> tuple[int, int]:
    """Upsert rows in batches, returns (upserted, errors)."""
    total = len(rows)
    upserted = 0
    errors = 0
    for i in range(0, total, batch_size):
        batch = rows[i:i + batch_size]
        backoff = 4
        for attempt in range(1, max_retries + 1):
            try:
                result = supabase.table("courses").upsert(batch, on_conflict="source,url").execute()
                if result.data is not None:
                    upserted += len(result.data)
                else:
                    upserted += len(batch)
                print(f"    ↑ {i + len(batch)}/{total} upserted")
                break
            except Exception as e:
                msg = str(e)
                is_transient = any(w in msg.lower() for w in ("timeout", "upstream", "504", "502", "503", "connection"))
                if attempt >= max_retries or not is_transient:
                    errors += 1
                    print(f"    ! batch {i}-{i+len(batch)} failed permanently: {msg[:200]}")
                    break
                print(f"    ! batch attempt {attempt}/{max_retries} failed, retrying in {backoff}s: {msg[:120]}")
                time.sleep(backoff)
                backoff = min(backoff * 2, 60)
    return upserted, errors
