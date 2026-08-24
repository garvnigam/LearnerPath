"""Hybrid course retrieval:
1. Query internal DB with two complementary strategies:
     - keyword/concept match  (`match_courses` RPC)
     - semantic similarity    (`search_courses_semantic` RPC on HNSW-indexed embeddings)
2. Query local curated catalog as a safety net.
3. Optionally ask the LLM to propose extras with a web search tool.
4. Dedupe, score, return top-K to the ranker/planner.

Semantic + keyword together catch both paraphrases (semantic) and precise
skill matches (keyword). Deduped by URL. Concept-overlap dedup collapses
near-duplicate topics before the LLM sees them.
"""
from __future__ import annotations

import asyncio
from typing import Awaitable

from .azure_client import embed_text
from .catalog import filter_catalog
from .supabase_client import get_supabase


# ------------- Source: internal DB (unified `courses` table via match_courses RPC) -------------
BUDGET_TO_PRICE_TYPES = {
    "strictly_free":  ["free"],
    "free_and_audit": ["free", "audit_free"],
    "free_and_paid":  ["free", "audit_free", "paid", "freemium"],
    # legacy aliases (in case older sessions send these values)
    "free_only":      ["free"],
}


async def fetch_db(
    subjects: list[str],
    focus: list[str],
    level: str,
    budget: str = "strictly_free",
    limit: int = 40,
    concepts: list[str] | None = None,
    max_hours: float | None = None,
    language: str = "en",
) -> list[dict]:
    """Fetch candidates from the unified `courses` table.

    budget:
        "strictly_free"  -> only price_type = 'free' (no audit-required Coursera courses)
        "free_and_audit" -> price_type in ('free', 'audit_free'); Coursera audit-free courses included
        "free_and_paid"  -> all four price types
    """
    sb = get_supabase()
    if not sb:
        return []
    topics = list({t.lower() for t in subjects + focus if t})
    if not topics:
        return []

    price_types = BUDGET_TO_PRICE_TYPES.get(budget, ["free"])
    params = {
        "q_topics": topics,
        "q_concepts": concepts or [],
        "level_in": _nearby_levels(level),
        "price_types": price_types,
        "language_in": [language, "en"],
        "max_hours": max_hours,
        "max_count": limit,
    }

    rows: list[dict] = []
    try:
        res = sb.rpc("match_courses", params).execute()
        rows = res.data or []
    except Exception as e:
        print(f"[hybrid] match_courses RPC failed, falling back to table select: {e}")
        try:
            q = sb.table("courses").select("*")
            q = q.overlaps("topics", topics).in_("level", _nearby_levels(level)).in_("price_type", price_types)
            rows = q.limit(limit).execute().data or []
        except Exception as e2:
            print(f"[hybrid] fallback failed: {e2}")

    return rows[:limit]


def _nearby_levels(level: str) -> list[str]:
    order = ["beginner", "intermediate", "advanced"]
    if level not in order:
        return order
    i = order.index(level)
    return order[max(0, i-1): min(3, i+2)]


def _semantic_query_text(subject: str, focus: list[str], gap_concepts: list[str]) -> str:
    """Build the text we embed for semantic search.

    Format matches how course rows are embedded (title + description + topics + concepts),
    so cosine similarity picks up courses that teach exactly these gaps within this subject.
    """
    parts = [subject]
    if focus:
        parts.append("focus on " + ", ".join(focus[:6]))
    if gap_concepts:
        parts.append("skills to learn: " + ", ".join(gap_concepts[:8]))
    return ". ".join(parts)


# ------------- Source: internal DB semantic search (HNSW on embedding column) -------------
async def fetch_semantic(
    query_embedding: list[float] | None,
    level: str,
    budget: str = "strictly_free",
    limit: int = 20,
    max_hours: float | None = None,
    language: str = "en",
) -> list[dict]:
    """Semantic top-K via `search_courses_semantic` RPC.

    Returns rows ordered by cosine similarity to `query_embedding`, filtered by
    level / price / language. Complementary to `fetch_db` (keyword) — captures
    paraphrased or niche queries that exact topic-overlap would miss.
    """
    if not query_embedding:
        return []
    sb = get_supabase()
    if not sb:
        return []

    price_types = BUDGET_TO_PRICE_TYPES.get(budget, ["free"])
    params = {
        "q_embedding": query_embedding,
        "level_in": _nearby_levels(level),
        "price_types": price_types,
        "language_in": [language, "en"],
        "max_hours": max_hours,
        "match_count": limit,
    }
    try:
        r = sb.rpc("search_courses_semantic", params).execute()
        return r.data or []
    except Exception as e:
        print(f"[hybrid] semantic RPC failed: {e}")
        return []


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


async def gather_candidates(
    subjects: list[str],
    focus: list[str],
    level: str,
    budget: str = "strictly_free",
    total_target: int = 40,
    allow_llm_fallback: bool = True,
    level_by_subject: dict[str, str] | None = None,
    gap_concepts_by_subject: dict[str, list[str]] | None = None,
    demonstrated_concepts: list[str] | None = None,
) -> list[dict]:
    """Run all sources in parallel per-subject, dedupe, and optionally fill with LLM extras.

    budget: 'strictly_free' | 'free_and_audit' | 'free_and_paid'.
    gap_concepts_by_subject: concepts the learner MISSED per subject. Retrieval boosts
        courses whose `concepts` array overlaps these (SQL: `c.concepts && q_concepts`,
        with a +2 boost over topic match).
    demonstrated_concepts: concepts the learner ANSWERED CORRECTLY (currently unused
        at retrieval time; useful for future prerequisite pruning).
    """
    level_by_subject = level_by_subject or {s: level for s in subjects}
    gap_concepts_by_subject = gap_concepts_by_subject or {}

    # Embed one query text per subject (subject + focus + that subject's gap concepts).
    # Fires all embeddings in parallel; each one becomes a semantic search below.
    subject_embed_tasks = [
        embed_text(
            _semantic_query_text(subj, focus, gap_concepts_by_subject.get(subj, []))
        )
        for subj in subjects
    ]
    subject_embeddings = await asyncio.gather(*subject_embed_tasks, return_exceptions=True)
    subject_embeddings_by_name: dict[str, list[float] | None] = {}
    for subj, emb in zip(subjects, subject_embeddings):
        if isinstance(emb, Exception) or not emb:
            print(f"[hybrid] embedding failed for '{subj}': {emb}")
            subject_embeddings_by_name[subj] = None
        else:
            subject_embeddings_by_name[subj] = emb

    tasks: list[Awaitable[list[dict]]] = []
    per_subject_limit = max(6, total_target // max(1, len(subjects)))
    for subj in subjects:
        subj_level = level_by_subject.get(subj, level)
        subj_gap_concepts = gap_concepts_by_subject.get(subj, [])
        subj_emb = subject_embeddings_by_name.get(subj)
        tasks.extend([
            fetch_db(
                [subj], focus, subj_level,
                budget=budget,
                limit=per_subject_limit,
                concepts=subj_gap_concepts,
            ),
            fetch_semantic(
                subj_emb,
                subj_level,
                budget=budget,
                limit=per_subject_limit,
            ),
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
    # Also collapse near-duplicates by concept overlap so the planner doesn't
    # see multiple beginner courses covering the same skills.
    deduped = _dedupe_by_concept_overlap(deduped)

    if allow_llm_fallback and len(deduped) < 12:
        extras = await fetch_llm_extras(subjects, focus, level, needed=12 - len(deduped))
        deduped.extend(extras)
        deduped = _dedupe_by_url(deduped)
        deduped = _dedupe_by_concept_overlap(deduped)

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


def _dedupe_by_concept_overlap(rows: list[dict], overlap_ratio: float = 0.6) -> list[dict]:
    """Drop later rows that share >= overlap_ratio of their concepts (or topics if no concepts)
    with any earlier kept row. Runs after URL dedupe. Preserves order (which reflects rank).

    This prevents e.g. 'Intro to Programming' + 'Programming Basics' both appearing.
    """
    kept: list[dict] = []
    kept_concept_sets: list[set[str]] = []
    for r in rows:
        cs = {c.lower().strip() for c in (r.get("concepts") or []) if c}
        if not cs:
            cs = {t.lower().strip() for t in (r.get("topics") or []) if t}
        if not cs:
            kept.append(r)
            kept_concept_sets.append(set())
            continue
        is_dup = False
        for prev in kept_concept_sets:
            if not prev:
                continue
            common = cs & prev
            if len(common) / max(1, min(len(cs), len(prev))) >= overlap_ratio:
                is_dup = True
                break
        if not is_dup:
            kept.append(r)
            kept_concept_sets.append(cs)
    return kept
