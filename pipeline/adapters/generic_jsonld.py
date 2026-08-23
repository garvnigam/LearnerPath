"""Generic JSON-LD scraper.

For catalog sites where courses are HTML pages embedding schema.org/Course JSON-LD
(Harvard PLL, Stanford Online, Yale, Kaggle Learn, freeCodeCamp, etc.). Given a
listing URL, this discovers course URLs, fetches each page, and normalizes the
embedded schema.org data into the unified `courses` schema.
"""
from __future__ import annotations

import asyncio
import json
import random
import re
import sys
from pathlib import Path
from typing import Optional
from urllib.parse import urljoin, urlparse

import aiohttp
from bs4 import BeautifulSoup

# Reuse shared helpers under scripts/sources/
_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(_ROOT / "scripts"))

from sources.base import build_row, clean_text, map_level, map_price_type, normalize_topics  # noqa: E402


UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/605.1.15"
HEADERS = {"User-Agent": UA, "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9"}
MAX_RETRIES = 5
INITIAL_BACKOFF = 4
MAX_BACKOFF = 60


async def _fetch(session: aiohttp.ClientSession, url: str, sem: asyncio.Semaphore) -> Optional[str]:
    backoff = INITIAL_BACKOFF
    for attempt in range(1, MAX_RETRIES + 1):
        async with sem:
            await asyncio.sleep(0.2 + random.uniform(0, 0.3))
            try:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=45)) as r:
                    if r.status == 200:
                        return await r.text()
                    if r.status in (429, 502, 503, 504):
                        print(f"    ! {url} → HTTP {r.status} (retry {attempt})")
                    else:
                        print(f"    ! {url} → HTTP {r.status} (skip)")
                        return None
            except (asyncio.TimeoutError, aiohttp.ClientError) as e:
                print(f"    ! {url} → {type(e).__name__} (retry {attempt})")

        await asyncio.sleep(backoff + random.uniform(0, 2))
        backoff = min(backoff * 2, MAX_BACKOFF)
    return None


def _extract_course_urls(html: str, base_url: str, url_pattern: str = "/course") -> list[str]:
    """Find course-detail URLs on a listing page.

    Strategy: pull URLs from any <script type='application/ld+json'> that contains an
    ItemList; fall back to <a href> filtering by url_pattern (default '/course').
    """
    soup = BeautifulSoup(html, "html.parser")
    urls: list[str] = []

    # JSON-LD ItemList
    for tag in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(tag.string or "")
        except (json.JSONDecodeError, AttributeError, TypeError):
            continue
        candidates = data if isinstance(data, list) else [data]
        for entry in candidates:
            if not isinstance(entry, dict):
                continue
            if entry.get("@type") == "ItemList":
                for item in entry.get("itemListElement", []) or []:
                    if isinstance(item, dict):
                        u = item.get("url") or (item.get("item") or {}).get("url")
                        if u:
                            urls.append(u)

    if not urls:
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if url_pattern in href:
                urls.append(urljoin(base_url, href))

    seen: set[str] = set()
    dedup: list[str] = []
    for u in urls:
        u = u.split("#")[0].rstrip("/")
        if u not in seen:
            seen.add(u)
            dedup.append(u)
    return dedup


def _find_course_jsonld(html: str) -> Optional[dict]:
    """Return the first schema.org/Course JSON-LD block from a page, or None."""
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(tag.string or "")
        except (json.JSONDecodeError, AttributeError, TypeError):
            continue
        entries = data if isinstance(data, list) else [data]
        for e in entries:
            if isinstance(e, dict) and (e.get("@type") == "Course" or "Course" in (e.get("@type") or [])):
                return e
    return None


def _price_from_offers(offers) -> tuple[str, float | None]:
    """Extract (price_type, price_amount) from a schema.org offers block."""
    if not offers:
        return "free", None
    first = offers[0] if isinstance(offers, list) else offers
    if isinstance(first, dict):
        price = first.get("price")
        try:
            amount = float(price) if price not in (None, "", "0", "0.00") else None
        except (TypeError, ValueError):
            amount = None
        if amount is None or amount == 0:
            return "free", None
        return "paid", amount
    return "free", None


def _normalize_jsonld_course(course_ld: dict, page_url: str, source: str) -> Optional[dict]:
    title = course_ld.get("name")
    if not title:
        return None

    provider = course_ld.get("provider") or {}
    if isinstance(provider, list):
        provider = provider[0] if provider else {}
    provider_name = provider.get("name") if isinstance(provider, dict) else None

    topics = []
    if course_ld.get("about"):
        about = course_ld["about"]
        if isinstance(about, list):
            topics = normalize_topics(about)
        else:
            topics = normalize_topics([about])
    if course_ld.get("keywords"):
        topics += normalize_topics(re.split(r"[,;]", str(course_ld["keywords"])))
    topics = list(dict.fromkeys(t for t in topics if t))

    level = "intermediate"
    if course_ld.get("educationalLevel"):
        level = map_level(course_ld["educationalLevel"])

    duration = None
    if course_ld.get("timeRequired"):
        # ISO-8601 duration: PT10H, P4W, etc.
        m = re.search(r"(\d+)\s*H", str(course_ld["timeRequired"]))
        if m:
            duration = float(m.group(1))
        else:
            wm = re.search(r"(\d+)\s*W", str(course_ld["timeRequired"]))
            if wm:
                duration = float(wm.group(1)) * 4  # rough

    price_type, price_amount = _price_from_offers(course_ld.get("offers"))

    image_url = None
    img = course_ld.get("image")
    if isinstance(img, str):
        image_url = img
    elif isinstance(img, dict):
        image_url = img.get("url")

    return build_row(
        source=source,
        external_id=None,
        url=page_url,
        title=clean_text(title, max_len=500) or "Untitled",
        description=clean_text(course_ld.get("description")),
        provider=provider_name or source,
        school=provider_name or "",
        platform=source,
        level=level,
        topics=topics,
        subjects=topics[:3],
        format="course",
        pace=course_ld.get("coursePrerequisites") and "self-paced" or None,
        modality="online",
        language=(course_ld.get("inLanguage") or "en")[:5] if isinstance(course_ld.get("inLanguage"), str) else "en",
        duration_hours=duration,
        price_type=price_type,
        price_amount=price_amount,
        image_url=image_url,
    )


async def scrape_jsonld_site(
    listing_url: str,
    *,
    source: str,
    url_pattern: str = "/course",
    max_concurrent: int = 6,
    max_pages: int = 40,
    page_query: str = "page",
) -> list[dict]:
    """Scrape a catalog site: paginate listing pages, fetch each course page, parse JSON-LD."""
    base_url = f"{urlparse(listing_url).scheme}://{urlparse(listing_url).netloc}"
    sem = asyncio.Semaphore(max_concurrent)
    connector = aiohttp.TCPConnector(limit=max_concurrent, ttl_dns_cache=300)

    async with aiohttp.ClientSession(headers=HEADERS, connector=connector) as session:
        # 1. discover course URLs across listing pages
        all_course_urls: set[str] = set()
        for pg in range(max_pages):
            sep = "&" if "?" in listing_url else "?"
            page_url = listing_url if pg == 0 else f"{listing_url}{sep}{page_query}={pg}"
            print(f"[jsonld] listing page {pg}: {page_url}")
            html = await _fetch(session, page_url, sem)
            if not html:
                break
            urls = _extract_course_urls(html, base_url, url_pattern=url_pattern)
            new = [u for u in urls if u not in all_course_urls]
            if not new and pg > 0:
                print(f"[jsonld] no new URLs → stopping pagination at page {pg}")
                break
            all_course_urls.update(urls)
            print(f"[jsonld]   +{len(new)} new  total {len(all_course_urls)}")

        print(f"[jsonld] {len(all_course_urls)} unique course URLs to fetch")

        # 2. fetch each course page in parallel and parse JSON-LD
        async def _one(u: str) -> Optional[dict]:
            html = await _fetch(session, u, sem)
            if not html:
                return None
            ld = _find_course_jsonld(html)
            if not ld:
                return None
            try:
                return _normalize_jsonld_course(ld, u, source)
            except Exception as e:
                print(f"    ! parse {u}: {e}")
                return None

        tasks = [_one(u) for u in sorted(all_course_urls)]
        rows: list[dict] = []
        for i in range(0, len(tasks), 30):
            chunk = tasks[i:i + 30]
            results = await asyncio.gather(*chunk, return_exceptions=True)
            for r in results:
                if isinstance(r, Exception):
                    continue
                if r:
                    rows.append(r)
            print(f"[jsonld] {min(i + 30, len(tasks))}/{len(tasks)} pages processed, {len(rows)} valid rows")

    return rows
