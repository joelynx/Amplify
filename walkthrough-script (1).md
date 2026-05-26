# Amplify Web — Live Walkthrough Script

A scene-by-scene script for narrating the live app at `https://amplify-karth.vercel.app`. Each scene tells the story of one feature and the problem it solves. The middle scenes are the user demo; Scenes 7 and 8 step back to explain the architecture and the next-semester pilot. Default runtime ~10–11 minutes; cuttable to ~6 minutes via the cut order at the end.

---

## Speaker split

Two presenters: **Karthik** (pitch, UX, faculty perspective) and **Joel** (vectorization, DPP, mastery — all the math).

| Scene | Presenter | Notes |
|---|---|---|
| 1 — Cold open | Karthik | Problem framing |
| 2 — Permalink + KaTeX | **Karthik → Joel** | Karthik does the UI demo through "reveal solution"; Joel takes over for the "similar questions" cosine-KNN beat |
| 3 — Filter form | **Karthik → Joel** | Karthik does topic tree / tags / types; Joel takes the Random vs Diverse mode toggle |
| 4 — Runner | Karthik | UX of auto-grade and self-assess |
| 5 — Mastery dashboard | Joel | Beta posterior + lower credibility bound |
| 6 — Faculty author | Karthik | Closes with "stored after vectorizing" — natural setup for Joel's Scene 7 |
| 7 — Under the hood | Joel | Vectors / KNN / DPP / Beta math |
| 8 — Vision | Karthik | Pilot pitch |
| 9 — Closing flourish | **Karthik → Joel** | Karthik cycles themes; Joel delivers the final line |

Mid-scene handoffs (Scenes 2, 3, 9) are marked inline with **Hand off** lines. Trade off at those exact points; don't try to interrupt mid-beat. Approximate speaking time works out to ~5 min each.

---

## Pre-flight (do this 60 seconds before you start)

1. **Pre-warm Vercel.** Hit `amplify-karth.vercel.app` so the landing page is cached. Cold starts will kill the opener.
2. **Pre-populate the demo account.** Sign in as a test student and answer 5–10 questions across 3–4 subtopics, so `/me` shows real mastery and the landing page's personalized banner is non-empty.
3. **Pre-stage tabs.** Have four tabs open and ready:
   - `/` (landing)
   - `/q` (browse) — and one good question permalink, e.g. `/q/<id>` with a populated solution + similar questions
   - `/practice` — with a few filters pre-clicked but session not yet started
   - `/me` — populated
4. **Have a phone in your pocket** with `amplify-karth.vercel.app/q/<same-id>` already loaded.
5. **Have `/about` open in a backup tab** — Scene 7 can use the stack list as a visual anchor when you're explaining the vector-first architecture.

---

## Scene 1 — The cold open (~30s)

**Presenter:** Karthik

**URL:** `https://amplify-karth.vercel.app`

**On screen:** Landing page. Hero reads *"The problem-bank commons for university STEM."* Public stats strip below: `401 questions · 1 institution · 1 faculty · 8 sessions this week`.

**Pause 3 seconds. Let them read.**

**Say:**
> Every freshman at IIT-AD practices the same way — they hunt for a PDF in a Teams or blackboard folder, work the questions in a notebook, and wait until the next tutorial session to find out if they were right and get feedback. They don't have any record of what they've practiced unless they manually keep tabs.
>
> This is Amplify. It's hosted, it's live, it has 401 curated questions right now. I'll walk you through what a student would actually do to use it.

---

## Scene 2 — One question is a URL (~1m)

**Presenter:** Karthik (then hand off to Joel for the similar-questions beat)

**Click:** `Browse` in the nav → `/q`

**On screen:** *"Browse the bank. 401 curated questions. Every one is a permalink."* Topic filter chips at the top, paginated cards below.

**Say:**
> Every question in the bank is a permalink. You can paste the link anywhere and anyone will be able to see the question that you're referring to.

**Click:** A topic chip (e.g., **Calculus**) to filter the list.

**Click into one question card.**

**On screen:** Single-question page. LaTeX rendered. Breadcrumb shows `Topic › Branch › Subtopic`. Type / source / difficulty pills below. *"▸ Reveal solution"* button collapsed.

**Say:**
> Math renders in the browser itself via KaTeX. 

**Click:** *"▸ Reveal solution"*

**On screen:** Solution unfolds beneath the question.

**Say:**
> The solution for the question is hidden by default so the student isn't tempted to peek. One click reveals the canonical answer and the worked solution.

**Hand off:** Karthik → Joel.

**Scroll down to "Similar questions."**

**Say:**
> And down here there are six similar questions, ranked by cosine similarity over the vector embeddings of the question text. If a student finishes this one and wants more practice on the same idea, the next six are already chosen for them. We did this by passing all the question-solution pairs into an embeddings model, (We used Gemini Embeddings 001), and then doing nearest neighbor search using cosine similarity as the distance metric. The similarity score is nothing but the normalized dot product of the two question vectors.

**Click one similar question** to show the navigation. Then click back.

---

## Scene 3 — Setting up a practice session (~1m)

**Presenter:** Karthik (then hand off to Joel for the mode toggle)

**Click:** `Practice` in nav → `/practice`

**On screen:** Filter form. Topic tree on top-left. Type / source / tag / mode / size below. A live *"X matching questions"* counter.

**Say:**
> Now suppose the student has a quiz on a specific topic that they have learnt, the next day. They can selectively practice topics and subtopics of their choosing using this user interface.

**Demonstrate the topic tree:** click **Calculus**. Watch every subtopic underneath get checked.

**Say:**
> The topic tree is tri-state. Click a topic once and every subtopic underneath is selected; click it again to clear. The matching-question count at the bottom updates live as I add filters. We made it a tree so that at each step the user is only exposed to as much depth as they wish to see.

**Demonstrate tags:** click a tag once (compulsory), then again (excluded), then again (off).

**Demonstrate types:** Select only Proof Questions

**Say:**
> Tags are tri-state too, they're either required, excluded, or ignored. So you can say "give me Calculus questions but skip the proof-heavy ones." Try doing that with a PDF.

**Hand off:** Karthik → Joel.

**Point at the mode toggle:** `Random` vs `Diverse`.

**Say:**
> Two modes. Random is a uniform shuffle of all questions meeting the filter criteria. Diverse uses a determinantal point process over the question embeddings to maximize coverage, so if you ask for ten questions, you get ten *across* the topic space, not ten from one subtopic. We show the diversity score on the next page so you can see it working.

**Set:** Session size = `5` (small for demo). **Click** *"Start practice."*

---

## Scene 4 — Inside the runner (~2m)

**Presenter:** Karthik

**On screen:** `/practice/<sessionId>`. Progress `1/5`, score `0 pts`, diversity badge *"Diverse session · diversity 0.34"*. First question rendered.

**Say:**
> One question at a time. Progress counter, score, diversity badge top-right.

**Say:**
> Proofs and explanations don't have a canonical answer in a meaningful sense, so we can't auto-grade them. Instead the student writes down their key idea, reveals the solution, and self-assesses.

**Click *Reveal solution*.** Then **click *Partial*** from the *Got it / Partial / Missed* row.

**Say:**
> The mastery update is weighted according to how the user self evaluates their performance in this question. one point of evidence for "got it," half a point for "partial," none for "missed." It's honest about what auto-grading can and can't do.

**Burn through the remaining questions quickly. Land on the "Session done" screen.**

**On screen:** *"Session done."* Score / accuracy / "start another" / "print" / "see mastery" CTAs.

**Say:**
> Session done. Score, accuracy, options to start another, print as a PDF if you want to do this offline, or go look at your mastery.

---

## Scene 5 — What the student now knows about themselves (~1m)

**Presenter:** Joel

**Click *See mastery*** → `/me`

**On screen:** Mastery dashboard. Headline cards (`Questions answered` / `Overall accuracy` / `Subtopics touched`). *"Your strongest"* and *"Your weakest"* lists below.

**Say:**
> This is the page that doesn't exist anywhere else in a student's life. Per subtopic, here's what they're strong at and what they need to work on.

**Point at the *Your weakest* list.**

**Say:**
> The important thing to notice here is that we're not just sorting by raw accuracy. A subtopic with one question right out of one attempted (accuracy 100%) shouldn't outrank a student who got nine right out of ten attempted  (accuracy 90%). So we model each subtopic as a Beta distribution, where we increment the α parameter for correct answers, and the β for incorrect. The mean of the distribution STILL matches raw accuracy, `α/(α+β)`, BUT we rank 'weakest' by the 'lower credibility bound', which is the mean minus one standard deviation. This effectively penalizes low evidence which will have high standard deviation, which is negatively weighted.

**Click back to** `/`.

**On screen:** Landing page. The personalized banner near the top reads *"Your weakest right now: [subtopic] · [subtopic] · [subtopic]"* with a *Practice these →* button.

**Say:**
> Next time the student lands on the homepage, we tell them where to focus. One click, and they get a session pre-filtered to their three weakest subtopics.

---

## Scene 6 — The faculty pivot (~1.5m)

**Presenter:** Karthik

**Click:** `Author` in nav → `/author`

**On screen:** Two-column form. Left: inputs (topic, branch, subtopic, type, LaTeX, answer, solution, source, course). Right: live LaTeX preview.

**Say:**
> Now on the other side, when a professor or TA wants to add a question, this is the author page. Topic, branch, subtopic, type. We have raw LaTeX in the textarea on the left, rendered preview on the right, which is the same renderer that the student will see.

**Type a small LaTeX expression into the question textarea**, e.g. `\int_0^1 x^2 \, dx`. Watch the preview update in real time.

**Say:**
> After the question is written, it gets stored in the database after getting vectorized.

---

## Scene 7 — Under the hood: vectors, not LLMs (~2.5m)

**Presenter:** Joel

**Pause the live walkthrough.** Optionally click to `/about` to use the stack list as a visual anchor — *"Next.js 15, Supabase Postgres with pgvector (HNSW), Gemini text-embedding-001 (768 dims, Matryoshka), Bayesian Beta posteriors, determinantal point processes, KaTeX, D3."*

**Say:**
> Everything you just saw — instant feedback, similarity recommendations, diverse session generation, mastery tracking — **none of it calls an LLM at runtime.** No API key in the request path, no rate limit, no per-request cost, no behavior drift when a model gets deprecated. Here's why.

*Pause. Let the implication land.*

**Say:**
> The expensive thing is *understanding* a question — what concept it tests, how it relates to other questions. We do that work **once**, offline, at ingest time. Every question in the bank gets embedded by Google's Gemini text-embedding model into a **768-dimensional vector**. Questions that test the same idea end up close together in that space; questions that test different ideas end up far apart.
>
> Those vectors live in Postgres using **pgvector with an HNSW index** — Hierarchical Navigable Small Worlds, an approximate-nearest-neighbor graph. Finding the K closest questions to any given one is a millisecond-level Postgres query, not a network call.
>
> Once you have that, everything you just saw becomes a small piece of math.


**Say:**
> **The "similar questions" panel** at the bottom of every question page — that's cosine-similarity KNN against the HNSW index. Give me the six vectors closest to this one. Done.
>
> **The "diverse" practice mode** — that's a **Determinantal Point Process** over the embeddings. The intuition: if you sample ten questions uniformly at random, you might get ten about limits and nothing else. A DPP samples subsets weighted by the **determinant** of the gram matrix of the selected vectors. Geometrically, the determinant is the **volume** those vectors span — so subsets that point in more different directions in concept space get sampled more often. The "diversity score" we show in the session header is that determinant, normalized. It's a number you can put a finger on.
>
> **The mastery model** isn't embedding-based, but it shares the philosophy — closed-form math, not inference loops. Beta(α, β) posterior per subtopic, conjugate updates. The "weakest topics" ranking uses the lower credibility bound — mean minus one standard deviation — which is two lines of code and prevents a one-out-of-one record from outranking a nine-out-of-ten record.
>
> The only place a model gets called is **at ingest** — when a new question is authored, we embed it once and store the vector. That's a one-time cost per question, amortized over every student who ever practices it. At runtime, this app is **Next.js doing vector math in Postgres.**

---

## Scene 8 — The vision: Calculus, next semester (~1m)

**Presenter:** Karthik

**Click to** `/q?topic=Calculus` — the browse page filtered to Calculus is the visual anchor.

**Say:**
> So — where does this go from here?
>
> The MVP you just walked through is completely set up for **Calculus,** which is a standard first-semester course at IIT-AD. Every question in the bank is curated, every one is embedded, every one is browseable, practiseable, and can contribute to mastery scores.

*Gesture at the populated browse page.*

**Say:**
> The next intake of freshers arrives next semester. We want them to walk in on day one, sign in with their institute email, and find an instant-feedback Calculus practice tool already waiting for them. Not "coming soon." 
>
> And as faculty start contributing, by adding new questions, peer-reviewing each other's drafts, retiring stale ones the same pipeline embeds those new questions automatically and they join the same vector space. The similar-question recommendations sharpen. The diversity sampling has more material to spread across. **The database gets better every semester instead of stagnating like a static one**
>
> That's the pilot we're pitching One course, real students, real measurements, before the midterm. If it works for Calculus, the same engine works for Linear Algebra, for Mechanics, for any subject whose questions can be typeset.

---

## Scene 9 — The closing flourish (~30s)

**Presenter:** Karthik (then hand off to Joel for the final line)

**Click the theme glyph in the top-right nav.**

**On screen:** Theme dropdown opens. Nine themes listed.

**Say:**
> One last thing. Nine themes ship. Default light, default dark — those are the serious ones. And then —

**Click through quickly:** Frutiger Aero → Windows XP → Pixel Art → Comic → ASCII. Pause ~1 second on each so the audience sees the chrome shift.

**Say:**
> Frutiger Aero. Windows XP. Pixel Art. Comic Sans. ASCII. Same IPC contract behind all of them, so adding a theme is one CSS file. Mostly we did this for fun.
>

**Hand off:** Karthik → Joel.

**Switch to a tasteful theme (default-light or pastel). Land on `/` or `/me` for a clean closing screen.**

**Say:**
> That's Amplify. A permalink per question, instant feedback, mastery tracking that's honest about uncertainty, faculty visibility before the midterm, and a Calculus bank that's ready for next semester's intake. Questions?

---

## Cut order if you're short on time

The default script runs ~10–11 minutes at a brisk pace. If you have less, cut in this order:

1. **First out:** Scene 9 (themes flourish) — close on Scene 8 instead. *Saves ~30s.*
2. **Then:** Trim Scene 7 — drop the DPP-determinant explanation and the grader bullet; keep just *"vectorize once, store, KNN and DPP are math, no LLM at runtime."* *Saves ~1m.*
3. **Then:** Compress Scene 6 to faculty dashboard only, skip the author form. *Saves ~45s.*
4. **Then:** Trim Scene 4 by skipping the proof self-assessment beat — only show the numerical auto-grade. *Saves ~30s.*

**Never cut Scenes 4, 5, 7, or 8.** The runner, the mastery dashboard, the "no LLM at runtime" thesis, and the next-semester pilot pitch are the load-bearing pieces — everything else supports them.

**Five-minute version (tight):** Scenes 1, 2 (skip phone flex), 3, 4 (numerical only), 5, a compressed 60-second Scene 7 (vectors-once + KNN + closed-form math, no DPP detail), and Scene 8. Lands around 5:30–6:00. Drops the faculty pivot and the themes; everything that remains is **problem → demo → thesis → pilot ask.**

---

## Backup plan if a live click fails

- **Vercel cold-start during opening:** stall by reading the public-stats numbers aloud while it loads ("Four hundred and one questions, one institution, one faculty, eight sessions this week — that last one is going to be more after this talk").
- **A page errors out:** switch to the pre-staged backup tab for that page. Say *"Let me grab the version I had open earlier"* — sounds like a deliberate pace beat, not a failure.
- **The grader marks your answer wrong when you typed it right:** lean in. *"This is actually a good demo — `looselyEqual` has a tolerance of 10⁻³, so if I round wrong it'll catch me."*
- **Theme switcher misfires:** skip Scene 9 entirely and close on Scene 6's faculty pivot.
