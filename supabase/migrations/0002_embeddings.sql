-- 0002_embeddings.sql
-- pgvector + separate question_embeddings table (HNSW-indexed).
-- Separate table chosen because:
--   1. questions table stays lean (no 768-dim payload on filter reads)
--   2. multi-model support via (question_id, model) composite PK
--   3. faster filter-then-similarity queries at scale
-- Forward-only. Idempotent — safe to re-run.

create extension if not exists vector;

-- Defensive cleanup: if an earlier version of this migration added an inline
-- embedding column on questions, drop it. The separate table is canonical.
alter table public.questions drop column if exists embedding;

create table if not exists public.question_embeddings (
  question_id  bigint not null references public.questions(id) on delete cascade,
  model        text   not null default 'text-embedding-004',
  embedding    vector(768) not null,
  created_at   timestamptz not null default now(),
  primary key (question_id, model)
);

-- HNSW: best for our scale (~5K → ~1M questions). Incremental insert friendly.
create index if not exists question_embeddings_hnsw_idx
  on public.question_embeddings
  using hnsw (embedding vector_cosine_ops);

-- Read-public (questions are public-read; embeddings inherit that posture).
-- Writes are service-role-only — no INSERT/UPDATE/DELETE policy.
alter table public.question_embeddings enable row level security;

create policy "embeddings public-read"
  on public.question_embeddings for select
  using (true);
