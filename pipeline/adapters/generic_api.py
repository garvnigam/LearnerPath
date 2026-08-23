"""Generic JSON-API ingestor helpers.

Adapts an arbitrary paginated REST API into the unified `courses` schema without
writing per-source normalizers. Given a URL, item path (JSONPath-lite), and a
key-mapping dict, this can ingest ~any catalog that returns JSON.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Any, Optional

import httpx

# Reuse the existing shared helpers under scripts/sources/ so all ingestors —
# per-source and generic — go through the same upsert/normalize path.
_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(_ROOT / "scripts"))

from sources.base import build_row, clean_text, map_level, map_price_type, normalize_topics  # noqa: E402


def _dig(obj: Any, path: str) -> Any:
    """Follow a dotted path into nested dicts/lists.

    Supports: 'results', 'data.items', 'response.0.courses'.
    Returns None if the path doesn't exist.
    """
    if not path:
        return obj
    cur = obj
    for part in path.split("."):
        if cur is None:
            return None
        if part.isdigit() and isinstance(cur, list):
            i = int(part)
            cur = cur[i] if i < len(cur) else None
        elif isinstance(cur, dict):
            cur = cur.get(part)
        else:
            return None
    return cur


def normalize_item_generic(
    item: dict,
    *,
    source: str,
    mapping: dict[str, str | list[str]],
    provider_default: str = "",
    level_default: str = "intermediate",
    price_type_default: str = "free",
    format_default: str = "course",
) -> Optional[dict]:
    """Turn a raw API item into a `courses`-row dict using a key-mapping.

    mapping is a dict of unified-schema-column -> raw-item-key (dotted path). A
    list of paths means "first non-null wins". Example:
        {
          "title": "name",
          "description": ["summary", "description"],
          "url": "canonical_url",
          "level": "difficulty",
          "topics": "subjects.name",   # list-of-dicts flattened
          "price_type": "pricing.tier",
          "image_url": "image.url",
        }
    """
    def get(field: str):
        spec = mapping.get(field)
        if not spec:
            return None
        keys = spec if isinstance(spec, list) else [spec]
        for k in keys:
            v = _dig(item, k)
            if v not in (None, "", []):
                return v
        return None

    url = get("url")
    title = get("title")
    if not url or not title:
        return None

    topics_raw = get("topics") or []
    if isinstance(topics_raw, dict):
        topics_raw = [topics_raw]
    if not isinstance(topics_raw, list):
        topics_raw = [str(topics_raw)]

    subjects_raw = get("subjects") or topics_raw

    return build_row(
        source=source,
        external_id=str(get("external_id") or item.get("id") or "") or None,
        url=str(url),
        title=str(title)[:500],
        description=clean_text(get("description")),
        provider=str(get("provider") or provider_default or source),
        school=str(get("school") or ""),
        platform=str(get("platform") or provider_default or source),
        level=map_level(get("level")) if get("level") else level_default,
        topics=normalize_topics(topics_raw),
        subjects=normalize_topics(subjects_raw),
        tags=normalize_topics(get("tags") or []),
        format=(get("format") or format_default),
        pace=get("pace"),
        modality=get("modality") or "online",
        language=(str(get("language") or "en"))[:5],
        duration_hours=_to_float(get("duration_hours")),
        price_type=map_price_type(get("price_type"), None) or price_type_default,
        price_amount=_to_float(get("price_amount")),
        image_url=get("image_url"),
    )


def _to_float(v) -> float | None:
    if v is None:
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def fetch_paginated_api(
    api_url: str,
    *,
    items_path: str = "results",
    paginate_style: str = "offset",   # 'offset' | 'page' | 'next_url' | 'none'
    page_size: int = 100,
    max_items: int = 100_000,
    headers: Optional[dict] = None,
    query_params: Optional[dict] = None,
    limit_key: str = "limit",
    offset_key: str = "offset",
    page_key: str = "page",
    next_url_path: str = "next",
    delay_sec: float = 0.3,
) -> list[dict]:
    """Iterate a paginated REST API and return raw items.

    Handles four common pagination shapes:
      - offset:   ?offset=0&limit=100 ...
      - page:     ?page=1  ?page=2 ...
      - next_url: response body contains an absolute or relative URL to next page
      - none:     one-shot dump
    """
    items: list[dict] = []
    session_headers = {"User-Agent": "Mozilla/5.0 (LearnerPath ingest)"} | (headers or {})

    with httpx.Client(timeout=60.0, headers=session_headers, follow_redirects=True) as client:
        if paginate_style == "none":
            r = client.get(api_url, params=query_params or {})
            r.raise_for_status()
            items = _dig(r.json(), items_path) or []
            return items[:max_items]

        offset = 0
        page = 1
        next_url = api_url
        while len(items) < max_items:
            params = dict(query_params or {})
            if paginate_style == "offset":
                params[offset_key] = offset
                params[limit_key] = page_size
                url = api_url
            elif paginate_style == "page":
                params[page_key] = page
                params[limit_key] = page_size
                url = api_url
            elif paginate_style == "next_url":
                url = next_url
                if not url:
                    break
                params = {}   # next_url usually includes params
            else:
                raise ValueError(f"unknown paginate_style: {paginate_style}")

            r = client.get(url, params=params)
            if r.status_code != 200:
                print(f"  ! HTTP {r.status_code} at {url}")
                break
            data = r.json()
            batch = _dig(data, items_path) or []
            if not batch:
                break
            items.extend(batch)

            if paginate_style == "offset":
                if len(batch) < page_size:
                    break
                offset += page_size
            elif paginate_style == "page":
                if len(batch) < page_size:
                    break
                page += 1
            elif paginate_style == "next_url":
                next_url = _dig(data, next_url_path)
                if not next_url:
                    break

            time.sleep(delay_sec)

    return items[:max_items]
