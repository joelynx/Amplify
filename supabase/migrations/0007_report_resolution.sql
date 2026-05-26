-- 0007_report_resolution.sql
-- Lets faculty mark a question_report as resolved.

alter table public.question_reports
  add column if not exists resolved_at timestamptz,
  add column if not exists resolved_by uuid references auth.users(id) on delete set null;

create index if not exists question_reports_unresolved_idx
  on public.question_reports(question_id) where resolved_at is null;
