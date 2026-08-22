#!/usr/bin/env python3
"""Ingest Microsoft Learn catalog into the unified `courses` table.

Source: https://learn.microsoft.com/api/catalog/  (no auth, single JSON dump ~14 MB)
Yields: 3459 modules + 842 learning paths + 143 courses + 151 certifications = ~4600 rows.

Run:
  python scripts/sources/ingest_microsoft_learn.py
"""
from __future__ import annotations

import sys
from pathlib import Path

# Add scripts/ to path so `sources.base` resolves
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import httpx

from sources.base import (
    build_row, clean_text, get_client, map_level, map_price_type,
    normalize_topics, upsert_courses,
)

CATALOG_URL = "https://learn.microsoft.com/api/catalog/"


def fetch_catalog() -> dict:
    print(f"[ms_learn] fetching {CATALOG_URL} ...")
    with httpx.Client(timeout=60.0) as client:
        r = client.get(CATALOG_URL, headers={"Accept": "application/json"})
        r.raise_for_status()
        return r.json()


def _normalize_level(levels_field) -> str:
    if not levels_field:
        return "intermediate"
    if isinstance(levels_field, list) and levels_field:
        raw = levels_field[0]
        return map_level(raw)
    return map_level(str(levels_field))


def _duration_hours(minutes: int | None, hours: float | None) -> float | None:
    if hours is not None:
        return round(float(hours), 2)
    if minutes is not None:
        return round(float(minutes) / 60.0, 2)
    return None


def _rating_value(raw) -> float | None:
    if raw is None:
        return None
    if isinstance(raw, dict):
        raw = raw.get("average") or raw.get("value")
    try:
        return float(raw)
    except (TypeError, ValueError):
        return None


def normalize_module(item: dict) -> dict:
    return build_row(
        source="ms_learn",
        external_id=item.get("uid"),
        url=item.get("url"),
        title=item.get("title") or "Untitled Module",
        description=clean_text(item.get("summary")),
        provider="Microsoft",
        school="Microsoft Learn",
        platform="Microsoft Learn",
        level=_normalize_level(item.get("levels")),
        topics=normalize_topics(item.get("subjects") or []) + normalize_topics(item.get("products") or []),
        subjects=normalize_topics(item.get("subjects") or []),
        tags=normalize_topics(item.get("roles") or []),
        format="module",
        modality="online",
        language=(item.get("locale") or "en").split("-")[0],
        duration_hours=_duration_hours(item.get("duration_in_minutes"), None),
        price_type="free",
        image_url=item.get("icon_url") or item.get("social_image_url"),
    )


def normalize_learning_path(item: dict) -> dict:
    return build_row(
        source="ms_learn",
        external_id=item.get("uid"),
        url=item.get("url"),
        title=item.get("title") or "Untitled Learning Path",
        description=clean_text(item.get("summary")),
        provider="Microsoft",
        school="Microsoft Learn",
        platform="Microsoft Learn",
        level=_normalize_level(item.get("levels")),
        topics=normalize_topics(item.get("subjects") or []) + normalize_topics(item.get("products") or []),
        subjects=normalize_topics(item.get("subjects") or []),
        tags=normalize_topics(item.get("roles") or []) + ["learning_path"],
        format="specialization",
        modality="online",
        language=(item.get("locale") or "en").split("-")[0],
        duration_hours=_duration_hours(item.get("duration_in_minutes"), None),
        rating=_rating_value(item.get("rating")),
        price_type="free",
        image_url=item.get("icon_url") or item.get("social_image_url"),
    )


def normalize_course(item: dict) -> dict:
    return build_row(
        source="ms_learn",
        external_id=item.get("uid"),
        url=item.get("url"),
        title=item.get("title") or "Untitled Course",
        description=clean_text(item.get("summary")),
        provider="Microsoft",
        school="Microsoft Learn",
        platform="Microsoft Learn",
        level=_normalize_level(item.get("levels")),
        topics=normalize_topics(item.get("products") or []),
        subjects=normalize_topics(item.get("products") or []),
        tags=normalize_topics(item.get("roles") or []) + ["instructor_led"],
        format="course",
        modality="online",
        language=(item.get("locales", ["en"])[0] if item.get("locales") else "en").split("-")[0],
        duration_hours=_duration_hours(None, item.get("duration_in_hours")),
        price_type="paid",  # instructor-led courses cost money
        image_url=item.get("icon_url"),
    )


def normalize_certification(item: dict) -> dict:
    return build_row(
        source="ms_learn",
        external_id=item.get("uid"),
        url=item.get("url"),
        title=item.get("title") or "Untitled Certification",
        description=clean_text(item.get("subtitle")),
        provider="Microsoft",
        school="Microsoft Learn",
        platform="Microsoft Learn",
        level=_normalize_level(item.get("levels")),
        subjects=[],
        tags=normalize_topics(item.get("roles") or []) + ["certification", item.get("certification_type") or ""],
        format="certification",
        modality="online",
        language="en",
        price_type="paid",
        certificate_available=True,
        image_url=item.get("icon_url"),
    )


def main():
    data = fetch_catalog()
    rows: list[dict] = []
    rows.extend(normalize_module(x) for x in data.get("modules", []) if x.get("url"))
    rows.extend(normalize_learning_path(x) for x in data.get("learningPaths", []) if x.get("url"))
    rows.extend(normalize_course(x) for x in data.get("courses", []) if x.get("url"))
    rows.extend(normalize_certification(x) for x in data.get("certifications", []) if x.get("url"))

    # dedupe by URL within this batch
    seen: set[str] = set()
    deduped: list[dict] = []
    for r in rows:
        if r["url"] in seen:
            continue
        seen.add(r["url"])
        deduped.append(r)

    print(f"[ms_learn] normalized {len(deduped)} rows (from {len(rows)} raw)")
    supabase = get_client()
    upserted, errors = upsert_courses(supabase, deduped, batch_size=100)
    print(f"[ms_learn] done: upserted={upserted}, errors={errors}")


if __name__ == "__main__":
    main()
