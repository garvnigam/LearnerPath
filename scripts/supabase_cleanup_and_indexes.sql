-- =============================================================================
-- Cleanup + finalize retrieval infrastructure
--   A) drop legacy harvard_pll_courses table
--   B) drop always-null columns: year_published, year_updated, trailer_url, subtitles
--   C) drop unused future-feature columns: estimated_difficulty, consensus_level
--   D) drop unused quality signals: views_count, likes_count, enrollment_count,
--      ratings_count, rating
--   + Build missing HNSW vector index for semantic search
--   + Install search_courses_semantic RPC
-- All idempotent (IF EXISTS / OR REPLACE). Safe to re-run.
-- =============================================================================

set statement_timeout = '600s';

-- A. Drop legacy table (521 rows already in `courses` with source='harvard_pll')
drop table if exists public.harvard_pll_courses cascade;

-- B. Always-null columns (no ingestor populates them)
alter table public.courses drop column if exists year_published;
alter table public.courses drop column if exists year_updated;
alter table public.courses drop column if exists trailer_url;
alter table public.courses drop column if exists subtitles;

-- C. Future-feature nulls
alter table public.courses drop column if exists estimated_difficulty;
alter table public.courses drop column if exists consensus_level;

-- D. Unused quality signals (mostly null across all sources)
alter table public.courses drop column if exists views_count;
alter table public.courses drop column if exists likes_count;
alter table public.courses drop column if exists enrollment_count;
alter table public.courses drop column if exists ratings_count;
alter table public.courses drop column if exists rating;

-- Recreate match_courses RPC without the removed `rating` reference in ORDER BY.
create or replace function public.match_courses(
    q_topics       text[],
    q_concepts     text[]  default '{}',
    level_in       text[]  default array['beginner','intermediate','advanced'],
    price_types    text[]  default array['free','audit_free','paid','freemium'],
    language_in    text[]  default array['en'],
    max_hours      numeric default null,
    max_count      int     default 40
) returns setof public.courses
language sql stable as $$
    select c.*
    from public.courses c
    where c.active = true
      and c.level = any(level_in)
      and c.price_type = any(price_types)
      and (c.language = any(language_in) or c.language is null)
      and (max_hours is null or c.duration_hours is null or c.duration_hours <= max_hours * 1.2)
      and (c.topics && q_topics or (q_concepts <> '{}' and c.concepts && q_concepts))
    order by
      (case when q_concepts <> '{}' and c.concepts && q_concepts then 2 else 0 end) +
      (case when c.topics && q_topics then 1 else 0 end) desc,
      c.updated_at desc
    limit max_count;
$$;

-- HNSW vector index (this was missing — the reason semantic queries timeout).
create index if not exists idx_courses_embedding
    on public.courses using hnsw (embedding vector_cosine_ops)
    with (m = 16, ef_construction = 32);

-- Semantic-search RPC.
create or replace function public.search_courses_semantic(
    q_embedding    vector(1536),
    level_in       text[]  default array['beginner','intermediate','advanced'],
    price_types    text[]  default array['free','audit_free','paid','freemium'],
    language_in    text[]  default array['en'],
    max_hours      numeric default null,
    match_count    int     default 40
) returns setof public.courses
language sql stable as $$
    select c.*
    from public.courses c
    where c.active = true
      and c.embedding is not null
      and c.level = any(level_in)
      and c.price_type = any(price_types)
      and (c.language = any(language_in) or c.language is null)
      and (max_hours is null or c.duration_hours is null or c.duration_hours <= max_hours * 1.2)
    order by c.embedding <=> q_embedding
    limit match_count;
$$;

analyze public.courses;

reset statement_timeout;
