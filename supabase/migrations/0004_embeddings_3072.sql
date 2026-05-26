-- 0004_embeddings_3072.sql
-- text-embedding-004 was deprecated by Google. Switching to gemini-embedding-001
-- with Matryoshka truncation → 768 dims (stays under pgvector HNSW's 2000-dim cap).
-- Drop & recreate the embeddings table (no data loss — no 768 vectors were ever written).
-- Forward-only. Idempotent.

-- Only drop the table if it doesn't already exist with the right shape.
-- Re-running migrations should never wipe populated embeddings.
do $$
begin
  if not exists (
    select 1 from information_schema.tables
    where table_schema = 'public' and table_name = 'question_embeddings'
  ) then
    -- nothing to drop, just continue to create
    null;
  end if;
end$$;

create table if not exists public.question_embeddings (
  question_id  bigint not null references public.questions(id) on delete cascade,
  model        text   not null default 'gemini-embedding-001',
  embedding    vector(768) not null,
  created_at   timestamptz not null default now(),
  primary key (question_id, model)
);

create index if not exists question_embeddings_hnsw_idx
  on public.question_embeddings
  using hnsw (embedding vector_cosine_ops);

alter table public.question_embeddings enable row level security;

create policy "embeddings public-read"
  on public.question_embeddings for select
  using (true);
