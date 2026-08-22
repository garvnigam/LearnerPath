-- Enable vector search on the `courses.embedding` column.
-- Run this AFTER `enrich_embeddings.py` has populated at least a few thousand rows.

create extension if not exists vector;

-- ivfflat index (fast approximate search)
-- lists ~= sqrt(n). At 25k rows, lists=160.
create index if not exists idx_courses_embedding
    on courses using ivfflat (embedding vector_cosine_ops) with (lists = 160);

-- RPC for semantic top-K retrieval with metadata filters.
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
