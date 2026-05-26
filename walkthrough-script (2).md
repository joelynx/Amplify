# Amplify Web — Walkthrough Script

Two presenters: **Karthik** (talks only) and **Joel** (drives the laptop, talks the math). Start at `https://amplify-karth.vercel.app`, logged out. Have a second **incognito window** pre-opened and signed in as a TA/faculty user, parked on `/author`. The demo student credentials are `demo.student@iitdabudhabi.ac.ae` / `amplify-demo-2026`; the TA is `demo.ta@iitdabudhabi.ac.ae` / `amplify-demo-2026`.

---

## Scene 1 — Cold open (~30s)

Stay on the landing page. Don't click anything.

**Karthik:**
> Every freshman at IIT-AD practices the same way — they hunt for a PDF in a Teams or Blackboard folder, work the questions in a notebook, and wait until the next tutorial session to find out if they were right and get feedback. They don't have any record of what they've practiced unless they manually keep tabs.
>
> This is Amplify. It's hosted, it's live, and it has over 400 curated questions right now. I'll walk you through what a student would actually do to use it.

---

## Scene 2 — Sign in (~20s)

Click **Sign in to practice** → on `/auth/login`, type the demo student email and password → click **Sign in** → land on `/me`.

**Karthik:**
> Sign-in is your institute email and a password — no inbox detour, no third-party SSO. Every practice session and every mastery measurement is tied to your account from the first question on.

---

## Scene 3 — One question is a URL (~1m)

Click **Browse** → `/q`. Click a topic chip (e.g., **Calculus**). Click into one question card.

**Karthik:**
> Every question in the bank is a permalink. You can paste the link anywhere and anyone will be able to see the question you're referring to. Math renders in the browser itself via KaTeX.

Click **▸ Reveal solution**.

**Karthik:**
> The solution is hidden by default so the student isn't tempted to peek. One click reveals the canonical answer and the worked solution.

Scroll down to **Similar questions**.

**Joel:**
> Down here there are six similar questions, ranked by cosine similarity over the vector embeddings of the question text. We did this by passing all the question-solution pairs into an embeddings model — we used Gemini Embeddings 001 — and then doing nearest neighbour search using cosine similarity as the distance metric. The similarity score is the normalised dot product of the two question vectors.

Click one of the similar questions, then click back.

---

## Scene 4 — Setting up a practice session (~1m)

Click **Practice** → `/practice`.

**Karthik:**
> Now suppose the student has a quiz on a specific topic the next day. They can selectively practice topics and subtopics using this form.

In the topic tree, click **Calculus** so every subtopic underneath gets selected.

**Karthik:**
> The topic tree is tri-state. Click a topic once and every subtopic underneath is selected; click again to clear. The matching count at the bottom updates live. We made it a tree so at each step the user is only exposed to as much depth as they wish to see.

In the **Tags** combobox, type a tag fragment, pick one from the dropdown — it lands in the chip tray as a green compulsory chip. Click the chip body once to flip it to red excluded; click again to flip back. Use the × on the chip to remove it. Then select only **Proof** under types.

**Karthik:**
> Tags are tri-state — compulsory, excluded, or removed. So you can say "give me Calculus questions but skip the proof-heavy ones." Try doing that with a PDF.

Point at the **Random / Diverse** mode toggle.

**Joel:**
> Two modes. Random is a uniform shuffle of all questions meeting the filter criteria. Diverse uses a determinantal point process over the question embeddings to maximise coverage — so if you ask for ten questions, you get ten *across* the topic space, not ten from one subtopic. We show the diversity score on the next page so you can see it working.

Set the session size to **5**. Click **Start practice**.

---

## Scene 5 — Inside the runner (~2m)

Let the first question load.

**Karthik:**
> One question at a time. Progress counter, score, diversity badge in the header.

For a proof question, type a brief idea or leave it blank. Click **Reveal solution**. Then click **Partial**.

**Karthik:**
> Proofs and explanations don't have a canonical answer in a meaningful sense, so we can't auto-grade them. Instead the student writes down their key idea, reveals the solution, and self-assesses. One point of evidence for "got it," half a point for "partial," none for "missed." It's honest about what auto-grading can and can't do.

Burn through the remaining questions. Land on the **Session done** screen.

**Karthik:**
> Session done. Score, accuracy, options to start another, print as a PDF, or go look at your mastery.

---

## Scene 6 — Mastery dashboard (~1m)

Click **See mastery** → `/me`.

**Joel:**
> This is the page that doesn't exist anywhere else in a student's life. Per subtopic, here's what they're strong at and what they need to work on.
>
> The important thing to notice is that we're not just sorting by raw accuracy. A subtopic with one right out of one attempted shouldn't outrank a student who got nine right out of ten. So we model each subtopic as a Beta distribution — we increment the α parameter for correct answers and β for incorrect. The mean of the distribution still matches raw accuracy, α over α plus β. But we rank "weakest" by the **lower credibility bound** — the mean minus one standard deviation. That penalises low evidence. A single attempt has high variance, which pulls its LCB away from the mean. "Weakest" really means weakest.

Click back to `/`.

**Joel:**
> Next time the student lands on the homepage, we tell them where to focus. One click and they get a session pre-filtered to their three weakest subtopics.

---

## Scene 7 — Faculty/TA side (~1.5m)

Switch to the **incognito window** (already signed in as a TA). You should already be on `/author`. If not, click **Author** in the nav.

**Karthik:**
> Now on the other side, when a professor or TA wants to add a question, this is the author page. Topic, branch, subtopic, type. Raw LaTeX in the textarea on the left, rendered preview on the right — the same renderer the student sees.

Type `\int_0^1 x^2 \, dx` into the question textarea and let the preview update.

**Karthik:**
> After the question is written, it gets stored in the database after being vectorised.

---

## Scene 8 — Under the hood (~2.5m)

Optionally click to `/about`. Otherwise stay where you are.

**Joel:**
> Everything you just saw — instant feedback, similarity recommendations, diverse session generation, mastery tracking — none of it calls an LLM at runtime. No API key in the request path, no rate limit, no per-request cost, no behaviour drift when a model gets deprecated. Here's why.
>
> The expensive thing is *understanding* a question — what concept it tests, how it relates to other questions. We do that work **once**, offline, at ingest time. Every question gets embedded by Google's Gemini text-embedding model into a 768-dimensional vector. Questions that test the same idea end up close together; questions that test different ideas end up far apart.
>
> Those vectors live in Postgres using **pgvector with an HNSW index** — Hierarchical Navigable Small Worlds, an approximate-nearest-neighbour graph. Finding the K closest questions to any one of them is a millisecond-level Postgres query, not a network call.
>
> Once you have that, everything you saw becomes a small piece of math.
>
> The **"similar questions" panel** is cosine-similarity KNN against the HNSW index. Give me the six vectors closest to this one. Done.
>
> The **"diverse" practice mode** is a Determinantal Point Process over the embeddings. A DPP samples subsets weighted by the *determinant* of the gram matrix of the selected vectors. Geometrically, the determinant is the *volume* those vectors span — so subsets that point in more different directions in concept space get sampled more often. The diversity score we show is that determinant, normalised.
>
> The **mastery model** isn't embedding-based, but it shares the same philosophy — closed-form math, not inference loops. Beta posterior per subtopic, conjugate updates, lower credibility bound for ranking weakness.
>
> The only place a model gets called is at ingest. At runtime, this is Next.js doing vector math in Postgres.

---

## Scene 9 — Vision: Calculus, next semester (~1m)

Switch back to the main window. Navigate to `/q?topic=Calculus`.

**Karthik:**
> Where does this go from here?
>
> The MVP you just walked through is completely set up for **Calculus** — a standard first-semester course at IIT-AD. Every question in the bank is curated, embedded, browseable, practiseable, and contributing to mastery scores.
>
> The next intake of freshers arrives next semester. We want them to walk in on day one, sign in with their institute email, and find an instant-feedback Calculus practice tool already waiting for them. Not "coming soon."
>
> And as faculty start contributing — adding new questions, peer-reviewing each other's drafts, retiring stale ones — the same pipeline embeds those new questions automatically and they join the same vector space. The similar-question recommendations sharpen. The diversity sampling has more material to spread across. **The database gets better every semester instead of stagnating like a static one.**
>
> That's the pilot we're pitching. One course, real students, real measurements, before the midterm. If it works for Calculus, the same engine works for Linear Algebra, for Mechanics, for any subject whose questions can be typeset.

---

## Scene 10 — Closing flourish (~30s)

Click the theme glyph in the top-right nav. Cycle through Frutiger Aero → Windows XP → Pixel Art → Comic → ASCII, ~1 second on each.

**Karthik:**
> One last thing. Nine themes ship. Default light, default dark are the serious ones. And then — Frutiger Aero. Windows XP. Pixel Art. Comic Sans. ASCII. Same IPC contract behind all of them, so adding a theme is one CSS file. Mostly we did this for fun.

Switch to a tasteful theme. Land on `/` or `/me`.

**Joel:**
> That's Amplify. A permalink per question, instant feedback, mastery tracking that's honest about uncertainty, faculty visibility before the midterm, and a Calculus bank that's ready for next semester's intake. Questions?
