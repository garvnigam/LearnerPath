#!/usr/bin/env python3
"""Populate `courses.embedding` (vector 1536) using Azure OpenAI text-embedding-3-small.

Cost: ~$0.02 per 1M input tokens → ~$0.30 for the 24k catalog.
Time: ~15-25 min at 32 concurrent, batched 100 inputs per API call.

Run:
  python scripts/enrich_embeddings.py                  # embed rows missing an embedding
  python scripts/enrich_embeddings.py --refresh        # re-embed all rows
  python scripts/enrich_embeddings.py --limit 100      # test on 100 rows
"""
from __future__ import annotations

import argparse
import asyncio
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
AZURE_OPENAI_ENDPOINT = "https://learnerpathmodels.openai.azure.com"
AZURE_OPENAI_KEY = os.getenv("AZURE_OPENAI_KEY")
EMBED_DEPLOYMENT = os.getenv("AZURE_OPENAI_EMBED_DEPLOYMENT", "text-embedding-3-small")
API_VERSION = "2024-08-01-preview"

if not (SUPABASE_URL and SUPABASE_SERVICE_ROLE and AZURE_OPENAI_KEY):
    print("ERROR: SUPABASE_URL, SUPABASE_SERVICE_ROLE, AZURE_OPENAI_KEY must be set")
    sys.exit(1)


@dataclass
class Row:
    id: str
    text: str


BATCH_INPUTS = 100          # inputs per API call (Azure limit ~2048; 100 is fast & safe)
CONCURRENCY = 8             # parallel API calls
MAX_RETRIES = 5
MAX_TEXT_LEN = 4000         # trim before embedding to keep tokens low


def build_text(row: dict) -> str:
    parts = [row.get("title") or ""]
    topics = row.get("topics") or []
    concepts = row.get("concepts") or []
    subjects = row.get("subjects") or []
    if row.get("description"):
        parts.append(row["description"])
    if topics:
        parts.append("Topics: " + ", ".join(topics))
    if concepts:
        parts.append("Concepts: " + ", ".join(concepts))
    if subjects:
        parts.append("Subjects: " + ", ".join(subjects))
    text = ". ".join(p for p in parts if p)
    return text[:MAX_TEXT_LEN]


async def embed_batch(client: httpx.AsyncClient, sem: asyncio.Semaphore, rows: list[Row]) -> list[tuple[str, list[float]]] | None:
    url = f"{AZURE_OPENAI_ENDPOINT}/openai/deployments/{EMBED_DEPLOYMENT}/embeddings?api-version={API_VERSION}"
    body = {"input": [r.text for r in rows]}

    backoff = 2.0
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            async with sem:
                r = await client.post(
                    url,
                    headers={"api-key": AZURE_OPENAI_KEY, "Content-Type": "application/json"},
                    json=body,
                    timeout=60,
                )
            if r.status_code == 429:
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 60)
                continue
            if r.status_code != 200:
                if attempt >= MAX_RETRIES:
                    print(f"    ! HTTP {r.status_code}: {r.text[:160]}")
                    return None
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 60)
                continue
            data = r.json()["data"]
            return [(rows[i].id, data[i]["embedding"]) for i in range(len(rows))]
        except httpx.HTTPError as e:
            if attempt >= MAX_RETRIES:
                print(f"    ! {type(e).__name__}: {str(e)[:160]}")
                return None
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, 60)
    return None


def upsert_embeddings(supabase, updates: list[tuple[str, list[float]]]) -> int:
    ok = 0
    for row_id, vec in updates:
        try:
            supabase.table("courses").update({"embedding": vec}).eq("id", row_id).execute()
            ok += 1
        except Exception as e:
            print(f"    ! upsert {row_id[:8]}: {str(e)[:120]}")
    return ok


def fetch_rows(supabase, refresh: bool, limit: int | None) -> list[Row]:
    all_rows: list[Row] = []
    page = 0
    page_size = 500

    while True:
        q = supabase.table("courses").select(
            "id,title,description,topics,concepts,subjects,embedding"
        )
        q = q.range(page * page_size, (page + 1) * page_size - 1)
        data = q.execute().data or []
        if not data:
            break
        for d in data:
            if not refresh and d.get("embedding") is not None:
                continue
            text = build_text(d)
            if not text.strip():
                continue
            all_rows.append(Row(id=d["id"], text=text))
            if limit and len(all_rows) >= limit:
                return all_rows
        if len(data) < page_size:
            break
        page += 1
    return all_rows


async def main_async(refresh: bool, limit: int | None):
    supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE)
    rows = fetch_rows(supabase, refresh=refresh, limit=limit)
    print(f"[embeddings] {len(rows)} rows to embed")
    if not rows:
        return

    total_ok = 0
    start = time.time()
    sem = asyncio.Semaphore(CONCURRENCY)

    async with httpx.AsyncClient() as client:
        i = 0
        while i < len(rows):
            # Build up to CONCURRENCY batches at once
            windows = []
            while len(windows) < CONCURRENCY and i < len(rows):
                windows.append(rows[i : i + BATCH_INPUTS])
                i += BATCH_INPUTS

            results = await asyncio.gather(*[embed_batch(client, sem, w) for w in windows])
            for res in results:
                if not res:
                    continue
                ok = upsert_embeddings(supabase, res)
                total_ok += ok

            done = min(i, len(rows))
            elapsed = time.time() - start
            rate = done / elapsed if elapsed else 0
            eta = (len(rows) - done) / rate if rate else 0
            print(f"    [{done:>5}/{len(rows)}] total {total_ok}  |  {rate:.1f} rows/s  |  ETA {eta/60:.1f} min")

    print(f"[embeddings] done: embedded {total_ok}/{len(rows)}")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--refresh", action="store_true")
    p.add_argument("--limit", type=int, default=None)
    args = p.parse_args()
    asyncio.run(main_async(refresh=args.refresh, limit=args.limit))


if __name__ == "__main__":
    main()
