create extension if not exists "pgcrypto";

-- issues/key_points/action_items/flow는 항상 부모 analysis와 함께 통째로
-- 읽고 쓰기 때문에(개별 issue를 따로 조회하는 곳이 없음) 별도 테이블로
-- 정규화하지 않고 jsonb 컬럼으로 둔다. app/repositories/supabase_repository.py
-- 참고.
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
    issues jsonb not null default '[]'::jsonb,
    key_points jsonb not null default '[]'::jsonb,
    action_items jsonb not null default '[]'::jsonb,
    flow jsonb not null default '[]'::jsonb,
    client_request_id text,
    extension_version text,
    processing_time_ms integer not null default 0,
    created_at timestamptz not null default now()
);

create table if not exists public.analysis_actions (
    id uuid primary key default gen_random_uuid(),
    analysis_id uuid not null references public.analyses(id) on delete cascade,
    -- AI가 매기는 issue_id는 UUID가 아닐 수 있어(예: "TONE_001") FK 대신 text로 둔다.
    issue_id text,
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

create unique index if not exists analyses_client_request_idx
    on public.analyses(user_id, client_request_id)
    where client_request_id is not null;
