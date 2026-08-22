#!/usr/bin/env python3
"""Ingest NUSMods (National University of Singapore) modules into unified `courses` table.

Source: https://api.nusmods.com/v2/{acadYear}/moduleInfo.json  (no auth, single dump)
Yields ~16,000 modules with descriptions, credits, department, workload.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import httpx

from sources.base import build_row, clean_text, get_client, map_level, upsert_courses

ACAD_YEAR = "2024-2025"
BULK_URL = f"https://api.nusmods.com/v2/{ACAD_YEAR}/moduleInfo.json"
MODULE_URL_TEMPLATE = "https://nusmods.com/modules/{code}"


def infer_level(module_code: str) -> str:
    """NUS codes: XX1000 = beginner, XX2000 = intermediate, XX3000+/XX4000+ = advanced, XX5000+/XX6000+ = graduate."""
    import re
    m = re.search(r"(\d)", module_code)
    if not m:
        return "intermediate"
    digit = int(m.group(1))
    if digit <= 2:
        return "beginner"
    if digit <= 3:
        return "intermediate"
    return "advanced"


def infer_subjects(department: str, faculty: str) -> list[str]:
    """Map NUS departments to broad subject tags."""
    d = (department or "").lower()
    f = (faculty or "").lower()
    subjects = []
    if "computer" in d or "computing" in f:
        subjects.append("computer science")
    if "mathematics" in d or "math" in d:
        subjects.append("mathematics")
    if "statistics" in d:
        subjects.append("statistics")
    if "business" in f or "management" in d:
        subjects.append("business")
    if "engineering" in f:
        subjects.append("engineering")
    if "medicine" in f or "biology" in d or "biomedical" in d:
        subjects.append("life sciences")
    if "econom" in d:
        subjects.append("economics")
    if "physics" in d:
        subjects.append("physics")
    if "chemistry" in d:
        subjects.append("chemistry")
    if "art" in f or "humanities" in f:
        subjects.append("humanities")
    if "law" in f:
        subjects.append("law")
    if "design" in d or "architecture" in f:
        subjects.append("design")
    if not subjects:
        subjects = [department.lower()] if department else ["general"]
    return subjects


def _workload_hours(workload) -> float | None:
    """NUS workload is [lecture, tutorial, lab, project, preparation] hrs/week."""
    if not workload or not isinstance(workload, list):
        return None
    try:
        weekly = sum(float(x) for x in workload if x is not None)
        # Assume 13-week semester
        return round(weekly * 13, 1) if weekly > 0 else None
    except (TypeError, ValueError):
        return None


def normalize(item: dict) -> dict | None:
    code = item.get("moduleCode")
    title = item.get("title")
    if not code or not title:
        return None

    url = MODULE_URL_TEMPLATE.format(code=code)
    department = item.get("department") or ""
    faculty = item.get("faculty") or ""
    subjects = infer_subjects(department, faculty)

    topics = subjects.copy()
    if department and department.lower() not in [t.lower() for t in topics]:
        topics.append(department)

    return build_row(
        source="nusmods",
        external_id=code,
        url=url,
        title=title,
        description=clean_text(item.get("description")),
        provider="National University of Singapore",
        school=faculty or "NUS",
        platform="NUSMods",
        level=infer_level(code),
        topics=topics,
        subjects=subjects,
        tags=[department] if department else [],
        format="course",
        pace="fixed-schedule",
        modality="in-person",
        language="en",
        duration_hours=_workload_hours(item.get("workload")),
        weeks=13,
        price_type="paid",  # university tuition
    )


def main():
    print(f"[nusmods] fetching {BULK_URL} ...")
    with httpx.Client(timeout=60.0, headers={"User-Agent": "Mozilla/5.0"}) as client:
        r = client.get(BULK_URL)
        r.raise_for_status()
        modules = r.json()

    print(f"[nusmods] {len(modules)} raw modules")

    rows: list[dict] = []
    for m in modules:
        row = normalize(m)
        if row:
            rows.append(row)
    print(f"[nusmods] normalized {len(rows)} rows")

    supabase = get_client()
    upserted, errors = upsert_courses(supabase, rows, batch_size=100)
    print(f"[nusmods] done: upserted={upserted}, errors={errors}")


if __name__ == "__main__":
    main()
