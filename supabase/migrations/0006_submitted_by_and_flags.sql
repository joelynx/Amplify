-- 0006_submitted_by_and_flags.sql
-- Track who submitted each question and a simple report-flag mechanism.
-- Forward-only. Idempotent.

alter table public.questions
  add column if not exists submitted_by text,
  add column if not exists flagged_count int not null default 0;

-- Lightweight reports — anyone signed in can flag a question; lets faculty
-- decide what to triage. No moderation UI yet, but the data path is there.
create table if not exists public.question_reports (
  id          bigserial primary key,
  question_id bigint not null references public.questions(id) on delete cascade,
  reporter_id uuid references auth.users(id) on delete set null,
  reason      text,
  created_at  timestamptz not null default now()
);

create index if not exists question_reports_question_id_idx
  on public.question_reports(question_id);

alter table public.question_reports enable row level security;

-- Anyone signed in can insert their own report.
drop policy if exists "reports: signed-in insert" on public.question_reports;
create policy "reports: signed-in insert"
  on public.question_reports for insert
  with check (auth.uid() = reporter_id);

-- Reports are not publicly readable. Faculty/admins read via service-role.
drop policy if exists "reports: own rows readable" on public.question_reports;
create policy "reports: own rows readable"
  on public.question_reports for select
  using (auth.uid() = reporter_id);
