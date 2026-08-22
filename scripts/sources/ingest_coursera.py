#!/usr/bin/env python3
"""Ingest Coursera public catalog into the unified `courses` table.

Source: https://api.coursera.org/api/courses.v1  (no auth, paginated)
Yields ~23,500 courses across Stanford, Yale, Princeton, Google, IBM, etc.

Coursera courses are 'audit_free' (watch videos free, cert costs money).
We store audit-free for a11 auditable courses; freemium if uncertain.

Run:
  python scripts/sources/ingest_coursera.py
  python scripts/sources/ingest_coursera.py --limit 500   # test on 500
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import httpx

from sources.base import build_row, clean_text, get_client, map_level, upsert_courses

BASE_URL = "https://api.coursera.org/api/courses.v1"
COURSE_URL_TEMPLATE = "https://www.coursera.org/learn/{slug}"
PAGE_SIZE = 100
MAX_ITEMS = 30_000

FIELDS = (
    "description,partnerIds,workload,photoUrl,previewLink,specializations,"
    "courseType,domainTypes,startDate,certificates,primaryLanguages,subtitleLanguages"
)
INCLUDES = "partnerIds,specializations,domainTypes"


def infer_level_from_domain(domains: list) -> str:
    """Coursera doesn't ship an explicit level. Guess from domain hints in title/description caller."""
    return "intermediate"


def _partner_name(partner_ids: list[str], partners_by_id: dict[str, dict]) -> str | None:
    if not partner_ids:
        return None
    p = partners_by_id.get(str(partner_ids[0]))
    return (p or {}).get("name")


def _domains_to_topics(domain_types: list, sub_by_id: dict[str, dict], dom_by_id: dict[str, dict]) -> tuple[list[str], list[str]]:
    """Return (topics, subjects)."""
    topics = []
    subjects = []
    for d in domain_types or []:
        sub_id = d.get("subdomainId")
        dom_id = d.get("domainId")
        if sub_id and sub_id in sub_by_id:
            n = sub_by_id[sub_id].get("name")
            if n and n not in topics:
                topics.append(n)
        if dom_id and dom_id in dom_by_id:
            n = dom_by_id[dom_id].get("name")
            if n and n not in subjects:
                subjects.append(n)
    # collapse
    if not subjects and topics:
        subjects = topics[:2]
    return topics, subjects


def _workload_hours(workload: str | None) -> float | None:
    """Parse 'X hours Y minutes' or 'N-M hours a week'."""
    if not workload:
        return None
    import re
    hours = 0.0
    m = re.search(r"(\d+)\s*hour", workload.lower())
    if m:
        hours += float(m.group(1))
    m = re.search(r"(\d+)\s*min", workload.lower())
    if m:
        hours += float(m.group(1)) / 60
    return round(hours, 2) if hours else None


def _infer_level_from_slug(slug: str, name: str) -> str:
    s = (slug + " " + name).lower()
    if any(k in s for k in ["advanced", "expert", "capstone", "professional"]):
        return "advanced"
    if any(k in s for k in ["intro", "getting-started", "beginner", "basics", "fundamentals", "101"]):
        return "beginner"
    return "intermediate"


def normalize(item: dict, partners: dict[str, dict], subs: dict[str, dict], doms: dict[str, dict]) -> dict | None:
    slug = item.get("slug")
    name = item.get("name")
    if not slug or not name:
        return None

    url = COURSE_URL_TEMPLATE.format(slug=slug)
    partner_name = _partner_name(item.get("partnerIds") or [], partners)
    topics, subjects = _domains_to_topics(item.get("domainTypes") or [], subs, doms)

    duration_hours = _workload_hours(item.get("workload"))
    level = _infer_level_from_slug(slug, name)

    certificates = item.get("certificates") or []
    cert_available = any(c in ("VerifiedCert", "PaidCertificate", "Specialization", "Professional") for c in certificates)

    tags = []
    if item.get("courseType"):
        tags.append(item["courseType"])
    if item.get("specializations"):
        tags.append(f"in {len(item['specializations'])} specialization(s)")

    return build_row(
        source="coursera",
        external_id=item.get("id"),
        url=url,
        title=name,
        description=clean_text(item.get("description")),
        provider=partner_name or "Coursera Partner",
        school=partner_name,
        platform="Coursera",
        level=level,
        topics=topics,
        subjects=subjects,
        tags=tags,
        format="course",
        pace="self-paced",
        modality="online",
        language=(item.get("primaryLanguages") or ["en"])[0] if item.get("primaryLanguages") else "en",
        duration_hours=duration_hours,
        price_type="audit_free",   # Coursera default: watch videos free, cert paid
        certificate_available=cert_available,
        image_url=item.get("photoUrl"),
    )


def fetch_page(client: httpx.Client, start: int) -> dict:
    params = {
        "limit": PAGE_SIZE,
        "start": start,
        "fields": FIELDS,
        "includes": INCLUDES,
    }
    r = client.get(BASE_URL, params=params)
    r.raise_for_status()
    return r.json()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args()

    supabase = get_client()
    start = 0
    total_upserted = 0
    total_errors = 0
    ingested = 0

    with httpx.Client(timeout=45.0, headers={"User-Agent": "Mozilla/5.0"}) as client:
        while ingested < (args.limit or MAX_ITEMS):
            print(f"[coursera] fetching start={start} ...")
            try:
                data = fetch_page(client, start)
            except Exception as e:
                print(f"[coursera] fetch failed at start={start}: {e}")
                time.sleep(4)
                continue

            elements = data.get("elements") or []
            if not elements:
                print(f"[coursera] no more results at start={start}")
                break

            # index linked partners / subdomains / domains for THIS page
            linked = data.get("linked") or {}
            partners = {p["id"]: p for p in linked.get("partners.v1", []) if p.get("id")}
            subs = {s["id"]: s for s in linked.get("subdomains.v1", []) if s.get("id")}
            doms = {d["id"]: d for d in linked.get("domains.v1", []) if d.get("id")}

            rows = [n for n in (normalize(e, partners, subs, doms) for e in elements) if n]
            print(f"[coursera] normalized {len(rows)}/{len(elements)} rows (page start={start})")

            if rows:
                up, err = upsert_courses(supabase, rows, batch_size=100)
                total_upserted += up
                total_errors += err

            ingested += len(elements)
            paging = data.get("paging") or {}
            nxt = paging.get("next")
            if not nxt:
                print("[coursera] no next page")
                break
            try:
                start = int(nxt)
            except (TypeError, ValueError):
                break

            if args.limit and ingested >= args.limit:
                break
            time.sleep(0.3)

    print(f"[coursera] done: upserted={total_upserted}, errors={total_errors}")


if __name__ == "__main__":
    main()
