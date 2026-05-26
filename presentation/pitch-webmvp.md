---
marp: true
theme: default
paginate: true
size: 16:9
title: Amplify — Web
description: 5-minute pitch deck for the karth/web-mvp branch
footer: 'Amplify — Web · ACOP290 Design Practices · IIT-Delhi Abu Dhabi'
style: |
  section {
    font-family: 'Inter', 'Helvetica Neue', system-ui, sans-serif;
    background: #fafaf7;
    color: #1a1a1a;
    padding: 60px 80px;
  }
  h1 {
    font-size: 2.6em;
    letter-spacing: -0.02em;
    margin: 0 0 0.15em 0;
    color: #1a1a1a;
  }
  h2 {
    color: #3b4d7a;
    font-weight: 600;
    font-size: 1.7em;
    letter-spacing: -0.01em;
    margin-bottom: 0.6em;
  }
  h3 {
    color: #555;
    font-weight: 400;
    margin-top: 0;
  }
  strong { color: #d97757; }
  em { color: #555; }
  code {
    font-family: 'JetBrains Mono', 'SF Mono', Menlo, monospace;
    font-size: 0.85em;
    background: #f0efea;
    color: #1a1a1a;
    padding: 0.08em 0.32em;
    border-radius: 3px;
  }
  pre {
    background: #1a1a1a;
    color: #f3f3ef;
    border-left: 3px solid #d97757;
    padding: 1em 1.2em;
    border-radius: 4px;
    line-height: 1.55;
    font-size: 0.78em;
  }
  pre code {
    background: transparent;
    color: inherit;
    padding: 0;
    font-size: inherit;
  }
  blockquote {
    border-left: 4px solid #d97757;
    padding: 0.4em 0 0.4em 1.2em;
    color: #444;
    font-style: italic;
    margin: 1em 0;
    font-size: 0.95em;
  }
  ul.commitments {
    font-size: 1.25em;
    line-height: 1.85;
    list-style: none;
    padding-left: 0;
    margin-top: 0.4em;
  }
  ul.commitments li::before {
    content: "→  ";
    color: #d97757;
    font-weight: 700;
  }
  .timer {
    position: absolute;
    bottom: 22px;
    right: 28px;
    color: #bbb;
    font-size: 0.72em;
    font-variant-numeric: tabular-nums;
    font-family: 'JetBrains Mono', monospace;
  }
  .demo-marker {
    font-size: 6.5em;
    color: #d97757;
    font-weight: 800;
    letter-spacing: -0.05em;
    text-align: center;
    margin: 0.2em 0 0.1em 0;
    line-height: 1;
  }
  .demo-script {
    font-size: 1.1em;
    line-height: 1.7;
    color: #333;
    margin-top: 1.2em;
  }
  .demo-script ol {
    padding-left: 1.4em;
  }
  .punchline {
    font-size: 1.4em;
    color: #1a1a1a;
    font-weight: 500;
    margin-top: 1.2em;
  }
  footer {
    color: #aaa;
    font-size: 0.7em;
  }
  section::after {
    color: #aaa;
    font-size: 0.7em;
  }
  .themes {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.85em;
    color: #666;
    margin-top: 1.5em;
    line-height: 1.8;
  }
  .signature {
    color: #888;
    font-size: 0.9em;
    margin-top: 0.8em;
  }
  .problem-cols {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 2.2em;
    margin-top: 0.4em;
  }
  .problem-cols h3 {
    color: #3b4d7a;
    margin: 0 0 0.4em 0;
    font-size: 1.15em;
    font-weight: 600;
    border-bottom: 2px solid #d97757;
    padding-bottom: 0.2em;
    display: inline-block;
  }
  .problem-cols ul {
    font-size: 0.95em;
    line-height: 1.55;
    color: #333;
    padding-left: 1.1em;
    margin-top: 0;
  }
  .problem-cols ul li { margin-bottom: 0.25em; }
---

## The problem

<div class="problem-cols">
<div>

### Students

- PDF from a Dropbox folder
- Write in a notebook
- Wait for the TA session to know if they were right
- No record of what's been practiced, or where the gaps are

</div>
<div>

### Faculty

- Copy-paste last year's `.tex`, swap a few numbers
- 30 minutes per genuinely new question
- No version control, no peer review
- Same 200 questions cycle every semester

</div>
</div>

<div class="punchline">There is no shared place to put new problems.</div>

<!--
SAY: Every freshman at IIT-AD practices the same way — PDF from a Dropbox
folder, notebook, wait for the TA session. No instant feedback, no record
of what they've practiced. Faculty have it worse: thirty minutes to author
a single new question, no peer review, the same two hundred questions
cycle every semester because there's no shared place to add new ones.

Next: what we committed to building against it.
-->

---

# Amplify — Web

### Practice STEM problems the way they should be practiced.

<ul class="commitments">
<li>Works in a phone browser on a slow connection</li>
<li>One URL per question, forever</li>
<li>Authorization in the <strong>database</strong>, not the route handler</li>
<li>Mastery is a <strong>Bayesian posterior</strong>, not a counter</li>
<li>The seed is <strong>idempotent</strong></li>
</ul>

<!--
SAY: That's the problem we set ourselves. Here are the five non-negotiables
we built the architecture around. The rest of the deck is how each one
gets honored.
-->

---

<div class="demo-marker">DEMO</div>

<div class="demo-script">

1. `/q/<id>` on a fresh browser — math renders, no auth, **permalink works**
2. **Pull out the phone.** Same URL. Same render.
3. `/practice` → pick filters → answer two questions → self-assess a proof
4. `/me` → mastery posterior visibly shifted for one subtopic

</div>

<!--
Pre-warm the Vercel deploy 30s before going up.
Phone moment is the load-bearing beat — physically pull it from your pocket.
Have a 60s pre-recorded screen capture one keystroke away in case Vercel cold-starts.
-->

---

## Authorization in the database

```
Browser  ─[anon cookie OR session JWT]─▶  Next.js (RSC + API routes)
                                                   │
                                                   ▼  per-user Supabase client
                                            Postgres  +  RLS
                                                   ▲
                                  auth lives here — not in route handlers
```

<div class="punchline">The API doesn't check permissions. <strong>The database does.</strong></div>

<!--
Row-level security policies decide which rows a user can read. The route
handler never has access to data the user shouldn't see — so it can't
accidentally leak it. That's what makes the multi-tenant model trustworthy
without writing security code in every endpoint.
-->

---

## Same spec, different architecture

```
                ┌─── PyWebView + SQLite + XeLaTeX   (desktop · 14 steps)
  Same Spec ────┤
                └─── Next.js + Supabase + KaTeX     (web · 9-step sprint)
```

Spec stays the source of truth. The stack and the build cycle don't.

<!--
Joel wrote the spec for an offline desktop tool. I re-targeted it for the
web — same product goals, different constraints, completely different stack.
The dev cycle compressed from fourteen desktop steps into a 9-step web sprint.
-->

---

## Mastery is a posterior

```ts
// lib/mastery.ts
export interface BetaPrior {
  alpha: number; beta: number; total_seen: number;
}

export function updateMastery(prior, outcome) {
  return {
    alpha: prior.alpha + outcome.correct,
    beta:  prior.beta  + outcome.incorrect,
    total_seen: prior.total_seen + 1,
  };
}

// "Weakest topic" ranking uses (mean − 1 SD), not raw mean —
// so a 0/0 prior can't beat a 5/5 prior.
```

Per **(user × topic × branch × subtopic)**. Empty-state when there's no evidence, instead of pretending 50%. Unit-tested.

<!--
Mastery is a Beta posterior, not a percentage. The estimate tightens as
evidence accumulates. The "weakest topic" ranking uses the lower credibility
bound — penalises uncertainty so a freshly-seen topic doesn't outrank a
well-evidenced one. Real statistics, properly tested.
-->

---

## The anon-to-auth seam

```
Anonymous  →  cookie UUID  →  personal mastery
                  │
                  ▼  user clicks "Sign in"
              magic link  →  UUID promoted to user_id  →  state persists
```

Most apps lock everything behind auth, or skip auth entirely.
<span class="punchline"><strong>Friction is opt-in.</strong></span>

<!--
Anonymous users get personal mastery via a cookie UUID. Signing in
promotes that UUID to a real account — no data lost. That's how you
earn the first session without giving up personalization on the second.

This is the design-practices money slide: a deliberate seam between
"trustless onboarding" and "trusted account." Most peers will not have
considered this seam at all.
-->

---

## What we hand the faculty

> We want to pilot Amplify in **one course this fall** — ideally MTL101
> (Calculus). A custom-branded problem-bank, free, forever. Aggregate
> dashboards: which topics your cohort struggles with, in real time,
> **before the midterm.**

<div class="signature">— <code>PITCH.md</code>, one page, signed by the team.</div>

<div class="themes">
9 themes shipped: <code>android-kitkat</code> · <code>ascii</code> · <code>comic</code> · <code>default-dark</code> · <code>default-light</code> · <code>frutiger-aero</code> · <code>pastel</code> · <code>pixel-art</code> · <code>windows-xp</code>
</div>

<!--
Final artifact isn't the app — it's this one-page faculty pitch. We want a
course pilot in the fall. That closes the design-practices loop: build the
thing, write the pitch, hand it to the user.

Also: nine themes. Flick through them on the live app as your last beat if
there's time. Sit down.
-->
