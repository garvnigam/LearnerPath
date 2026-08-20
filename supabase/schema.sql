-- Run this in the Supabase SQL editor.

create table if not exists public.learning_sessions (
  session_id text primary key,
  user_id uuid references auth.users(id) on delete cascade,
  data jsonb not null,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create index if not exists idx_learning_sessions_user on public.learning_sessions(user_id);

create or replace function public.touch_updated_at() returns trigger as $$
begin new.updated_at = now(); return new; end $$ language plpgsql;

drop trigger if exists trg_learning_sessions_touch on public.learning_sessions;
create trigger trg_learning_sessions_touch
  before update on public.learning_sessions
  for each row execute function public.touch_updated_at();

alter table public.learning_sessions enable row level security;

drop policy if exists "own sessions read" on public.learning_sessions;
create policy "own sessions read" on public.learning_sessions
  for select using (auth.uid() = user_id);

drop policy if exists "own sessions write" on public.learning_sessions;
create policy "own sessions write" on public.learning_sessions
  for insert with check (auth.uid() = user_id);

drop policy if exists "own sessions update" on public.learning_sessions;
create policy "own sessions update" on public.learning_sessions
  for update using (auth.uid() = user_id);
