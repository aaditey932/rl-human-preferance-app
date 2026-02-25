-- Run this in the Supabase SQL editor to create the preferences table.

create table if not exists preferences (
  id         uuid primary key default gen_random_uuid(),
  prompt     text not null,
  response_a text not null,
  response_b text not null,
  preference text not null check (preference in ('a', 'b', 'tie')),
  metadata   jsonb default '{}',
  created_at timestamptz default now()
);

-- Allow inserts/selects without RLS policies (service_role bypasses RLS; anon needs this).
alter table preferences disable row level security;
