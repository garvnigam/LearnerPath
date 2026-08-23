"""Source adapters. Each converts a raw catalog into unified `courses` rows.

- generic_api: paginated JSON REST endpoint
- generic_jsonld: HTML page with embedded schema.org/Course JSON-LD

Shared utilities (upsert, level/price mapping, topic normalization) live in
../../scripts/sources/base.py so the existing ingestors and these adapters use
the same code path.
"""
