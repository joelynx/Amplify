-- 0005_match_questions.sql
-- RPC for "Find similar questions" — cosine KNN against the gemini-embedding-001
-- vectors via pgvector's HNSW index.
-- Forward-only. Idempotent (create or replace).

create or replace function public.match_questions(
  source_id bigint,
  match_count int default 10
)
returns table (
  id bigint,
  topic text,
  branch text,
  subtopic text,
  latexcode text,
  type text,
  similarity real
)
language plpgsql
stable
security invoker
as $$
declare
  source_embedding vector(768);
begin
  select embedding into source_embedding
  from public.question_embeddings
  where question_id = source_id
    and model = 'gemini-embedding-001'
  limit 1;

  if source_embedding is null then
    return;
  end if;

  return query
  select
    q.id,
    q.topic,
    q.branch,
    q.subtopic,
    q.latexcode,
    q.type,
    (1 - (qe.embedding <=> source_embedding))::real as similarity
  from public.question_embeddings qe
    join public.questions q on q.id = qe.question_id
  where qe.question_id <> source_id
    and qe.model = 'gemini-embedding-001'
  order by qe.embedding <=> source_embedding asc
  limit match_count;
end;
$$;

-- Allow anon and authenticated to call it (no row mutation).
grant execute on function public.match_questions(bigint, int) to anon, authenticated;
