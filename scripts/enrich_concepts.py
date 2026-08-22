#!/usr/bin/env python3
"""Enrich `courses` rows with `concepts` and `prerequisite_concepts` using
the existing Azure OpenAI chat deployment (gpt-4.1-mini).

Cost: ~$0.00015 per course with gpt-4.1-mini → ~$4 for 25k rows.
Time: ~2 hours at 20 req/sec with async batching.

Run:
  python scripts/enrich_concepts.py                  # tag rows missing concepts
  python scripts/enrich_concepts.py --refresh        # re-tag everything
  python scripts/enrich_concepts.py --limit 100      # test on 100 rows
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import httpx
from dotenv import load_dotenv
from supabase import create_client

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / "backend" / ".env")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE = os.getenv("SUPABASE_SERVICE_ROLE")
AZURE_OPENAI_ENDPOINT = "https://learnerpathmodels.openai.azure.com"  # bare resource URL (Foundry proj URL doesn't work for /openai/*)
AZURE_OPENAI_KEY = os.getenv("AZURE_OPENAI_KEY")
CHAT_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4.1-mini")
API_VERSION = "2024-08-01-preview"

if not (SUPABASE_URL and SUPABASE_SERVICE_ROLE and AZURE_OPENAI_KEY):
    print("ERROR: SUPABASE_URL, SUPABASE_SERVICE_ROLE, AZURE_OPENAI_KEY must be set")
    sys.exit(1)


SYSTEM_PROMPT = """You are an expert curriculum analyst.
Given a course's title, description, topics and level, extract:

1. "concepts": 3-8 CONCRETE skills or topics the course teaches (short lowercase phrases, e.g. "backpropagation", "recursion", "sql joins", "financial statements", "gradient descent"). No generic filler like "programming" or "computer science" — pick specifics.
2. "prerequisite_concepts": 0-5 concrete skills a learner should ideally have before starting (same style, may be empty for absolute beginner content).

Rules:
- Both arrays are lowercase, hyphen or space allowed, no periods.
- Skills only, not course names or vendors.
- Return STRICT JSON: {"concepts": [...], "prerequisite_concepts": [...]}
- If the input is too vague to judge, return {"concepts": [], "prerequisite_concepts": []}.
"""


@dataclass
class Row:
    id: str
    title: str
    description: str | None
    topics: list[str]
    level: str


CONCURRENCY = 12
MAX_RETRIES = 5


async def tag_one(client: httpx.AsyncClient, sem: asyncio.Semaphore, row: Row) -> tuple[str, dict] | None:
    user_prompt = json.dumps({
        "title": row.title,
        "level": row.level,
        "topics": row.topics[:10],
        "description": (row.description or "")[:1200],
    })

    url = f"{AZURE_OPENAI_ENDPOINT}/openai/deployments/{CHAT_DEPLOYMENT}/chat/completions?api-version={API_VERSION}"
    body = {
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
        "max_tokens": 300,
    }

    backoff = 2.0
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            async with sem:
                r = await client.post(
                    url,
                    headers={"api-key": AZURE_OPENAI_KEY, "Content-Type": "application/json"},
                    json=body,
                    timeout=30,
                )
            if r.status_code == 429:
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 30)
                continue
            if r.status_code != 200:
                if attempt >= MAX_RETRIES:
                    print(f"    ! {row.id[:8]}: HTTP {r.status_code} {r.text[:120]}")
                    return None
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 30)
                continue
            content = r.json()["choices"][0]["message"]["content"]
            data = json.loads(content)
            concepts = [str(c).strip().lower() for c in (data.get("concepts") or []) if c]
            prereqs = [str(c).strip().lower() for c in (data.get("prerequisite_concepts") or []) if c]
            return row.id, {"concepts": concepts[:8], "prerequisite_concepts": prereqs[:5]}
        except (httpx.HTTPError, json.JSONDecodeError, KeyError) as e:
            if attempt >= MAX_RETRIES:
                print(f"    ! {row.id[:8]}: {type(e).__name__} {str(e)[:120]}")
                return None
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, 30)
    return None


async def process_batch(rows: list[Row]) -> list[tuple[str, dict]]:
    sem = asyncio.Semaphore(CONCURRENCY)
    async with httpx.AsyncClient() as client:
        tasks = [tag_one(client, sem, r) for r in rows]
        results = await asyncio.gather(*tasks)
    return [r for r in results if r]


def upsert_concepts(supabase, updates: list[tuple[str, dict]]) -> int:
    """Update rows one at a time (Supabase REST doesn't support bulk update on different values)."""
    ok = 0
    for row_id, payload in updates:
        try:
            supabase.table("courses").update(payload).eq("id", row_id).execute()
            ok += 1
        except Exception as e:
            print(f"    ! upsert {row_id[:8]}: {e}")
    return ok


def fetch_rows(supabase, refresh: bool, limit: int | None) -> list[Row]:
    """Fetch rows that need tagging. Deduplicates by id in case of page overlap."""
    all_rows: list[Row] = []
    seen_ids: set[str] = set()
    page = 0
    page_size = 1000  # Supabase max per query

    while True:
        q = supabase.table("courses").select("id,title,description,topics,level")
        if not refresh:
            q = q.eq("concepts", "{}")
        # order by id for stable pagination
        q = q.order("id").range(page * page_size, (page + 1) * page_size - 1)
        data = q.execute().data or []
        if not data:
            break
        added = 0
        for d in data:
            if d["id"] in seen_ids:
                continue
            seen_ids.add(d["id"])
            all_rows.append(Row(
                id=d["id"],
                title=d["title"],
                description=d.get("description"),
                topics=d.get("topics") or [],
                level=d.get("level") or "intermediate",
            ))
            added += 1
            if limit and len(all_rows) >= limit:
                return all_rows
        if added == 0 or len(data) < page_size:
            break
        page += 1
    return all_rows


async def main_async(refresh: bool, limit: int | None):
    supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE)
    rows = fetch_rows(supabase, refresh=refresh, limit=limit)
    print(f"[concepts] {len(rows)} rows need tagging")
    if not rows:
        return

    BATCH = 60  # requests in flight per Supabase upsert window
    total_ok = 0
    start = time.time()
    for i in range(0, len(rows), BATCH):
        chunk = rows[i : i + BATCH]
        results = await process_batch(chunk)
        ok = upsert_concepts(supabase, results)
        total_ok += ok
        done = i + len(chunk)
        elapsed = time.time() - start
        rate = done / elapsed if elapsed else 0
        eta = (len(rows) - done) / rate if rate else 0
        print(f"    [{done:>5}/{len(rows)}] +{ok} tagged this batch  |  total {total_ok}  |  {rate:.1f} rows/s  |  ETA {eta/60:.1f} min")

    print(f"[concepts] done: tagged {total_ok}/{len(rows)}")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--refresh", action="store_true", help="Re-tag rows even if concepts already set")
    p.add_argument("--limit", type=int, default=None, help="Test on N rows")
    args = p.parse_args()
    asyncio.run(main_async(refresh=args.refresh, limit=args.limit))


if __name__ == "__main__":
    main()
