-- Harvard PLL Courses Table
-- Run this in Supabase SQL Editor

create extension if not exists pgcrypto;  -- for gen_random_uuid()
create extension if not exists vector;   -- for embeddings (optional)

create table if not exists harvard_pll_courses (
    id uuid primary key default gen_random_uuid(),
    
    -- Core identifiers
    title text not null,
    url text unique not null,
    provider text not null,
    school text,
    
    -- Content
    description text,
    duration text,
    time_commitment text,
    pace text,
    modality text,
    language text,
    
    -- Classification
    level text not null check (level in ('beginner', 'intermediate', 'advanced')),
    topics text[] not null default '{}',
    subjects text[] not null default '{}',
    
    -- Platform & delivery
    platform text,
    format text not null default 'course',
    source text not null default 'harvard_pll',
    
    -- Pricing
    price_type text not null check (price_type in ('free', 'paid')),
    price_amount numeric(10, 2),
    price_currency text not null default 'USD',
    certificate_price numeric(10, 2),
    
    -- Metadata
    image_url text,
    
    -- Timestamps
    scraped_at timestamptz not null,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

-- Indexes for common queries
create index if not exists idx_harvard_pll_price_type on harvard_pll_courses(price_type);
create index if not exists idx_harvard_pll_level on harvard_pll_courses(level);
create index if not exists idx_harvard_pll_topics on harvard_pll_courses using gin(topics);
create index if not exists idx_harvard_pll_subjects on harvard_pll_courses using gin(subjects);
create index if not exists idx_harvard_pll_url on harvard_pll_courses(url);

-- Optional: full-text search
alter table harvard_pll_courses add column if not exists search_vector tsvector;
create index if not exists idx_harvard_pll_search on harvard_pll_courses using gin(search_vector);

-- Trigger to update search_vector
create or replace function update_search_vector() returns trigger as $$
begin
    new.search_vector :=
        setweight(to_tsvector('english', coalesce(new.title, '')), 'A') ||
        setweight(to_tsvector('english', coalesce(new.description, '')), 'B') ||
        setweight(to_tsvector('english', array_to_string(new.topics, ' ')), 'C') ||
        setweight(to_tsvector('english', array_to_string(new.subjects, ' ')), 'C');
    return new;
end;
$$ language plpgsql;

drop trigger if exists trigger_update_search_vector on harvard_pll_courses;
create trigger trigger_update_search_vector
    before insert or update on harvard_pll_courses
    for each row execute function update_search_vector();

-- Optional: embedding column for semantic search (uncomment if using pgvector)
-- alter table harvard_pll_courses add column if not exists embedding vector(1536);
-- create index if not exists idx_harvard_pll_embedding on harvard_pll_courses using ivfflat (embedding vector_cosine_ops);

-- RLS (Row Level Security) - allow public read
alter table harvard_pll_courses enable row level security;

drop policy if exists "Allow public read" on harvard_pll_courses;
create policy "Allow public read" on harvard_pll_courses
    for select using (true);

-- Insert/Update policy (service role only)
drop policy if exists "Service role write" on harvard_pll_courses;
create policy "Service role write" on harvard_pll_courses
    for all using (auth.role() = 'service_role');