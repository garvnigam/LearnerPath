"""Hybrid course retrieval:
1. Query internal DB (Azure Postgres or Supabase).
2. Query live public APIs (MIT Learn, NPTEL, ...).
3. Optionally ask the LLM to propose extras with a web search tool.
4. Dedupe, score, return top-K to the ranker/planner.

Every source implements the same interface: `async def fetch(...) -> list[dict]`.
Sources are pluggable; add/remove in `SOURCES`.
"""
from __future__ import annotations

import asyncio
from typing import Callable, Awaitable

from .catalog import CURATED, filter_catalog
from .mit_learn import fetch_mit_courses
from .supabase_client import get_supabase


# ------------- Source: internal DB (unified `courses` table via match_courses RPC) -------------
async def fetch_db(
    subjects: list[str],
    focus: list[str],
    level: str,
    budget: str = "prefer_free",
    limit: int = 40,
    concepts: list[str] | None = None,
    max_hours: float | None = None,
    language: str = "en",
) -> list[dict]:
    sb = get_supabase()
    if not sb:
        return []
    topics = list({t.lower() for t in subjects + focus if t})
    if not topics:
        return []

    price_types = ["free", "audit_free"] if budget == "free_only" else ["free", "audit_free", "paid", "freemium"]
    params = {
        "q_topics": topics,
        "q_concepts": concepts or [],
        "level_in": _nearby_levels(level),
        "price_types": price_types,
        "language_in": [language, "en"],
        "max_hours": max_hours,
        "max_count": limit,
    }

    try:
        # Preferred: single-query RPC on the unified `courses` table
        res = sb.rpc("match_courses", params).execute()
        rows = res.data or []
        if rows:
            return rows
    except Exception as e:
        print(f"[hybrid] match_courses RPC failed, falling back to table select: {e}")

    # Fallback: legacy harvard_pll_courses table
    try:
        q = sb.table("harvard_pll_courses").select("*")
        q = q.overlaps("topics", topics).in_("level", _nearby_levels(level))
        if budget == "free_only":
            q = q.eq("price_type", "free")
        return q.limit(limit).execute().data or []
    except Exception as e:
        print(f"[hybrid] db fetch failed: {e}")
        return []


def _nearby_levels(level: str) -> list[str]:
    order = ["beginner", "intermediate", "advanced"]
    if level not in order:
        return order
    i = order.index(level)
    return order[max(0, i-1): min(3, i+2)]


# ------------- Source: MIT Learn API (already wired) -------------
async def fetch_mit(subjects: list[str], focus: list[str], level: str, limit: int = 20) -> list[dict]:
    return await fetch_mit_courses(subjects + focus, limit=limit)


# ------------- Source: local curated catalog -------------
async def fetch_curated(subjects: list[str], focus: list[str], level: str, limit: int = 20) -> list[dict]:
    return filter_catalog(subjects + focus, level)[:limit]


# ------------- Source: LLM-guided web extras (fallback) -------------
async def fetch_llm_extras(subjects: list[str], focus: list[str], level: str, needed: int) -> list[dict]:
    """
    Only invoked when other sources returned < N candidates.
    Uses the LLM to propose real, well-known URLs. Validates each URL exists.
    """
    if needed <= 0:
        return []
    from .azure_client import chat_json
    system = (
        "You suggest well-known free courses/playlists that ACTUALLY EXIST. "
        "Only return URLs on: youtube.com, coursera.org, edx.org, mit.edu, "
        "stanford.edu, harvard.edu, cs50.harvard.edu, nptel.ac.in, khanacademy.org, "
        "freecodecamp.org, 3blue1brown.com, fast.ai. "
        "Never invent URLs. If unsure, omit."
    )
    prompt = (
        f"Subjects: {', '.join(subjects)}\n"
        f"Focus: {', '.join(focus)}\n"
        f"Level: {level}\n"
        f"Return up to {needed} JSON entries with keys: title, provider, url, level, description, topics (array), format (course|playlist)."
    )
    try:
        data = chat_json(system, [{"role":"user","content":prompt}], temperature=0.2)
    except Exception as e:
        print(f"[hybrid] llm extras failed: {e}")
        return []
    proposals = data.get("courses") or data.get("extras") or []

    # validate URLs exist (HEAD request, 5s timeout)
    import httpx
    validated = []
    async with httpx.AsyncClient(timeout=5, follow_redirects=True) as client:
        async def _check(p):
            try:
                r = await client.head(p["url"])
                if r.status_code < 400:
                    validated.append(p)
            except Exception:
                pass
        await asyncio.gather(*[_check(p) for p in proposals if p.get("url")])
    return validated


# ------------- Orchestrator -------------

SOURCES: list[tuple[str, Callable[..., Awaitable[list[dict]]]]] = [
    ("db",       fetch_db),
    ("mit",      fetch_mit),
    ("curated",  fetch_curated),
]


async def gather_candidates(
    subjects: list[str],
    focus: list[str],
    level: str,
    budget: str = "prefer_free",
    total_target: int = 40,
    allow_llm_fallback: bool = True,
    level_by_subject: dict[str, str] | None = None,
) -> list[dict]:
    """Run all sources in parallel per-subject, dedupe, and optionally fill with LLM extras.

    If `level_by_subject` is provided, one retrieval pass is fired for EACH subject
    at that subject's own level (so a learner who is advanced in ML but beginner in
    cybersecurity gets courses that fit each subject individually).
    """
    level_by_subject = level_by_subject or {s: level for s in subjects}

    tasks: list[Awaitable[list[dict]]] = []
    # One (db+mit+curated) pass per subject, sized to leave room for merging.
    per_subject_limit = max(6, total_target // max(1, len(subjects)))
    for subj in subjects:
        subj_level = level_by_subject.get(subj, level)
        # topics passed = only this subject + focus areas (keep it focused)
        tasks.extend([
            fetch_db([subj], focus, subj_level, budget=budget, limit=per_subject_limit),
            fetch_mit([subj], focus, subj_level, limit=max(4, per_subject_limit // 2)),
            fetch_curated([subj], focus, subj_level, limit=max(4, per_subject_limit // 2)),
        ])

    results = await asyncio.gather(*tasks, return_exceptions=True)

    merged: list[dict] = []
    for r in results:
        if isinstance(r, Exception):
            print(f"[hybrid] source error: {r}")
            continue
        merged.extend(r)

    deduped = _dedupe_by_url(merged)

    if allow_llm_fallback and len(deduped) < 12:
        extras = await fetch_llm_extras(subjects, focus, level, needed=12 - len(deduped))
        deduped.extend(extras)
        deduped = _dedupe_by_url(deduped)

    return deduped[:total_target]


def _dedupe_by_url(rows: list[dict]) -> list[dict]:
    seen: set[str] = set()
    out = []
    for r in rows:
        url = (r.get("url") or "").rstrip("/")
        if not url or url in seen:
            continue
        seen.add(url)
        out.append(r)
    return out
