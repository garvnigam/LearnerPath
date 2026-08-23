# LearnerPath Ingestion Pipeline

Add any new free course source to the `courses` database with **one command**.
Handles ingestion, deduplication, concept tagging, and embedding automatically.

## When to use this

You have a URL for a new course catalog (JSON API or HTML site) and want it in
the DB without writing a per-source Python file. If the source has particularly
weird pagination or auth, prefer a dedicated ingestor under `scripts/sources/`.

## Two modes

### 1. Paginated JSON API

For sources like edX Discovery, Coursera Catalog, Microsoft Learn, MIT Learn.

```bash
python pipeline/ingest_new_source.py api \
  --name my_source \
  --api-url https://api.example.com/v1/courses \
  --items-path results \
  --paginate-style page \
  --map-title title \
  --map-url url \
  --map-description summary \
  --map-level level \
  --map-topics topics \
  --limit 500
```

Every `--map-<col>` flag maps a unified-schema column (see
`scripts/sources/base.py`) to a dotted path inside each raw API item.

### 2. HTML with JSON-LD

For sites like Harvard PLL, Stanford Online, Yale Open Courses — any site whose
course pages embed `<script type="application/ld+json">` with `@type=Course`.

```bash
python pipeline/ingest_new_source.py jsonld \
  --name stanford_online \
  --scrape-url https://online.stanford.edu/courses \
  --limit 100
```

### 3. Config file (recommended for reproducibility)

Save the spec so you can re-ingest later or share:

```bash
cp pipeline/configs/example_api.yaml pipeline/configs/my_source.yaml
# edit my_source.yaml
python pipeline/ingest_new_source.py config pipeline/configs/my_source.yaml
```

## What happens after ingest

Unless you pass `--skip-enrichment`, the pipeline runs:

1. **Concept tagging** — `gpt-4.1-mini` tags each new row with 3-8 concrete
   concepts + 0-5 prerequisite concepts.
2. **Embeddings** — `text-embedding-3-small` produces a 1536-dim vector per row
   for semantic search.

The tagger and embedder are both **idempotent** — they only touch new rows.

## Where files live

```
pipeline/
├── ingest_new_source.py   # CLI entry point
├── adapters/
│   ├── generic_api.py     # paginated JSON API adapter
│   └── generic_jsonld.py  # schema.org JSON-LD scraper
└── configs/
    ├── example_api.yaml   # copy → edit → replay
    └── example_jsonld.yaml
```

Shared upsert / mapping helpers live in `scripts/sources/base.py` (same code
path used by all existing per-source ingestors).

## Test with a tiny run first

Always set `--limit 5` on your first run to catch mapping issues cheaply:

```bash
python pipeline/ingest_new_source.py api \
  --name test_smoke \
  --api-url ... \
  --map-title title --map-url url \
  --limit 5 --skip-enrichment
```

Inspect a few rows in Supabase, tweak your `--map-*` flags, then rerun without
the limit + without `--skip-enrichment`.

## Requirements

Python deps already listed in `backend/requirements.txt` + `scripts/requirements-scraper.txt`:

- `httpx`, `aiohttp`, `beautifulsoup4`, `supabase`, `python-dotenv`
- `pyyaml` (only needed for `config` mode)

Env vars in `backend/.env`:

- `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE`
- `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_KEY`, `AZURE_OPENAI_DEPLOYMENT`
  (only needed when enrichment runs)
