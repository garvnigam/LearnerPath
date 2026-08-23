-- Post-ingest indexing: run after embeddings pass finishes (or once concepts are populated).
-- All indexes are IF NOT EXISTS, safe to re-run.

-- 1. Vector similarity index for semantic search.
--    lists = sqrt(n_rows). At 33k rows, ~180.
--    Increase to sqrt(new_count) if catalog grows past ~50k.
create index if not exists idx_courses_embedding
    on courses using ivfflat (embedding vector_cosine_ops)
    with (lists = 180);

-- 2. Composite index for the hottest retrieval path.
--    Partial index (active = true) is smaller and only touches live rows.
create index if not exists idx_courses_hot
    on courses (active, level, price_type)
    where active = true;

-- 3. Refresh planner statistics after big ingests (Coursera added 23k).
--    Not an index but critical for the planner to choose the right index.
analyze courses;

-- 4. Semantic-search RPC (idempotent).
--    Uses the ivfflat index above via <=> cosine-distance operator.
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
