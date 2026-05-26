# Amplify

> Practice STEM problems the way they should be practiced. Built at IIT-Delhi Abu Dhabi.

A web-based practice tool for university-grade math, physics, and CS problems. LaTeX-typeset questions rendered in the browser, filter by subtopic, grade yourself, watch your per-subtopic mastery score climb.

- **Live:** *(URL after first Vercel deploy)*
- **Spec docs:** [`Files/AMPLIFY_BUILD_SPEC (3).md`](./Files/AMPLIFY_BUILD_SPEC%20(3).md), [`Files/AMPLIFY_DEV_CYCLE.md`](./Files/AMPLIFY_DEV_CYCLE.md)
- **Faculty pitch:** [`PITCH.md`](./PITCH.md)

## Stack

- **Frontend:** Next.js 15 (App Router) + Tailwind + React 19
- **Backend:** Supabase Postgres + Auth + RLS, accessed via Next.js API routes
- **Math rendering:** KaTeX in the browser (no XeLaTeX install required)
- **Tests:** Vitest for pure functions (grader, mastery math, LaTeX renderer)
- **Deploy:** Vercel

## Setup (first-time, ~10 min)

### 1. Create a Supabase project

1. Go to <https://supabase.com/dashboard/new>, sign in with GitHub.
2. New project → name `amplify` → strong DB password → region **South Asia (Singapore)** is closest to Abu Dhabi.
3. Wait ~2 min for provisioning.

### 2. Plug in env vars

In your project's **Settings → API**, copy these three values into `.env.local`:

```bash
NEXT_PUBLIC_SUPABASE_URL=https://<your-ref>.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=<the long "anon" key>
SUPABASE_SERVICE_ROLE_KEY=<the long "service_role" key — KEEP SECRET>
```

(`.env.local` is gitignored.)

### 3. Run the migration

In the Supabase dashboard: **SQL Editor → New query**. Paste the entire contents of [`supabase/migrations/0001_initial.sql`](./supabase/migrations/0001_initial.sql) and click **Run**. You should see "Success. No rows returned."

### 4. Import the seed bank

```bash
npm install
npm run seed
```

This reads `Files/TEST.csv` (~400 curated questions from IITD-AD, IITD, IITM, IITK, and the Kaczor-Nowak textbook), dedupes by LaTeX hash, and inserts. Re-running is safe — duplicates are skipped.

Dry-run mode prints stats without writing to the DB:

```bash
npm run seed -- --dry-run
```

### 5. Start the dev server

```bash
npm run dev
```

Open <http://localhost:3000>. You should be able to:

- Browse the bank at `/q`
- Start a practice session at `/practice`
- Sign in via magic link and see mastery at `/me`

## Deploying to Vercel

1. `git push -u origin karth/web-mvp` (or whichever branch).
2. <https://vercel.com/new> → import the GitHub repo.
3. Add the same three env vars from `.env.local` to the Vercel project's **Settings → Environment Variables**.
4. Deploy. Subsequent pushes auto-deploy.
5. Back in Supabase: **Authentication → URL Configuration** → set **Site URL** to your Vercel URL so magic-link emails redirect correctly.

## Project structure

```
app/
├── page.tsx                  # landing
├── q/                        # public question viewer + browse
│   ├── page.tsx              # /q  — paginated list
│   └── [id]/page.tsx         # /q/[id] — single question permalink
├── practice/
│   ├── page.tsx              # filter form
│   └── [sessionId]/page.tsx  # runner
├── me/page.tsx               # mastery dashboard (auth required)
├── auth/{login,callback,signout}/
└── api/
    ├── questions/count/      # POST live counter
    └── sessions/             # POST create, GET state, POST answer

components/
└── nav.tsx                   # global nav

lib/
├── supabase/{server,browser,admin}.ts   # SSR + browser + service-role clients
├── katex.ts + katex.tsx                 # pure render + React wrapper
├── grade.ts                             # looselyEqual: numeric/string comparison
├── mastery.ts                           # Bayesian beta posterior + update
├── queries.ts                           # filter assembly, random picking
├── anon.ts                              # anonymous session key
└── db/types.ts                          # hand-written DB types

supabase/migrations/0001_initial.sql     # schema + RLS

scripts/seed.ts                          # CSV → DB import (idempotent)

Files/                                   # source-of-truth spec docs from Joel
└── AMPLIFY_BUILD_SPEC (3).md, AMPLIFY_DEV_CYCLE.md, TEST.csv
```

## Scripts

| Command | What |
|---|---|
| `npm run dev` | Next.js dev server with HMR |
| `npm run build` | Production build |
| `npm run start` | Run the production build locally |
| `npm test` | Run vitest suite |
| `npm run test:watch` | Vitest watch mode |
| `npm run seed` | Import `Files/TEST.csv` into Supabase |
| `npm run seed -- --dry-run` | Parse only; print stats |
| `npm run lint` | ESLint |
| `npm run types` | Regenerate `lib/db/types.ts` from local Supabase (requires Supabase CLI) |

## Data model (short version)

`questions` — three-level taxonomy (topic → branch → subtopic), per-question `in_syllabus` flag, type ∈ {proof, numerical, explanation/reasoning}, optional canonical answer + solution.

`practice_sessions` — one per "Start practicing" click. Owned by user_id (signed in) or anon_key (cookie-stored UUID).

`practice_responses` — one row per question in a session. The user's answer, whether it was correct (or null if not gradeable), time taken.

`user_mastery` — Bayesian Beta(α, β) per (user, topic, branch, subtopic). Updated on every answer. `α` increments on correct, `β` on incorrect; partial credit splits.

Full schema lives in [`supabase/migrations/0001_initial.sql`](./supabase/migrations/0001_initial.sql) with RLS policies (questions are public-read; sessions and mastery are own-row-only).

## What's done vs deferred

**MVP done:**

- Magic-link auth, public question viewer, paginated browse, filter-driven practice loop, self-assessment for non-gradeable questions, Bayesian mastery dashboard.

**Deferred (post-MVP):**

- Authoring page (`/author`) — let professors add questions in-browser
- Embeddings + similarity search via `pgvector` and `gemini-embedding-002`
- Server-side LaTeX → PDF export (Tectonic)
- Subjects-as-bundles (the "MTL101 Calculus" curricular subject model from the spec)
- Themes, PBS quiz mode, Smart Difficulty — all on the long roadmap

See [`Files/AMPLIFY_DEV_CYCLE.md`](./Files/AMPLIFY_DEV_CYCLE.md) for the full step-by-step build order from Joel's original spec; this web rewrite collapsed steps 1–14 of that plan into a tighter 9-step 48-hour sprint.

## License

MIT — see [`LICENSE`](./LICENSE).
