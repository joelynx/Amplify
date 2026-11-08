# Low-Hanging Fruit for Amplify

This review covers the practice flows, selection algorithms, stats, embeddings, themes, and solution-pipeline documentation. The repository review was read-only; no application code was changed.

My strongest recommendation is to build a simple daily practice loop: **choose relevant questions → attempt them → get feedback → revisit them later.** The repository already has much of the infrastructure. The keyword idea would make starting easier; better stats and a review queue would make subsequent sessions more useful.

Here is how I would prioritise the additions. Effort refers to a deliberately small first version.

| Priority | Feature | Relative effort |
|---|---|---|
| 1 | Review missed and partially solved questions | Small |
| 2 | Stats based on actual answers, with useful next actions | Small–medium |
| 3 | Paste lecture keywords and start practice | Small with aliases; medium with semantic retrieval |
| 4 | Mixed review across previously studied techniques | Small |
| 5 | Short self-explanation prompts after solutions | Small |
| 6 | Earnable theme customisations | Small for milestones; medium for a currency |

## 1. A review queue is probably the best return on implementation effort

The [answer records](app/interactive/models.py#L49) already accommodate correctness, partial credit, self-assessment, hints, timestamps, and time taken. Use that to offer:

- **Review mistakes:** questions missed or partially solved.
- **Try independently:** questions completed with assistance or after revealing the solution.
- **Review due:** questions scheduled for another attempt.
- A prominent **“Start a short review”** button.

Start with simple scheduling rules. For example, a missed question returns soon; an independently solved question returns after a longer interval. Intervals such as 1, 3, 7, and 21 days would be an initial product heuristic—the research does not establish those exact intervals as universally optimal.

The evidence for the underlying mechanisms is strong. A classroom quizzing meta-analysis covered 222 studies and 48,478 students, finding a moderate overall benefit. A separate spacing meta-analysis covered 317 experiments and found that effective spacing depends partly on how long knowledge must be retained. [Yang et al., 2021](https://pubmed.ncbi.nlm.nih.gov/33683913/), [Cepeda et al., 2006](https://digitalcommons.usf.edu/psy_facpub/1771/).

One existing behaviour deserves adjustment: [the reuse-pressure detector](app/core/trends.py#L239) discourages repeated questions once enough have been used three times. Make that recommendation depend on outcomes and spacing. Repeated exposure can represent either unproductive repetition or valuable review.

## 2. The stats need more trustworthy definitions before they need more charts

Currently, the dashboard mostly describes bank usage. Several concrete issues make it weaker:

- [Question totals and topic distributions](app/core/stats.py#L72) remain lifetime measures despite the selected date range.
- [Discover increments usage for the entire selected batch](app/ipc/api.py#L725) when the session starts.
- The quiz-mode Trends endpoint [currently ignores the mode](app/ipc/api.py#L1522) and reads PSet history.
- In Traverse/Discover, [opening a hint](frontend/src/components/quiz/QuestionViewer.tsx#L33) changes frontend state, but that use is not recorded in the completed answer history.

I would first distinguish **generated, presented, attempted, assisted, and independently solved** questions. Historical assistance data that was not captured should remain “unknown.”

Then give the dashboard five useful measures:

| Measure | Student-facing purpose |
|---|---|
| First-attempt independent success by topic | Identify where unaided practice is succeeding |
| Assisted and partially solved questions | Find questions worth revisiting |
| Success on delayed reviews | Check what remains accessible after time passes |
| Coverage by topic, with attempt counts | Reveal gaps and sparse evidence |
| Reviews due | Provide an immediate next action |

Each topic row should have a **“Practise this”** action. Show denominators—“4 of 6 independently solved” communicates more than an unexplained mastery percentage. Keep self-assessed proofs distinguishable from automatically graded answers.

Also, compare progress within similar topics and difficulty bands. The difficulty score combines solution length, embedding novelty, and topic depth; it is a useful heuristic, but it has not established a calibrated measure of student ability.

Research supports being cautious about dashboard claims: a review of 38 studies found limited evidence for learning improvements and frequent confounding between dashboard use and student engagement. I would treat these metrics as decision aids and evaluate the practice they lead to. [Kaliisa et al., 2024](https://arxiv.org/abs/2312.15042).

## 3. The lecture-keyword idea is worth building—and an inexpensive version can come first

A useful interaction would be:

> Paste: “eigenvalues, diagonalisation, repeated roots”  
> Confirm the matched concepts → choose question count → practise → save as “Monday’s lecture.”

The important product detail is **confirming the interpreted concepts**. Short terms are ambiguous, and students should be able to remove an incorrect match before starting.

The current [browser search](app/persistence/repositories/questions.py#L352) searches question LaTeX with a substring match. Extending discovery to topic names, subtopics, tags, and aliases would already improve it substantially.

I would build this in two stages:

1. **Topic and alias matching.** Recognise abbreviations, spelling variants, and course terminology. Retrieve through the existing taxonomy and filters.
2. **Asymmetric semantic retrieval.** Represent the student’s short input as a query and the candidate question’s searchable description as a document.

For the semantic version, I would experiment with a question representation containing its statement, topic hierarchy, and concise technique description. The full solution can contribute useful information, but whether that outperforms a shorter description should be measured.

The [existing embedding pipeline](app/tools/reembed.py#L74) embeds question-plus-solution content with an instruction to find similar underlying concepts and techniques. That is a good foundation for problem similarity, but keyword-to-problem retrieval needs its own evaluation. Keep experimental retrieval vectors alongside the existing vectors.

There is also a model-specific detail: the code uses `gemini-embedding-2`. Google currently documents asymmetric retrieval through query/document formatting; that model does **not** use the older `task_type` parameter. [Google embedding documentation](https://ai.google.dev/gemini-api/docs/embeddings).

To preserve the app’s offline design, precompute query vectors for recognised concepts and aliases. Arbitrary unseen text requires a compatible local encoder or an optional online embedding path. A different local model would also require compatible corpus embeddings.

Two implementation choices matter:

- Retrieve separately for each recognised concept, then allocate questions across them. A single averaged keyword vector can lose less dominant topics.
- Respect course scope and syllabus filters before selecting the final set.

Before embedding the whole bank again, evaluate perhaps 30–50 realistic lecture inputs. Compare aliases alone against semantic and combined retrieval, using manually judged relevance among the top results.

The learning evidence supports the **practice that follows discovery**. It does not establish that semantic matching itself improves retention.

## 4. Add deliberate mixed review using the existing selection infrastructure

The app already has focused and diverse selection. A small addition would let students select several previously studied techniques and arrange questions so adjacent problems usually require different approaches.

For example, mixed integration practice could require students to decide among substitution, integration by parts, and partial fractions. Keep technique labels hidden during the attempt so the student has to choose the method.

This has directly relevant mathematics evidence: a preregistered trial across 54 seventh-grade classes found that interleaved practice improved performance on a delayed test. That supports trying the approach here, while its effectiveness on undergraduate proofs and advanced material still needs evaluation. [Rohrer et al., 2020](https://doi.org/10.1037/edu0000367).

The diversity selector can supply candidates; add ordering and technique constraints. Embedding diversity alone does not ensure useful interleaving.

## 5. Make solutions invite a small amount of explanation

After showing a worked solution, offer one optional prompt:

- “Why was this method appropriate?”
- “Which condition makes this step valid?”
- “What would change if this assumption were removed?”

Save the response as a personal note attached to the question. Start with a handful of reusable prompts and use the existing takeaways where available; this needs no live AI tutor.

Self-explanation prompts have evidence across studying worked examples and solving problems. A meta-analysis reported an overall effect of `g = 0.55`. That supports the mechanism, while the best prompt and frequency for Amplify remain design questions. [Bisra et al., 2018](https://link.springer.com/article/10.1007/s10648-018-9434-x).

## 6. Themes are a sensible reward, but pilot milestones before building a full economy

The [theme gallery](frontend/src/pages/Themes.tsx#L40) and switching infrastructure already exist, with nine themes. That makes cosmetic progression relatively inexpensive.

My first version would award a few **new** theme variants or accents for milestones such as completing spaced reviews or returning to previously missed questions. Preserve access to existing themes and keep readability and accessibility settings freely available.

If introducing a currency, make the earning rules reinforce the practice loop:

| Action | Suggested reward treatment |
|---|---|
| Complete a scheduled review | Small, predictable reward |
| Correct a previous mistake on a later visit | Additional reward |
| Generate a PDF or leave the app open | No currency |
| Repeatedly answer the same easy question | Limited repeat rewards |

Give some credit for completing and assessing an honest attempt, so students still have a reason to practise difficult material. Hint use should remain a useful learning choice.

I would also improve theme previews to show an actual question, equation, input, and feedback state. That helps students choose a theme they can comfortably study with.

Gamification research is promising: one meta-analysis found positive average effects on learning, although motivational and behavioural findings were less stable in more rigorous subsets. It does **not** isolate a theme shop or establish an optimal currency design. Treat the reward rules as a hypothesis to test. [Sailer & Homner, 2020](https://link.springer.com/article/10.1007/s10648-019-09498-w).

## Additional small features and pilot evaluation

Two additional small features fit this repository well: **bookmarks with personal notes**, and **“Record paper results”** from PSet history. The app already stores each PSet’s question IDs, so students working on printed sheets could mark questions as solved, partial, or missed and feed the same review queue.

For a pilot, measure **successful unaided attempts after a delay**, alongside return visits and review completion. That would help determine whether the additions improve learning and whether students keep using them.
