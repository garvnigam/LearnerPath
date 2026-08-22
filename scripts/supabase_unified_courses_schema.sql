-- One authoritative courses table for all sources (MIT, Harvard, NPTEL, YouTube, edX, etc.)
-- Optimized for < 200ms retrieval at 50k+ rows.

create extension if not exists pgcrypto;
create extension if not exists pg_trgm;
create extension if not exists vector;

create table if not exists courses (
    id                      uuid primary key default gen_random_uuid(),

    -- Identity & provenance
    source                  text not null,               -- 'mit_learn' | 'harvard_pll' | 'nptel' | ...
    external_id             text,                        -- source-specific id
    url                     text not null,
    canonical_url           text,                        -- for cross-source dedupe (nightly job fills)

    -- Core content
    title                   text not null,
    description             text,
    provider                text,
    school                  text,
    platform                text,                        -- edX | Coursera | YouTube | OCW | ...

    -- Classification (INDEXED for fast retrieval)
    level                   text not null check (level in ('beginner','intermediate','advanced')) default 'intermediate',
    consensus_level         text,                        -- filled by nightly cross-source majority vote
    estimated_difficulty    numeric(3,2),                -- 0.0–3.0, filled by calibration (later)
    topics                  text[] not null default '{}',
    concepts                text[] not null default '{}', -- fine-grained skill tags (see enrichment)
    subjects                text[] not null default '{}',
    tags                    text[] not null default '{}',
    prerequisite_concepts   text[] not null default '{}',

    -- Format / delivery
    format                  text default 'course',
    pace                    text,
    modality                text default 'online',
    language                text default 'en',
    subtitles               text[] default '{}',

    -- Timing (essential for time-budget matching)
    duration_hours          numeric,
    weeks                   int,
    hours_per_week_min      numeric,
    hours_per_week_max      numeric,

    -- Pricing
    price_type              text not null check (price_type in ('free','audit_free','paid','freemium')) default 'free',
    price_amount            numeric(10,2),
    price_currency          text default 'USD',
    certificate_available   boolean default false,
    certificate_price       numeric(10,2),

    -- Quality signals
    rating                  numeric(3,2),
    ratings_count           int,
    views_count             bigint,
    likes_count             bigint,
    enrollment_count        bigint,
    year_published          int,
    year_updated            int,

    image_url               text,
    trailer_url             text,

    -- Retrieval indexes
    search_vector           tsvector,
    embedding               vector(1536),                -- populate later

    -- Housekeeping
    active                  boolean not null default true,
    scraped_at              timestamptz not null default now(),
    created_at              timestamptz not null default now(),
    updated_at              timestamptz not null default now(),

    unique (source, url)
);

-- ---- indexes that keep queries fast ----
create index if not exists idx_courses_topics       on courses using gin (topics);
create index if not exists idx_courses_concepts     on courses using gin (concepts);
create index if not exists idx_courses_subjects     on courses using gin (subjects);
create index if not exists idx_courses_tags         on courses using gin (tags);
create index if not exists idx_courses_search       on courses using gin (search_vector);

create index if not exists idx_courses_source       on courses (source);
create index if not exists idx_courses_platform     on courses (platform);
create index if not exists idx_courses_level        on courses (level);
create index if not exists idx_courses_price_type   on courses (price_type);
create index if not exists idx_courses_active       on courses (active);
create index if not exists idx_courses_duration     on courses (duration_hours);
create index if not exists idx_courses_updated      on courses (updated_at desc);
create index if not exists idx_courses_canonical    on courses (canonical_url);

-- title trigram index for fuzzy dedupe
create index if not exists idx_courses_title_trgm   on courses using gin (title gin_trgm_ops);

-- Vector index: create AFTER you populate embeddings. Rule of thumb: lists = sqrt(row_count).
-- create index if not exists idx_courses_embedding on courses using ivfflat (embedding vector_cosine_ops) with (lists = 225);

-- ---- tsvector auto-update trigger ----
create or replace function courses_search_vector_update() returns trigger as $$
begin
  new.search_vector :=
    setweight(to_tsvector('english', coalesce(new.title, '')), 'A') ||
    setweight(to_tsvector('english', coalesce(new.description, '')), 'B') ||
    setweight(to_tsvector('english', array_to_string(coalesce(new.topics, '{}'), ' ')), 'C') ||
    setweight(to_tsvector('english', array_to_string(coalesce(new.concepts, '{}'), ' ')), 'C') ||
    setweight(to_tsvector('english', array_to_string(coalesce(new.subjects, '{}'), ' ')), 'D');
  new.updated_at := now();
  return new;
end;
$$ language plpgsql;

drop trigger if exists trg_courses_search on courses;
create trigger trg_courses_search
  before insert or update on courses
  for each row execute function courses_search_vector_update();

-- ---- retrieval RPC used by hybrid_retrieval.py ----
create or replace function match_courses(
    q_topics       text[],
    q_concepts     text[]  default '{}',
    level_in       text[]  default array['beginner','intermediate','advanced'],
    price_types    text[]  default array['free','audit_free','paid','freemium'],
    language_in    text[]  default array['en'],
    max_hours      numeric default null,
    max_count      int     default 40
) returns setof courses
language sql stable as $$
    select c.*
    from courses c
    where c.active = true
      and c.level = any(level_in)
      and c.price_type = any(price_types)
      and (c.language = any(language_in) or c.language is null)
      and (max_hours is null or c.duration_hours is null or c.duration_hours <= max_hours * 1.2)
      and (c.topics && q_topics or (q_concepts <> '{}' and c.concepts && q_concepts))
    order by
      (case when q_concepts <> '{}' and c.concepts && q_concepts then 2 else 0 end) +
      (case when c.topics && q_topics then 1 else 0 end) desc,
      c.rating desc nulls last,
      c.updated_at desc
    limit max_count;
$$;

-- ---- backfill from harvard_pll_courses (one-time; safe to re-run) ----
insert into courses (
    source, url, title, description, provider, school, platform,
    level, topics, subjects, format, pace, modality, language,
    price_type, price_amount, price_currency, certificate_price, image_url,
    scraped_at
)
select
    'harvard_pll', url, title, description, provider, school, platform,
    level, topics, coalesce(subjects, topics), coalesce(format, 'course'),
    pace, modality, language, price_type, price_amount, coalesce(price_currency, 'USD'),
    certificate_price, image_url, scraped_at
from harvard_pll_courses
on conflict (source, url) do update set
    title = excluded.title,
    description = excluded.description,
    updated_at = now();
