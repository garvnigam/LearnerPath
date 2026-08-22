#!/usr/bin/env python3
"""Ingest MIT Learn (learn.mit.edu) into the unified `courses` table.

Source: https://api.learn.mit.edu/api/v1/learning_resources_search/
No auth. Paginates via offset.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import httpx

from sources.base import (
    build_row, clean_text, get_client, map_level, normalize_topics, upsert_courses,
)

BASE = "https://api.learn.mit.edu/api/v1/learning_resources_search/"
PAGE_SIZE = 100
MAX_ITEMS = 5000  # safety cap


def fetch_page(client: httpx.Client, offset: int) -> dict:
    params = {"resource_type": ["course", "program"], "limit": PAGE_SIZE, "offset": offset}
    r = client.get(BASE, params=params)
    r.raise_for_status()
    return r.json()


def _first(field):
    """Return first value regardless of dict/list/scalar."""
    if not field:
        return None
    if isinstance(field, list):
        return field[0] if field else None
    return field


def _name_of(field) -> str | None:
    v = _first(field)
    if isinstance(v, dict):
        return v.get("name") or v.get("value") or v.get("code")
    if isinstance(v, str):
        return v
    return None


def normalize(item: dict) -> dict | None:
    url = item.get("url")
    if not url and item.get("runs"):
        first_run = _first(item.get("runs"))
        if isinstance(first_run, dict):
            url = first_run.get("url")
    if not url:
        return None

    levels = item.get("learning_format") or item.get("levels") or []
    level = "intermediate"
    first_level = _first(levels)
    if first_level:
        if isinstance(first_level, dict):
            level = map_level(first_level.get("name") or first_level.get("value") or first_level.get("code"))
        else:
            level = map_level(str(first_level))

    topics = normalize_topics(item.get("topics", [])) + normalize_topics(item.get("ocw_topics", []))
    subjects = normalize_topics(item.get("departments", []))
    if not subjects and any("comput" in t.lower() for t in topics):
        subjects = ["computer science"]

    duration_hours = None
    if item.get("min_weekly_hours") and item.get("max_weeks"):
        try:
            duration_hours = float(item["min_weekly_hours"]) * float(item["max_weeks"])
        except (TypeError, ValueError):
            pass

    return build_row(
        source="mit_learn",
        external_id=str(item.get("id")) if item.get("id") is not None else None,
        url=url,
        title=item.get("title") or "Untitled",
        description=clean_text(item.get("description") or item.get("full_description")),
        provider="MIT",
        school=(subjects[0] if subjects else "MIT"),
        platform=_name_of(item.get("offered_by")) or "MIT OpenCourseWare",
        level=level,
        topics=topics,
        subjects=subjects,
        tags=normalize_topics(item.get("course_feature", [])),
        format="course",
        modality=_name_of(item.get("delivery")) or "online",
        language=(item.get("languages", ["en"])[0] if item.get("languages") else "en"),
        duration_hours=round(duration_hours, 2) if duration_hours else None,
        weeks=int(item["max_weeks"]) if item.get("max_weeks") else None,
        hours_per_week_min=float(item["min_weekly_hours"]) if item.get("min_weekly_hours") else None,
        hours_per_week_max=float(item["max_weekly_hours"]) if item.get("max_weekly_hours") else None,
        price_type="free" if item.get("free") else "audit_free",
        certificate_available=bool(item.get("certification")),
        image_url=(item.get("image") or {}).get("url") if isinstance(item.get("image"), dict) else None,
    )


def main():
    supabase = get_client()
    offset = 0
    total_upserted = 0
    total_errors = 0

    with httpx.Client(timeout=60.0, headers={"User-Agent": "Mozilla/5.0"}) as client:
        while offset < MAX_ITEMS:
            print(f"[mit_learn] fetching offset={offset} ...")
            try:
                data = fetch_page(client, offset)
            except Exception as e:
                print(f"[mit_learn] fetch failed at offset {offset}: {e}")
                break
            results = data.get("results", []) or []
            if not results:
                print(f"[mit_learn] no more results at offset {offset}")
                break

            rows = [n for n in (normalize(x) for x in results) if n]
            print(f"[mit_learn] normalized {len(rows)}/{len(results)} rows")
            up, err = upsert_courses(supabase, rows, batch_size=100)
            total_upserted += up
            total_errors += err

            if len(results) < PAGE_SIZE:
                break
            offset += PAGE_SIZE
            time.sleep(0.3)

    print(f"[mit_learn] done: upserted={total_upserted}, errors={total_errors}")


if __name__ == "__main__":
    main()
