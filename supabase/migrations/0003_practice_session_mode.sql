-- 0003_practice_session_mode.sql
-- Add `mode` (random|diverse) and `diversity_score` to practice_sessions so the
-- generation strategy and its measured diversity are recorded per session.
-- Forward-only. Idempotent.

alter table public.practice_sessions
  add column if not exists mode text default 'random';

alter table public.practice_sessions
  add column if not exists diversity_score real;

-- Backfill any NULL modes on pre-existing sessions.
update public.practice_sessions set mode = 'random' where mode is null;

-- Add the check constraint once, idempotently.
do $$
begin
  if not exists (
    select 1 from pg_constraint
    where conname = 'practice_sessions_mode_check'
  ) then
    alter table public.practice_sessions
      add constraint practice_sessions_mode_check
      check (mode in ('random', 'diverse'));
  end if;
end$$;
