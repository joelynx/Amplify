-- Amplify migration 0002 — the institutional data model.
-- Adds: institutions, courses, course_questions, user_profiles (with role),
-- question_revisions, question_drafts. Updates RLS.

-- ============================================================
-- institutions
-- ============================================================
create table if not exists public.institutions (
  id          bigserial primary key,
  slug        text not null unique,
  name        text not null,
  short_name  text not null,
  country     text not null default 'IN',
  logo_url    text,
  primary_color text default '#0f1320',
  joined_at   timestamptz not null default now(),
  is_active   boolean not null default true,
  status      text not null default 'active' check (status in ('active', 'pilot', 'interested')),
  description text
);

create index if not exists institutions_slug_idx on public.institutions(slug);

-- ============================================================
-- courses
-- ============================================================
create table if not exists public.courses (
  id             bigserial primary key,
  institution_id bigint not null references public.institutions(id) on delete cascade,
  slug           text not null,
  code           text not null,
  name           text not null,
  description    text,
  created_at     timestamptz not null default now(),
  unique (institution_id, slug)
);

create index if not exists courses_institution_idx on public.courses(institution_id);

-- ============================================================
-- course_questions (M:N — questions belong to one or more courses)
-- ============================================================
create table if not exists public.course_questions (
  course_id   bigint not null references public.courses(id) on delete cascade,
  question_id bigint not null references public.questions(id) on delete cascade,
  primary key (course_id, question_id)
);

create index if not exists course_questions_q_idx on public.course_questions(question_id);

-- ============================================================
-- user_profiles — extends auth.users with role + institution
-- ============================================================
create type user_role as enum ('student', 'faculty', 'admin', 'moderator');

create table if not exists public.user_profiles (
  user_id        uuid primary key references auth.users(id) on delete cascade,
  institution_id bigint references public.institutions(id) on delete set null,
  display_name   text,
  role           user_role not null default 'student',
  created_at     timestamptz not null default now()
);

-- Auto-create a profile row on signup.
create or replace function public.handle_new_user()
returns trigger as $$
begin
  insert into public.user_profiles (user_id, display_name)
  values (new.id, coalesce(new.raw_user_meta_data->>'display_name', split_part(new.email, '@', 1)))
  on conflict (user_id) do nothing;
  return new;
end;
$$ language plpgsql security definer;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function public.handle_new_user();

-- ============================================================
-- Contribution attribution on questions
-- ============================================================
alter table public.questions
  add column if not exists contributed_by uuid references auth.users(id) on delete set null,
  add column if not exists contributed_at timestamptz default now(),
  add column if not exists last_revised_by uuid references auth.users(id) on delete set null,
  add column if not exists last_revised_at timestamptz;

-- ============================================================
-- question_revisions — append-only history
-- ============================================================
create table if not exists public.question_revisions (
  id              bigserial primary key,
  question_id     bigint not null references public.questions(id) on delete cascade,
  revised_by      uuid references auth.users(id) on delete set null,
  revised_at      timestamptz not null default now(),
  latexcode_before text,
  latexcode_after  text,
  solution_before  text,
  solution_after   text,
  reason          text
);

create index if not exists question_revisions_q_idx on public.question_revisions(question_id);

-- ============================================================
-- question_drafts — author submissions awaiting moderation
-- ============================================================
create table if not exists public.question_drafts (
  id           bigserial primary key,
  author_id    uuid references auth.users(id) on delete cascade,
  institution_id bigint references public.institutions(id) on delete set null,
  course_id    bigint references public.courses(id) on delete set null,
  topic        text not null,
  branch       text not null,
  subtopic     text not null,
  latexcode    text not null,
  type         text not null check (type in ('proof', 'numerical', 'explanation/reasoning')),
  source       text,
  answer       text,
  solution     text,
  status       text not null default 'pending' check (status in ('pending', 'approved', 'rejected', 'needs_revision')),
  reviewer_id  uuid references auth.users(id) on delete set null,
  reviewed_at  timestamptz,
  review_notes text,
  created_at   timestamptz not null default now()
);

create index if not exists question_drafts_status_idx on public.question_drafts(status);
create index if not exists question_drafts_author_idx on public.question_drafts(author_id);

-- ============================================================
-- RLS for the new tables
-- ============================================================

-- Institutions + courses + course_questions are public-read.
alter table public.institutions enable row level security;
alter table public.courses enable row level security;
alter table public.course_questions enable row level security;

create policy "institutions public-read" on public.institutions for select using (true);
create policy "courses public-read"      on public.courses for select using (true);
create policy "course_questions public-read" on public.course_questions for select using (true);

-- user_profiles: own row read+update; everyone can read display_name and institution.
alter table public.user_profiles enable row level security;

create policy "profiles: own row read"
  on public.user_profiles for select
  using (auth.uid() = user_id or true); -- public read for attribution display

create policy "profiles: own row update"
  on public.user_profiles for update
  using (auth.uid() = user_id);

create policy "profiles: own row insert"
  on public.user_profiles for insert
  with check (auth.uid() = user_id);

-- question_revisions: public-read (full transparency).
alter table public.question_revisions enable row level security;
create policy "revisions public-read" on public.question_revisions for select using (true);

-- question_drafts: authors see their own; moderators/admins see all.
alter table public.question_drafts enable row level security;

create policy "drafts: author or moderator read"
  on public.question_drafts for select
  using (
    auth.uid() = author_id
    or exists (
      select 1 from public.user_profiles
      where user_id = auth.uid()
      and role in ('moderator', 'admin')
    )
  );

create policy "drafts: faculty or admin insert"
  on public.question_drafts for insert
  with check (
    exists (
      select 1 from public.user_profiles
      where user_id = auth.uid()
      and role in ('faculty', 'admin', 'moderator')
    )
  );

create policy "drafts: moderators update"
  on public.question_drafts for update
  using (
    exists (
      select 1 from public.user_profiles
      where user_id = auth.uid()
      and role in ('moderator', 'admin')
    )
  );

-- ============================================================
-- Seed the canonical institution: IIT-Delhi Abu Dhabi
-- ============================================================
insert into public.institutions (slug, name, short_name, country, status, description)
values (
  'iit-ad',
  'Indian Institute of Technology, Delhi — Abu Dhabi Campus',
  'IIT-AD',
  'AE',
  'active',
  'The Abu Dhabi campus of IIT Delhi. Launched 2024. The first institution on Amplify.'
)
on conflict (slug) do nothing;

-- ============================================================
-- Seed the campuses we're going after next (status: interested)
-- ============================================================
insert into public.institutions (slug, name, short_name, country, status) values
  ('iit-delhi',    'Indian Institute of Technology, Delhi',     'IIT-D',     'IN', 'interested'),
  ('iit-bombay',   'Indian Institute of Technology, Bombay',    'IIT-B',     'IN', 'interested'),
  ('iit-madras',   'Indian Institute of Technology, Madras',    'IIT-M',     'IN', 'interested'),
  ('iit-kanpur',   'Indian Institute of Technology, Kanpur',    'IIT-K',     'IN', 'interested'),
  ('iit-kharagpur','Indian Institute of Technology, Kharagpur', 'IIT-KGP',   'IN', 'interested'),
  ('iit-roorkee',  'Indian Institute of Technology, Roorkee',   'IIT-R',     'IN', 'interested'),
  ('iit-guwahati', 'Indian Institute of Technology, Guwahati',  'IIT-G',     'IN', 'interested'),
  ('iit-hyderabad','Indian Institute of Technology, Hyderabad', 'IIT-H',     'IN', 'interested'),
  ('iit-bhu',      'Indian Institute of Technology (BHU) Varanasi','IIT-BHU', 'IN', 'interested')
on conflict (slug) do nothing;

-- ============================================================
-- Seed three flagship freshman courses at IIT-AD
-- ============================================================
with iit_ad as (select id from public.institutions where slug = 'iit-ad')
insert into public.courses (institution_id, slug, code, name, description)
select iit_ad.id, c.slug, c.code, c.name, c.description from iit_ad, (values
  ('mtl101', 'MTL101', 'Calculus',            'Single & multivariable calculus. The freshman gateway course.'),
  ('mtl102', 'MTL102', 'Linear Algebra & DE', 'Linear algebra and ordinary differential equations.'),
  ('phl101', 'PHL101', 'Mechanics & Waves',   'Classical mechanics and wave physics for freshmen.')
) as c(slug, code, name, description)
on conflict (institution_id, slug) do nothing;

-- ============================================================
-- Auto-assign existing questions to courses by topic.
-- ============================================================
-- Calculus → MTL101
insert into public.course_questions (course_id, question_id)
select c.id, q.id
from public.courses c
join public.institutions i on c.institution_id = i.id
join public.questions q on q.topic = 'Calculus'
where i.slug = 'iit-ad' and c.slug = 'mtl101'
on conflict do nothing;

-- Linear Algebra + DEs → MTL102
insert into public.course_questions (course_id, question_id)
select c.id, q.id
from public.courses c
join public.institutions i on c.institution_id = i.id
join public.questions q on q.topic in ('Linear Algebra', 'Differential Equations')
where i.slug = 'iit-ad' and c.slug = 'mtl102'
on conflict do nothing;
