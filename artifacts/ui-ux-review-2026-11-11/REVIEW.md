# Amplify UI and UX review — 11 November 2026

Amplify has a distinctive visual identity and valuable study features. Its main weakness is the path from intent to action: the interface asks students to understand configuration, taxonomy and selection algorithms before they can comfortably start studying. Several reproducible interaction defects also undermine the otherwise promising experience.

The highest-value next iteration is to make study actions obvious, keep subject and session state predictable, and strengthen the shared controls. More themes would have less immediate benefit.

## Scope and evidence

Reviewed the current React source and rendered Home, Generate, Quiz, Browser, Subjects, History, Stats, Themes and Settings. Inspected the saved Pastel appearance and Default Light, at 1280 × 820 and the supported minimum size of 960 × 640. Exercised subject activation, starting a Traverse session, navigating away and back, revealing a solution, opening a question and opening the Stats filter dialog.

The frontend ran in headless Edge against a temporary HTTP adapter to the real Python API and an isolated database snapshot. The snapshot retained 25,197 questions but omitted large embedding vectors to fit available disk space. Similarity quality and performance, DPP selection quality, native dialogs, PDF compilation and the PyWebView-specific experience were not validated. Timing observations are not production performance benchmarks. A browser extension's floating icon is visible in some captures; it is not part of Amplify and is excluded from this critique.

No application source or original study data was changed. Evidence is in the adjacent screenshots, `interaction-findings.json` and `session-findings.json`. This is an expert inspection, not a study with representative students or a complete accessibility certification.

## Findings, in priority order

### 1. P1 — Returning to a practice session can prevent further progress

**Reproduced:** Start Traverse, open Stats, then return to Quiz. The question remains, but **Next Question** becomes disabled and the remaining count changes from 199 to a dash. The diversity slider is disabled too. The UI looks like a resumed session but cannot continue normally.

`TraverseRunner` initializes local `loading` to true and `remaining` to null. On remount, its initialization effect returns early because the questions/session ID already exist. It never restores those local values. See `frontend/src/components/quiz/TraverseRunner.tsx:33`, `:39` and `:188`.

**Change:** Restore all necessary session state when returning to a session. Persist question drafts as well as completed answers. Make resume behavior explicit and keep session timing/summary state intact across navigation.

**Acceptance:** Start a session, enter an answer draft, visit another page and return. The draft, question, remaining count and working Next action survive.

Evidence: [before navigation](practice-before-navigation.png), [after navigation](practice-after-navigation.png).

### 2. P1 — “Active subject” does not reliably determine what a student studies

**Reproduced:** Activate Calculus in Subjects and open Quiz directly. Quiz still displays **Any subject** and offers the whole taxonomy. Starting Traverse selected a question outside Calculus. This contradicts Home's promise that activating a subject scopes every other page.

Quiz takes its filters from `useGenerateStore`, whose subject initially defaults to null. Generate separately initializes that store from the active subject; Quiz does not. Browser does not pass a subject in its search filters, and Stats/History initialize to all subjects. The student's experience therefore depends partly on which page they visited first.

**Change:** Put a visible subject selector in the application shell and use a single scope model. Where an all-subjects override is useful, label it clearly and keep it distinct from the selected course. Resolve whether Quiz and Generate should share drafts; currently their coupling is not visible to users.

**Acceptance:** Activate Calculus, go straight to Quiz and get Calculus questions. Visit Browser, Stats and History and see either that scope or a clearly indicated override.

References: `frontend/src/pages/Welcome.tsx:34`, `frontend/src/pages/Quiz.tsx:89`, `frontend/src/state/generate.ts:96`, `frontend/src/pages/Browser.tsx:98`.

### 3. P1 — The inactive Stats tab is visually invisible

**Reproduced:** In the saved Pastel theme, the **Quizzes** tab's text is `rgb(110, 95, 134)` and its background is also `rgb(110, 95, 134)`. The control appears to have only one labeled option.

The tab container uses `bg-muted`; its inactive button uses `text-muted`. The same construction exists independent of this particular palette. Several quiz controls also use tokens such as `text-primary-foreground` that are absent from the Tailwind configuration, weakening consistency across themes.

**Change:** Give selected, unselected, hover and disabled controls distinct semantic colors. Audit rendered components across themes, beyond testing palette token pairs in isolation.

Reference: `frontend/src/pages/Stats.tsx:149`. Evidence: [Stats](stats.png), computed colors in `interaction-findings.json`.

### 4. P1 — Keyboard and assistive-technology support is incomplete in core controls

**Reproduced:** Opening the Stats filter dialog leaves keyboard focus on the **Filters** button behind the overlay. The dialog has no `aria-labelledby` connection to its title. The shared Modal has no initial focus, focus containment or focus restoration.

Source inspection also finds clickable subject list items without keyboard interaction, custom comboboxes without expanded/listbox/option semantics, and visual partial checkboxes that do not expose an indeterminate state. These are recurring primitives, so their effects span many pages.

**Change:** Repair the shared dialog, combobox and checkbox components first. Make subject selection a native button/list control, provide visible keyboard focus and label inputs consistently. The combobox already supports some arrow-key selection; preserve that while making its state perceivable.

**Acceptance:** Complete subject selection, filtering and dialog dismissal using only the keyboard. Focus enters a dialog, remains there and returns to its trigger.

References: `frontend/src/components/ui/Modal.tsx:19`, `Combobox.tsx:85`, `Checkbox.tsx:28`, `frontend/src/pages/Subjects.tsx:292`.

### 5. P2 — Home spends its strongest visual emphasis on the room rather than the next study action

The room is memorable and worth retaining as an optional source of character. At 1280 × 820, it occupies roughly 550 vertical pixels, while the Today card begins near the bottom of the viewport. The Subjects, Themes, Tutorial and About cards are further down. The large illustration is interactive, but several destinations depend on recognizing objects or discovering tooltips. In the non-room version, the main CTA is the vague **Enter**.

**Change:** Lead with the active subject, **Start practice**, **Review due questions** and **Create a paper**. Put today's review status beside those actions. Offer a compact room beneath or beside that area. Use the room as an additional way to navigate, with visible labels for important destinations.

Evidence: [Home](home.png). Reference: `frontend/src/pages/Welcome.tsx:61`.

### 6. P2 — Generate and Quiz place too much setup before the primary action

At 1280 × 820 with the populated bank, **Generate PDF** was approximately 1,445 pixels below the top of the viewport; **Start Traverse Session** was at approximately 1,449 pixels. Each sits after multiple configuration blocks. The nested, scrolling taxonomy adds another layer of navigation. In Quiz, even the Subject Filters header is cramped enough to wrap labels and the Save template button.

Generate's first card is labeled **Required** while its first control says **Pick a template (optional)**. Tags, source filters, types and strategy appear before completion without a strong basic/advanced distinction.

**Change:** Make subject/topic, question count and start/create the main flow. Collapse advanced filters and print options. Keep a compact action bar visible with a selection summary, matching question count and clear validation. On Quiz, recommend a sensible starting mode instead of presenting five equally weighted choices.

Evidence: [Generate](generate.png), [Quiz](quiz.png), measured positions in `interaction-findings.json`. Reference: `frontend/src/pages/Generate.tsx:322`.

### 7. P2 — Product language repeatedly exposes the underlying implementation

Examples include **Filter visible leaves**, **Collapse leaves**, **DPP selection**, **greedy MAP-DPP**, **cosine similarity**, **In-syllabus = 1**, **ingest the seed** and **multiplicity**. Students should not need the data model to understand the study workflow. Traverse's **Diversity** percentage increases toward **Similar**, which makes the label harder to interpret.

Tag selection adds a particularly subtle rule: turning **Exclude** on also turns **Compulsory?** on. The switches affect newly added tags, while existing chips keep their category. Their category is conveyed primarily by color.

**Change:** Use “Search topics,” “Collapse all,” “Varied practice,” “Similar questions,” “Include in syllabus” and “Import question bank.” Replace the two tag switches with an explicit rule selector and labeled chips, such as “Must include,” “Match any” and “Exclude.” Label the slider “Similarity to this question,” with clear endpoints.

References: `frontend/src/components/generate/CheckableTree.tsx:126`, `TagTray.tsx:82`, `OutputSettings.tsx:12`, `frontend/src/pages/Quiz.tsx:35`.

### 8. P2 — Browser is optimized for metadata inspection more than choosing questions

The table shows ID, topic, branch, subtopic, type and source, but no question excerpt. Many adjacent rows look identical. The empty side panel already reserves 420 pixels at larger widths. At 960 × 640, opening a question leaves just 540 pixels for the table, requiring horizontal scrolling while the detail panel scrolls separately.

The empty panel instructs **Click a row to view it**, but only the ID button opens the question. Hints and outlines are expanded by default, potentially revealing help before the student chooses to see it.

**Change:** Make a rendered question excerpt the primary row content; move secondary taxonomy into supporting text or optional columns. Make the row action match its instruction. Use a resizable panel on wide windows and a full-width detail view or overlay at the minimum size. Hide hints until requested.

Evidence: [question detail at 1280](browser-question.png), [question detail at 960](browser-960.png). References: `frontend/src/pages/Browser.tsx:344`, `frontend/src/components/browser/QuestionSidePanel.tsx:64`.

### 9. P2 — Revealing help changes grading without explaining the consequence beforehand

**Reproduced:** Clicking **Show Solution** before answering changes the answer area to “this one is not graded.” The consequence is explained after the action. The reveal controls sit above the question, making them prominent before the student's attempt.

**Change:** Keep the helpful, non-punitive distinction between independent and assisted work, but explain it beside the reveal action before the click. For example: “Reveal solution — this question will count as assisted.” Put the main answer action first and keep hint/reveal controls secondary. An inline explanation is preferable to another mandatory modal.

References: `frontend/src/components/quiz/QuestionViewer.tsx:37`, `PracticeAnswer.tsx:34`. Evidence: `session-findings.json`.

### 10. P2 — The five-minute screensaver conflicts with solving problems on paper

During inspection, the screen dimmed and a moving logo overlaid an active question after inactivity. The implementation triggers after five minutes without pointer/keyboard activity. A student can easily spend that long working on paper while still needing to read the question. The default appearance settings enable easter eggs, and the timer has no general active-study-session exemption.

**Change:** Suppress the screensaver whenever a question or solution is being studied. Make it opt-in for Home if retained. Preserve decorative personality where it does not interrupt reading, thinking or answering.

Reference: `frontend/src/appearance/eggs/EasterEggs.tsx:29` and `:60`. This is separate from reduced-motion and timed-session focus settings.

### 11. P2 — Stats leads with activity accounting and weakens the learning story

Nine large tiles emphasize generated sets, questions seen and multiplicity before Learning. With little recent activity, the first screen is mostly zeros and dashes. The Learning section is more useful: it distinguishes unaided work, revisits, delayed reviews and coverage, and links to practice. The full page was over 4,200 pixels tall in the inspected state.

**Change:** Lead with “What should I practise next?”, reviews due and one or two comprehensible learning measures. Keep denominators and assistance distinctions. Move generation usage and detailed distributions into secondary sections, with clear scope and date labels.

Evidence: [Stats](stats.png). References: `frontend/src/pages/Stats.tsx:182`, `frontend/src/components/stats/LearningPanel.tsx:90`.

### 12. P2 — Recovery and destructive actions need a clearer hierarchy

Settings opens with **Reset DB Data**, before ordinary preferences. **Reset active subject usage** immediately invokes the reset; its modal reports the result afterwards. Factory reset does have a confirmation, but that protection is inconsistent. Neither placement helps users looking for normal settings.

Generate communicates a disabled action's reason through a tooltip around a disabled button; this is difficult to discover by keyboard. While generating, the button remains labeled Generate PDF; Export LaTeX is not disabled by the same busy state. Browser initializes with “No questions match these filters” while rows are still loading, and its request path has no loading/error state or stale-response protection.

**Change:** Move destructive controls to a clearly separated maintenance area, name the affected subject and explain scope before reset. Give important operations visible progress and retry states. Show actionable empty states and inline validation. Prevent overlapping exports. Preserve drafts or warn before abandoning unsaved subject edits and notes.

References: `frontend/src/pages/Settings.tsx:217` and `:295`, `frontend/src/components/generate/ActionRow.tsx:37`, `frontend/src/pages/Browser.tsx:109`.

## Additional content trust observation

Question 1 renders a clear mathematical question about a root of cos(x) = x, but its expanded hint says the statement appears to be an undefined LaTeX command rather than a question. That mismatch is visible in [the Browser capture](browser-question.png). This is one observed example, not an estimate of prevalence. Provide a way to flag unusable hints/solutions, hide diagnostics from the teaching surface, and present source versus generated assistance consistently.

## What to preserve

- A coherent, recognizable personality and theme system, plus focus and reduced-motion options.
- The Today/review queue, lecture-keyword flow and mixed practice: useful entry points tied to student intentions.
- Readable mathematical rendering, bookmarks and self-explanation notes.
- Learning measures that show denominators and distinguish assisted from independent performance.
- The persistent matching-question count and reusable templates for experienced users.

## Suggested implementation sequence

1. Repair session resumption, subject scope, invisible tabs and the shared keyboard/dialog primitives.
2. Rework Home, Quiz and Generate around a visible first action and optional advanced settings.
3. Make Browser useful for choosing questions at both supported desktop sizes.
4. Simplify terminology, prevent study-time decorative interruptions, improve recovery and make Learning lead Stats.

Then observe a first-time student and a returning student completing three tasks: start a short Calculus session, create a ten-question paper, and find something worth reviewing. Measure completion, time to first question and wrong-subject starts before deciding whether more visual customization is the next priority.
