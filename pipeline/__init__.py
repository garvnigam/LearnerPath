"""Pipeline for adding new course sources to LearnerPath.

Public entry point: pipeline/ingest_new_source.py

Adapters (pipeline/adapters/):
    - generic_api.py:    paginated JSON REST APIs
    - generic_jsonld.py: HTML catalogs with schema.org/Course JSON-LD

Configs (pipeline/configs/): saved YAML/JSON specs, one file per source, for
reproducibility. See configs/example_api.yaml and configs/example_jsonld.yaml.

All ingested rows land in the unified `courses` table via scripts/sources/base.py
helpers (upsert on (source, url), exponential backoff, batched writes).

Post-ingest, the CLI can auto-run concept tagging (scripts/enrich_concepts.py)
and embeddings (scripts/enrich_embeddings.py) so new rows are immediately
usable by both keyword and semantic retrieval.
"""
