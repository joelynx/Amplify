-- Amplify — initial schema
-- One file per migration. Forward-only. Never edit after release.

-- ============================================================
-- questions
-- ============================================================
create table if not exists public.questions (
  id              bigserial primary key,
  topic           text not null,
  branch          text not null,
  subtopic        text not null,
  latexcode       text not null,
  type            text not null check (type in ('proof', 'numerical', 'explanation/reasoning')),
  in_syllabus     boolean not null default true,
  source          text,
  subsource       text,
  answer          text,
  solution        text,
  difficulty_rating real default 0 check (difficulty_rating >= 0 and difficulty_rating <= 20),
  latex_hash      text not null unique,
  times_used      int not null default 0,
  created_at      timestamptz not null default now()
);

create index if not exists questions_topic_idx     on public.questions(topic);
create index if not exists questions_subtopic_idx  on public.questions(topic, branch, subtopic);
create index if not exists questions_type_idx      on public.questions(type);
create index if not exists questions_source_idx    on public.questions(source);

-- ============================================================
-- question_tags
-- ============================================================
create table if not exists public.question_tags (
  question_id bigint not null references public.questions(id) on delete cascade,
  tag         text   not null,
  primary key (question_id, tag)
);

create index if not exists question_tags_tag_idx on public.question_tags(tag);

-- ============================================================
-- practice_sessions
-- ============================================================
create table if not exists public.practice_sessions (
  id           uuid primary key default gen_random_uuid(),
  user_id      uuid references auth.users(id) on delete cascade,
  anon_key     text,  -- for unsigned-in users; client-stored
  filters      jsonb not null,
  n_target     int not null default 10,
  created_at   timestamptz not null default now(),
  completed_at timestamptz,
  check ((user_id is not null) or (anon_key is not null))
);

create index if not exists practice_sessions_user_idx on public.practice_sessions(user_id);
create index if not exists practice_sessions_anon_idx on public.practice_sessions(anon_key);

-- ============================================================
-- practice_responses
-- ============================================================
create table if not exists public.practice_responses (
  id             bigserial primary key,
  session_id     uuid not null references public.practice_sessions(id) on delete cascade,
  question_id    bigint not null references public.questions(id) on delete cascade,
  question_order int not null,
  user_answer    text,
  is_correct     boolean,
  time_taken_ms  int,
  answered_at    timestamptz not null default now(),
  unique (session_id, question_id)
);

create index if not exists practice_responses_session_idx on public.practice_responses(session_id);

-- ============================================================
-- user_mastery — Bayesian beta per (user, subtopic)
-- ============================================================
create table if not exists public.user_mastery (
  user_id      uuid not null references auth.users(id) on delete cascade,
  topic        text not null,
  branch       text not null,
  subtopic     text not null,
  alpha        real not null default 1.0,
  beta         real not null default 1.0,
  total_seen   int  not null default 0,
  last_updated timestamptz not null default now(),
  primary key (user_id, topic, branch, subtopic)
);

create index if not exists user_mastery_user_idx on public.user_mastery(user_id);

-- ============================================================
-- Row Level Security
-- ============================================================

-- Questions and tags are publicly readable.
alter table public.questions enable row level security;
alter table public.question_tags enable row level security;

create policy "questions are public-read"
  on public.questions for select
  using (true);

create policy "question_tags are public-read"
  on public.question_tags for select
  using (true);

-- Practice sessions: own-row-only for signed-in; anon_key match for anonymous.
alter table public.practice_sessions enable row level security;
alter table public.practice_responses enable row level security;

create policy "sessions: own rows or anon match"
  on public.practice_sessions for all
  using (
    (auth.uid() is not null and user_id = auth.uid())
    or (auth.uid() is null and anon_key is not null)
  )
  with check (
    (auth.uid() is not null and user_id = auth.uid())
    or (auth.uid() is null and anon_key is not null)
  );

create policy "responses: own session"
  on public.practice_responses for all
  using (
    exists (
      select 1 from public.practice_sessions s
      where s.id = session_id
      and (
        (auth.uid() is not null and s.user_id = auth.uid())
        or (auth.uid() is null and s.anon_key is not null)
      )
    )
  )
  with check (
    exists (
      select 1 from public.practice_sessions s
      where s.id = session_id
      and (
        (auth.uid() is not null and s.user_id = auth.uid())
        or (auth.uid() is null and s.anon_key is not null)
      )
    )
  );

-- Mastery: signed-in users only, own row.
alter table public.user_mastery enable row level security;

create policy "mastery: own rows"
  on public.user_mastery for all
  using (auth.uid() = user_id)
  with check (auth.uid() = user_id);
