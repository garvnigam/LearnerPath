-- Post-ingest indexing: run after embeddings pass finishes.
-- All indexes are IF NOT EXISTS, safe to re-run.

-- 1. Vector similarity index for semantic search.
--    HNSW is preferred over ivfflat on Supabase free tier because it doesn't
--    need large maintenance_work_mem (ivfflat lists=180 requires ~70 MB;
--    Supabase free tier caps at 32 MB).
--    m=16, ef_construction=64 are pgvector defaults — good recall on ~33k rows.
create index if not exists idx_courses_embedding
    on courses using hnsw (embedding vector_cosine_ops)
    with (m = 16, ef_construction = 64);

-- 2. Composite index for the hottest retrieval path.
--    Partial index (active = true) is smaller and only touches live rows.
create index if not exists idx_courses_hot
    on courses (active, level, price_type)
    where active = true;

-- 3. Refresh planner statistics after big ingests (Coursera added 23k).
analyze courses;

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
-- Alternative: ivfflat (only if HNSW ever gets removed).
-- Requires bumping maintenance_work_mem for this session:
--   SET maintenance_work_mem = '128MB';
--   CREATE INDEX ... USING ivfflat ...
--   RESET maintenance_work_mem;
-- ==============================================================
