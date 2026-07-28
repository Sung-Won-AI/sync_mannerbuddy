create extension if not exists "pgcrypto";

create table if not exists public.analyses (
    id uuid primary key default gen_random_uuid(),
    user_id uuid,
    kind text not null check (kind in ('email', 'meeting')),
    target_country text not null check (target_country in ('US', 'JP', 'CN')),
    language text not null default 'en',
    source text,
    title text,
    overall_score integer not null check (overall_score between 0 and 100),
    vocabulary_score integer not null check (vocabulary_score between 0 and 100),
    tone_score integer not null check (tone_score between 0 and 100),
    taboo_score integer not null check (taboo_score between 0 and 100),
    manners_score integer not null check (manners_score between 0 and 100),
    meeting_temperature integer check (meeting_temperature between 0 and 100),
    revised_text text,
    summary text not null,
    key_points jsonb not null default '[]'::jsonb,
    action_items jsonb not null default '[]'::jsonb,
    flow jsonb not null default '[]'::jsonb,
    client_request_id text,
    extension_version text,
    processing_time_ms integer not null default 0,
    created_at timestamptz not null default now()
);

create table if not exists public.analysis_issues (
    id uuid primary key default gen_random_uuid(),
    analysis_id uuid not null references public.analyses(id) on delete cascade,
    original_text text not null,
    start_index integer not null default 0,
    end_index integer not null default 0,
    category text not null check (
        category in ('vocabulary', 'tone', 'taboo', 'manners')
    ),
    severity text not null check (severity in ('low', 'medium', 'high')),
    reason text not null,
    suggestion text not null,
    created_at timestamptz not null default now()
);

create table if not exists public.analysis_actions (
    id uuid primary key default gen_random_uuid(),
    analysis_id uuid not null references public.analyses(id) on delete cascade,
    issue_id uuid references public.analysis_issues(id) on delete set null,
    user_id uuid,
    action text not null check (
        action in ('accepted', 'rejected', 'copied', 'dismissed')
    ),
    created_at timestamptz not null default now()
);

create table if not exists public.quiz_attempts (
    id uuid primary key default gen_random_uuid(),
    user_id uuid,
    question_id text not null,
    selected_option_id text not null,
    correct boolean not null,
    created_at timestamptz not null default now()
);

create table if not exists public.feedback (
    id uuid primary key default gen_random_uuid(),
    user_id uuid,
    analysis_id uuid references public.analyses(id) on delete set null,
    rating integer not null check (rating between 1 and 5),
    is_helpful boolean not null,
    comment text,
    created_at timestamptz not null default now()
);

create index if not exists analyses_user_created_idx
    on public.analyses(user_id, created_at desc);

create index if not exists analysis_issues_analysis_idx
    on public.analysis_issues(analysis_id);

create unique index if not exists analyses_client_request_idx
    on public.analyses(user_id, client_request_id)
    where client_request_id is not null;
