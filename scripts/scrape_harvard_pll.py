#!/usr/bin/env python3
"""
Harvard PLL Catalog Scraper (v2)
- Handles pagination (both free and paid catalogs)
- Exponential backoff + retry on failures / timeouts
- Direct writes to Supabase (harvard_pll_courses table)
- Resume-safe: skips URLs already in DB unless --refresh is passed
- Persistent checkpoint file so re-runs continue where they stopped

Run:
  python scripts/scrape_harvard_pll.py            # incremental
  python scripts/scrape_harvard_pll.py --refresh  # re-scrape everything
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import random
import re
import sys
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from urllib.parse import urljoin

import aiohttp
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from supabase import Client, create_client

# ----------------------------- config -----------------------------

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / "backend" / ".env")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE = os.getenv("SUPABASE_SERVICE_ROLE")

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE:
    print("ERROR: SUPABASE_URL and SUPABASE_SERVICE_ROLE must be set in backend/.env")
    sys.exit(1)

CHECKPOINT_FILE = Path(__file__).parent / ".harvard_pll_checkpoint.json"

BASE_URL = "https://pll.harvard.edu"

CATALOGS = [
    {
        "label": "free",
        "url_template": "https://pll.harvard.edu/catalog?price%5B1%5D=1&page={page}",
        "max_page": 4,  # inclusive, 0-indexed
    },
    {
        "label": "paid",
        "url_template": "https://pll.harvard.edu/catalog?price%5B2%5D=2&page={page}",
        "max_page": 13,
    },
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

MAX_CONCURRENCY = 6
BASE_DELAY = 0.4          # per-request pacing
FETCH_TIMEOUT = 45        # per HTTP request
MAX_RETRIES = 6           # per URL
INITIAL_BACKOFF = 5       # seconds
MAX_BACKOFF = 120         # cap
BATCH_UPSERT_SIZE = 25    # Supabase upsert batch

# ----------------------------- data model -----------------------------


@dataclass
class Course:
    title: str
    url: str
    price_type: str                     # "free" | "paid"
    provider: str = "Harvard University"
    school: Optional[str] = None
    description: Optional[str] = None
    duration: Optional[str] = None
    time_commitment: Optional[str] = None
    pace: Optional[str] = None
    modality: Optional[str] = None
    language: Optional[str] = None
    level: str = "intermediate"
    topics: list[str] = field(default_factory=list)
    subjects: list[str] = field(default_factory=list)
    platform: Optional[str] = None
    format: str = "course"
    source: str = "harvard_pll"
    price_amount: Optional[float] = None
    price_currency: str = "USD"
    certificate_price: Optional[float] = None
    image_url: Optional[str] = None
    scraped_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# ----------------------------- helpers -----------------------------


def _clean(txt: Optional[str]) -> Optional[str]:
    if not txt:
        return None
    txt = re.sub(r"^(Duration|Pace|Modality|Time Commitment|Language)\s*", "", txt, flags=re.I)
    txt = re.sub(r"\s+", " ", txt).strip()
    return txt or None


def _map_level(level: Optional[str]) -> str:
    if not level:
        return "intermediate"
    lv = level.lower()
    if lv in ("introductory", "beginner", "intro"):
        return "beginner"
    if lv in ("advanced", "expert"):
        return "advanced"
    return "intermediate"


def _first_text(soup: BeautifulSoup, selector: str) -> Optional[str]:
    node = soup.select_one(selector)
    return node.get_text(strip=True) if node else None


def _load_checkpoint() -> dict:
    if CHECKPOINT_FILE.exists():
        try:
            return json.loads(CHECKPOINT_FILE.read_text())
        except Exception:
            pass
    return {"completed_urls": [], "started_at": datetime.now(timezone.utc).isoformat()}


def _save_checkpoint(state: dict) -> None:
    CHECKPOINT_FILE.write_text(json.dumps(state, indent=2))


# ----------------------------- scraper -----------------------------


class HarvardPLLScraper:
    def __init__(self, supabase: Client, refresh: bool = False):
        self.supabase = supabase
        self.refresh = refresh
        self.sem = asyncio.Semaphore(MAX_CONCURRENCY)
        self.session: Optional[aiohttp.ClientSession] = None
        self.checkpoint = _load_checkpoint()
        self.completed: set[str] = set(self.checkpoint.get("completed_urls", []))
        self.pending_batch: list[dict] = []
        self.total_upserted = 0
        self.total_failed = 0

    async def __aenter__(self):
        timeout = aiohttp.ClientTimeout(total=FETCH_TIMEOUT, connect=15)
        connector = aiohttp.TCPConnector(limit=MAX_CONCURRENCY, ttl_dns_cache=300)
        self.session = aiohttp.ClientSession(timeout=timeout, connector=connector, headers=HEADERS)
        return self

    async def __aexit__(self, *_):
        if self.session:
            await self.session.close()

    # ---- fetch with retry + exponential backoff ----
    async def fetch(self, url: str) -> Optional[str]:
        backoff = INITIAL_BACKOFF
        for attempt in range(1, MAX_RETRIES + 1):
            async with self.sem:
                await asyncio.sleep(BASE_DELAY + random.uniform(0, 0.3))
                try:
                    async with self.session.get(url) as resp:
                        if resp.status == 200:
                            return await resp.text()
                        if resp.status in (429, 502, 503, 504):
                            body = await resp.text()
                            print(f"    ! {url} → HTTP {resp.status} (attempt {attempt}/{MAX_RETRIES}), sleeping {backoff}s")
                        else:
                            print(f"    ! {url} → HTTP {resp.status} (giving up)")
                            return None
                except (asyncio.TimeoutError, aiohttp.ClientError) as e:
                    print(f"    ! {url} → {type(e).__name__} (attempt {attempt}/{MAX_RETRIES}), sleeping {backoff}s")

            # sleep OUTSIDE the semaphore so we don't block other workers
            await asyncio.sleep(backoff + random.uniform(0, 2))
            backoff = min(backoff * 2, MAX_BACKOFF)
        print(f"    !! {url} → failed after {MAX_RETRIES} attempts")
        self.total_failed += 1
        return None

    # ---- extract course URLs from ANY catalog page ----
    def extract_course_urls(self, html: str) -> list[str]:
        soup = BeautifulSoup(html, "html.parser")
        urls: list[str] = []
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string or "")
            except (json.JSONDecodeError, AttributeError, TypeError):
                continue
            if isinstance(data, dict) and data.get("@type") == "ItemList":
                for item in data.get("itemListElement", []):
                    u = item.get("url")
                    if u:
                        urls.append(u)
        if not urls:
            for link in soup.find_all("a", href=True):
                href = link["href"]
                if "/course/" in href:
                    urls.append(urljoin(BASE_URL, href))
        # dedupe, keep order
        seen: set[str] = set()
        out: list[str] = []
        for u in urls:
            u = u.split("#")[0].rstrip("/")
            if u not in seen:
                seen.add(u)
                out.append(u)
        return out

    # ---- parse one course page ----
    def parse_course_page(self, html: str, url: str, price_label: str) -> Optional[Course]:
        soup = BeautifulSoup(html, "html.parser")

        course_ld: dict = {}
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string or "")
            except (json.JSONDecodeError, AttributeError, TypeError):
                continue
            if isinstance(data, dict) and data.get("@type") == "Course":
                course_ld = data
                break

        datalayer: dict = {}
        for script in soup.find_all("script"):
            txt = script.string or ""
            if "dataLayer.push" in txt and "page_data" in txt:
                m = re.search(r"dataLayer\.push\((\{.*?\})\);", txt, re.DOTALL)
                if m:
                    try:
                        dl = json.loads(m.group(1))
                        if "page_data" in dl and isinstance(dl["page_data"], dict):
                            datalayer = dl["page_data"]
                            break
                    except json.JSONDecodeError:
                        pass

        title = (
            course_ld.get("name")
            or datalayer.get("course_name")
            or _first_text(soup, "h1, .field--name-title")
            or "Unknown Course"
        )

        description = (
            course_ld.get("description")
            or _first_text(soup, ".field--name-field-summary")
            or _first_text(soup, ".field--name-body")
            or ""
        )

        provider_obj = course_ld.get("provider") if isinstance(course_ld.get("provider"), dict) else {}
        school = (
            datalayer.get("course_school")
            or datalayer.get("item_brand")
            or provider_obj.get("name")
            or _first_text(soup, ".field--name-field-schools a")
            or "Harvard University"
        )
        platform = (
            datalayer.get("course_platform")
            or provider_obj.get("name")
            or _first_text(soup, ".field--name-field-platform a")
            or "Harvard Online"
        )

        # pricing
        price_amount: Optional[float] = None
        if price_label == "paid":
            raw = (
                datalayer.get("course_price")
                or datalayer.get("price")
                or (course_ld.get("offers", {}) or {}).get("price")
            )
            try:
                if raw not in (None, ""):
                    price_amount = float(raw)
            except (TypeError, ValueError):
                price_amount = None

        cert_price: Optional[float] = None
        raw = datalayer.get("course_certificate_price")
        try:
            if raw not in (None, "", 0, "0"):
                cert_price = float(raw)
        except (TypeError, ValueError):
            cert_price = None
        if cert_price is None:
            node = soup.select_one(".field---extra-field-pll-extra-field-course-credit")
            if node:
                m = re.search(r"\$([\d,]+)", node.get_text())
                if m:
                    cert_price = float(m.group(1).replace(",", ""))

        level = _map_level(
            datalayer.get("course_difficulty")
            or _first_text(soup, ".field--name-field-difficulty")
        )

        duration = _clean(
            datalayer.get("course_length")
            or _first_text(soup, ".field---extra-field-pll-extra-field-duration")
        )
        time_commitment = _clean(_first_text(soup, ".field---extra-field-pll-extra-field-time-commitment"))
        pace = _clean(datalayer.get("course_pace") or _first_text(soup, ".field--name-field-pace"))
        modality = _clean(datalayer.get("course_modality") or _first_text(soup, ".field--name-field-modality"))
        language = _clean(datalayer.get("course_language") or _first_text(soup, ".field--name-field-course-language"))

        topics: list[str] = []
        for k in ("item_category", "item_category2"):
            v = datalayer.get(k)
            if v and v not in topics:
                topics.append(v)
        cat = course_ld.get("category")
        if isinstance(cat, str) and cat and cat not in topics:
            topics.append(cat)
        for a in soup.select(".field--name-field-topics a, .field---extra-field-pll-extra-field-subject a"):
            t = a.get_text(strip=True)
            if t and t not in topics:
                topics.append(t)

        image_url = None
        if isinstance(course_ld.get("image"), str):
            image_url = course_ld["image"]
        else:
            img = soup.select_one(".field--name-field-media-image img")
            if img and img.get("src"):
                image_url = urljoin(BASE_URL, img["src"])

        return Course(
            title=title,
            url=url,
            price_type=price_label,
            provider="Harvard University",
            school=school,
            description=description,
            duration=duration,
            time_commitment=time_commitment,
            pace=pace,
            modality=modality,
            language=language,
            level=level,
            topics=topics,
            subjects=topics.copy(),
            platform=platform,
            price_amount=price_amount,
            price_currency="USD",
            certificate_price=cert_price,
            image_url=image_url,
        )

    # ---- Supabase upsert with retry ----
    async def flush_batch(self, force: bool = False):
        if not self.pending_batch:
            return
        if not force and len(self.pending_batch) < BATCH_UPSERT_SIZE:
            return
        batch = self.pending_batch[:]
        self.pending_batch.clear()

        backoff = INITIAL_BACKOFF
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                # supabase-py is sync; run in a thread
                await asyncio.to_thread(
                    lambda: self.supabase.table("harvard_pll_courses").upsert(
                        batch, on_conflict="url"
                    ).execute()
                )
                self.total_upserted += len(batch)
                for c in batch:
                    self.completed.add(c["url"])
                self.checkpoint["completed_urls"] = sorted(self.completed)
                _save_checkpoint(self.checkpoint)
                print(f"    ↑ upserted {len(batch)} rows (total {self.total_upserted})")
                return
            except Exception as e:
                msg = str(e)
                is_timeout = "timeout" in msg.lower() or "504" in msg or "Upstream" in msg
                print(f"    ! Supabase upsert failed (attempt {attempt}/{MAX_RETRIES}): {msg[:200]}")
                if not is_timeout and attempt >= 3:
                    break
                await asyncio.sleep(backoff + random.uniform(0, 3))
                backoff = min(backoff * 2, MAX_BACKOFF)
        # if we get here, keep them in-memory so they aren't lost
        self.pending_batch.extend(batch)
        print(f"    !! upsert giving up temporarily; {len(self.pending_batch)} rows queued")

    async def enqueue(self, course: Course):
        self.pending_batch.append(asdict(course))
        await self.flush_batch(force=False)

    # ---- catalog page → list of course URLs ----
    async def collect_course_urls(self) -> list[tuple[str, str]]:
        """Returns list of (url, price_label). Deduped."""
        by_url: dict[str, str] = {}
        for cat in CATALOGS:
            for page in range(cat["max_page"] + 1):
                cat_url = cat["url_template"].format(page=page)
                print(f"→ catalog {cat['label']} page {page}: {cat_url}")
                html = await self.fetch(cat_url)
                if not html:
                    continue
                urls = self.extract_course_urls(html)
                print(f"    found {len(urls)} URLs")
                for u in urls:
                    by_url.setdefault(u, cat["label"])  # first wins
        return list(by_url.items())

    async def scrape_course(self, url: str, price_label: str):
        if not self.refresh and url in self.completed:
            return
        html = await self.fetch(url)
        if not html:
            return
        try:
            course = self.parse_course_page(html, url, price_label)
        except Exception as e:
            print(f"    ! parse failed for {url}: {e}")
            return
        if course:
            await self.enqueue(course)

    async def run(self):
        pairs = await self.collect_course_urls()
        print(f"\nTotal unique course URLs discovered: {len(pairs)}")
        skipped = sum(1 for u, _ in pairs if not self.refresh and u in self.completed)
        remaining = [(u, l) for u, l in pairs if self.refresh or u not in self.completed]
        print(f"  Already in DB (skipping): {skipped}")
        print(f"  To scrape:                {len(remaining)}\n")

        # gather with concurrency handled by semaphore inside fetch
        tasks = [self.scrape_course(u, l) for u, l in remaining]
        # process in windows so we can flush + save checkpoint periodically
        WINDOW = 30
        for i in range(0, len(tasks), WINDOW):
            chunk = tasks[i:i + WINDOW]
            await asyncio.gather(*chunk)
            await self.flush_batch(force=True)
            print(f"    [progress] {min(i + WINDOW, len(tasks))}/{len(tasks)} attempted, {self.total_upserted} upserted so far")

        await self.flush_batch(force=True)
        print(f"\nDone. Upserted: {self.total_upserted}, failed fetches: {self.total_failed}")


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--refresh", action="store_true", help="Re-scrape URLs already in DB")
    parser.add_argument("--reset-checkpoint", action="store_true", help="Clear local checkpoint file")
    args = parser.parse_args()

    if args.reset_checkpoint and CHECKPOINT_FILE.exists():
        CHECKPOINT_FILE.unlink()
        print("Cleared checkpoint.")

    supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE)

    async with HarvardPLLScraper(supabase, refresh=args.refresh) as scraper:
        await scraper.run()


if __name__ == "__main__":
    asyncio.run(main())
