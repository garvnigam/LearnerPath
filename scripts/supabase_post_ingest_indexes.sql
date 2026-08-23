-- Post-ingest indexing: run after embeddings pass finishes.
-- All indexes are IF NOT EXISTS, safe to re-run.

-- Supabase SQL Editor has a 2-minute timeout by default. Bump it for this session
-- so the vector index build has time to complete.
set statement_timeout = '600s';

-- 1. Vector similarity index for semantic search.
--    HNSW is preferred over ivfflat on Supabase free tier because it doesn't
--    need large maintenance_work_mem.
--    m=16 keeps memory small; ef_construction=32 halves build time vs default
--    64 with negligible recall loss at this scale (~33k rows).
create index if not exists idx_courses_embedding
    on courses using hnsw (embedding vector_cosine_ops)
    with (m = 16, ef_construction = 32);

-- 2. Composite index for the hottest retrieval path.
--    Partial index (active = true) is smaller and only touches live rows.
create index if not exists idx_courses_hot
    on courses (active, level, price_type)
    where active = true;

-- 3. Refresh planner statistics after big ingests.
analyze courses;

-- Reset timeout (safety; session ends anyway).
reset statement_timeout;

-- 4. Semantic-search RPC (idempotent).
--    Uses the vector index above via <=> cosine-distance operator.
create or replace function search_courses_semantic(
    q_embedding    vector(1536),
    level_in       text[]  default array['beginner','intermediate','advanced'],
    price_types    text[]  default array['free','audit_free','paid','freemium'],
    language_in    text[]  default array['en'],
    max_hours      numeric default null,
    match_count    int     default 40
) returns setof courses
language sql stable as $$
    select c.*
    from courses c
    where c.active = true
      and c.embedding is not null
      and c.level = any(level_in)
      and c.price_type = any(price_types)
      and (c.language = any(language_in) or c.language is null)
      and (max_hours is null or c.duration_hours is null or c.duration_hours <= max_hours * 1.2)
    order by c.embedding <=> q_embedding
    limit match_count;
$$;

-- ==============================================================
-- If HNSW ever times out even at 10 min: build with parallel workers
--   set max_parallel_maintenance_workers = 4;
--   create index ...
-- Or fall back to ivfflat with bumped work_mem:
--   set maintenance_work_mem = '128MB';
--   create index ... using ivfflat ... with (lists = 100);
--   reset maintenance_work_mem;
-- ==============================================================
