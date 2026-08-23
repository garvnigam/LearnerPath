#!/usr/bin/env python3
"""One-command pipeline to add a new course source.

Modes:
  api      — paginated JSON REST API. Configure via --items-path / --map-title / etc.
  jsonld   — HTML catalog site with embedded schema.org/Course JSON-LD.
  config   — replay a YAML/JSON config file (recommended for reproducibility).

After ingest, this optionally kicks off concept tagging + embeddings so the new
rows are usable by retrieval immediately.

Examples:
  # NEW: paginated JSON API (Microsoft-Learn-style)
  python pipeline/ingest_new_source.py api \\
    --name my_source \\
    --api-url https://api.example.com/v1/courses \\
    --items-path results \\
    --paginate-style page \\
    --map-title title \\
    --map-url url \\
    --map-description summary \\
    --map-level level \\
    --map-topics topics \\
    --limit 500

  # NEW: JSON-LD scrape (Harvard-PLL-style)
  python pipeline/ingest_new_source.py jsonld \\
    --name yale_online \\
    --scrape-url https://online.yale.edu/courses \\
    --limit 100

  # REPLAY: use a saved config
  python pipeline/ingest_new_source.py config pipeline/configs/example_api.yaml

  # SKIP enrichment (fastest, but new rows won't be discoverable by concept/semantic match)
  python pipeline/ingest_new_source.py api ... --skip-enrichment
"""
from __future__ import annotations

import argparse
import asyncio
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Make scripts/sources/base.py importable + the sibling adapters/ folder.
for p in (ROOT / "scripts", ROOT / "pipeline"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from sources.base import get_client, upsert_courses  # noqa: E402
from adapters.generic_api import fetch_paginated_api, normalize_item_generic  # noqa: E402
from adapters.generic_jsonld import scrape_jsonld_site  # noqa: E402


# ------------------------- config file support -------------------------
def load_config(path: Path) -> dict:
    text = path.read_text()
    if path.suffix in (".yml", ".yaml"):
        try:
            import yaml  # type: ignore
        except ImportError:
            print("ERROR: pyyaml not installed. Run: pip install pyyaml")
            sys.exit(1)
        return yaml.safe_load(text)
    return json.loads(text)


# ------------------------- mode: api -------------------------
def run_api_mode(args) -> tuple[str, int]:
    """Returns (source_name, rows_upserted)."""
    print(f"[ingest] mode=api  name={args.name}  url={args.api_url}")

    mapping: dict[str, str | list[str]] = {}
    for k, v in vars(args).items():
        if k.startswith("map_") and v:
            mapping[k[4:]] = v

    if "title" not in mapping or "url" not in mapping:
        print("ERROR: --map-title and --map-url are required in api mode.")
        sys.exit(1)

    raw_items = fetch_paginated_api(
        args.api_url,
        items_path=args.items_path or "results",
        paginate_style=args.paginate_style or "offset",
        page_size=args.page_size,
        max_items=args.limit or 100_000,
        query_params=(json.loads(args.query_params) if args.query_params else None),
        limit_key=args.limit_key,
        offset_key=args.offset_key,
        page_key=args.page_key,
        next_url_path=args.next_url_path,
    )
    print(f"[ingest] fetched {len(raw_items)} raw items")

    rows = []
    for item in raw_items:
        row = normalize_item_generic(
            item,
            source=args.name,
            mapping=mapping,
            provider_default=args.provider or "",
        )
        if row:
            rows.append(row)
    print(f"[ingest] normalized {len(rows)}/{len(raw_items)} rows")

    if not rows:
        return args.name, 0

    supabase = get_client()
    up, err = upsert_courses(supabase, rows, batch_size=100)
    print(f"[ingest] upserted={up}, errors={err}")
    return args.name, up


# ------------------------- mode: jsonld -------------------------
async def run_jsonld_mode(args) -> tuple[str, int]:
    print(f"[ingest] mode=jsonld  name={args.name}  url={args.scrape_url}")
    rows = await scrape_jsonld_site(
        args.scrape_url,
        source=args.name,
        url_pattern=args.url_pattern,
        max_pages=args.max_pages,
    )
    print(f"[ingest] scraped {len(rows)} rows")

    if args.limit:
        rows = rows[: args.limit]

    if not rows:
        return args.name, 0

    supabase = get_client()
    up, err = upsert_courses(supabase, rows, batch_size=50)
    print(f"[ingest] upserted={up}, errors={err}")
    return args.name, up


# ------------------------- enrichment orchestration -------------------------
def run_enrichment(source_name: str, skip: bool) -> None:
    if skip:
        print("[ingest] --skip-enrichment set; not tagging or embedding new rows.")
        return

    print(f"\n[ingest] running concept tagger for source={source_name!r} ...")
    # tag only untagged rows (script already filters by concepts='{}')
    r = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "enrich_concepts.py")],
        cwd=str(ROOT),
    )
    if r.returncode != 0:
        print("[ingest] tagger failed; continuing to embeddings anyway")

    print(f"\n[ingest] running embeddings pass ...")
    r = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "enrich_embeddings.py")],
        cwd=str(ROOT),
    )
    if r.returncode != 0:
        print("[ingest] embeddings failed; new rows will still work via keyword match")


# ------------------------- argparse -------------------------
def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="mode", required=True)

    # api mode
    api = sub.add_parser("api", help="Ingest a paginated JSON REST API")
    api.add_argument("--name", required=True, help="Source identifier (goes into courses.source)")
    api.add_argument("--api-url", required=True)
    api.add_argument("--items-path", default="results", help="Dotted path to the list of items in each response")
    api.add_argument("--paginate-style", default="offset", choices=["offset", "page", "next_url", "none"])
    api.add_argument("--page-size", type=int, default=100)
    api.add_argument("--limit", type=int, default=None, help="Max items to ingest total")
    api.add_argument("--query-params", default=None, help="Extra query params as JSON string")
    api.add_argument("--limit-key", default="limit")
    api.add_argument("--offset-key", default="offset")
    api.add_argument("--page-key", default="page")
    api.add_argument("--next-url-path", default="next")
    api.add_argument("--provider", default=None, help="Default provider label")
    # mapping flags — a key per unified column
    for col in ("title", "url", "description", "provider", "school", "platform",
                "level", "topics", "subjects", "tags", "format", "pace",
                "modality", "language", "duration_hours", "price_type",
                "price_amount", "image_url", "external_id"):
        api.add_argument(f"--map-{col.replace('_','-')}", dest=f"map_{col}", default=None,
                         help=f"Dotted path in raw item that maps to `{col}`")

    # jsonld mode
    js = sub.add_parser("jsonld", help="Scrape an HTML catalog with schema.org/Course JSON-LD")
    js.add_argument("--name", required=True)
    js.add_argument("--scrape-url", required=True, help="Listing / catalog URL")
    js.add_argument("--url-pattern", default="/course", help="Substring courses' href must contain")
    js.add_argument("--max-pages", type=int, default=20)
    js.add_argument("--limit", type=int, default=None)

    # config mode
    cf = sub.add_parser("config", help="Replay a saved YAML/JSON config")
    cf.add_argument("path", type=str)

    # shared
    for _sub in (api, js, cf):
        _sub.add_argument("--skip-enrichment", action="store_true",
                          help="Don't run concept tagging / embedding after ingest")

    return p


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.mode == "config":
        cfg = load_config(Path(args.path))
        cfg.setdefault("skip_enrichment", args.skip_enrichment)
        # Rebuild an argparse.Namespace from the config and re-dispatch.
        inner_mode = cfg.pop("mode", None)
        if inner_mode not in ("api", "jsonld"):
            print(f"config missing/invalid 'mode': {inner_mode}")
            sys.exit(1)
        ns = argparse.Namespace(mode=inner_mode, skip_enrichment=cfg.pop("skip_enrichment", False))
        for k, v in cfg.items():
            setattr(ns, k, v)
        args = ns

    if args.mode == "api":
        source, _ = run_api_mode(args)
    elif args.mode == "jsonld":
        source, _ = asyncio.run(run_jsonld_mode(args))
    else:
        parser.error(f"unknown mode: {args.mode}")
        return

    run_enrichment(source, args.skip_enrichment)


if __name__ == "__main__":
    main()
