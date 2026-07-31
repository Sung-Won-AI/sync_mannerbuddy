-- Demo data should use synthetic content only.
-- The backend's current default is an in-memory repository, so this file is
-- intentionally empty until Supabase Auth user IDs are available.

create extension if not exists pgcrypto;

create table if not exists analyses (
  analysis_id uuid primary key default gen_random_uuid(),
  request_id text,
  client_request_id text,
  extension_version text,

  target_country text not null check (target_country in ('US', 'JP')),
  language text not null default 'en',
  source text not null default 'gmail',
  mode text not null check (mode in ('manual', 'automatic')),

  masked_text text not null,
  overall_score int not null check (overall_score between 0 and 100),
  scores jsonb not null,
  issues jsonb not null default '[]'::jsonb,
  revised_text text not null,
  summary text not null,

  processing_time_ms int not null check (processing_time_ms >= 0),
  created_at timestamptz not null default now()
);

create index if not exists idx_analyses_created_at on analyses (created_at desc);
create index if not exists idx_analyses_client_request_id on analyses (client_request_id);
