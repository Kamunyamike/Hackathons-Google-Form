create table if not exists public.responses (
    response_id uuid primary key,
    edit_token text not null unique,
    record jsonb not null,
    follow_up jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create index if not exists responses_created_at_idx
    on public.responses (created_at);

alter table public.responses enable row level security;
