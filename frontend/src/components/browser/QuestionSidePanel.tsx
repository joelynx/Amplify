/**
 * Side panel for the Browser (spec §8.6).
 *
 * Renders question / solution / hints / solution_outline (KaTeX'd); the
 * solution is the generated one when there is one, with the source's own
 * under "Original solution". Plus a
 * "similar questions" list driven by `get_similar_questions`. With "Apply
 * filters" checked, that list only draws from questions matching the
 * Browser's filters and search text. Read-only — no edit / new / delete
 * affordances anywhere.
 *
 * Beside the list on a wide window, where its left edge drags to resize it;
 * over the whole list below the `lg` width, where the two do not fit.
 */

import { useEffect, useRef, useState } from "react";
import { ChevronRight, X } from "lucide-react";

import { setPref, usePref } from "../../appearance/prefs";
import { cn } from "../../lib/cn";

import { Button } from "../ui/Button";
import { Checkbox } from "../ui/Checkbox";
import { bestSolution, hintTiers, ipc, type Filters, type Question, type SimilarQuestion } from "../../lib/ipc";
import { LatexContent } from "./LatexContent";
import { BookmarkButton, NoteEditor } from "../notes/QuestionNotes";
import { Flaggable } from "../notes/ContentFlag";

interface Props {
  question: Question | null;
  /** The Browser's current filters and search text, used when "Apply filters" is on. */
  filters: Filters;
  textQuery: string;
  onClose: () => void;
  onPickSimilar: (qid: number) => void;
}

const WIDTH_PREF = "browser.panelWidth";
const DEFAULT_WIDTH = 420;
const MIN_WIDTH = 340;
const MAX_WIDTH = 760;
const clampWidth = (w: number) => Math.min(MAX_WIDTH, Math.max(MIN_WIDTH, Math.round(w)));

export function QuestionSidePanel({ question, filters, textQuery, onClose, onPickSimilar }: Props) {
  const [similar, setSimilar] = useState<SimilarQuestion[]>([]);
  const [loadingSimilar, setLoadingSimilar] = useState(false);
  const [applyFilters, setApplyFilters] = useState(false);

  const storedWidth = usePref<number>(WIDTH_PREF, DEFAULT_WIDTH);
  // Width while the edge is being dragged; saved on release.
  const [dragWidth, setDragWidth] = useState<number | null>(null);
  const width = clampWidth(dragWidth ?? storedWidth);
  const panelRef = useRef<HTMLElement>(null);

  const onDragStart = (e: React.PointerEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.currentTarget.setPointerCapture(e.pointerId);
    setDragWidth(width);
  };
  const onDragMove = (e: React.PointerEvent<HTMLDivElement>) => {
    if (dragWidth === null || !panelRef.current) return;
    setDragWidth(clampWidth(panelRef.current.getBoundingClientRect().right - e.clientX));
  };
  const onDragEnd = () => {
    if (dragWidth !== null) setPref(WIDTH_PREF, dragWidth);
    setDragWidth(null);
  };
  const onHandleKey = (e: React.KeyboardEvent) => {
    if (e.key === "ArrowLeft") setPref(WIDTH_PREF, clampWidth(width + 24));
    else if (e.key === "ArrowRight") setPref(WIDTH_PREF, clampWidth(width - 24));
  };

  // Escape closes the question, unless a dialog on top of it wants the key.
  const isOpen = question !== null;
  useEffect(() => {
    if (!isOpen) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape" && !e.defaultPrevented && !document.querySelector('[role="dialog"]')) onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [isOpen, onClose]);

  // Null while "Apply filters" is off, so Browser filter edits don't refetch then.
  const scopeFilters = applyFilters ? filters : null;
  const scopeText = applyFilters && textQuery ? textQuery : null;

  useEffect(() => {
    if (!question) {
      setSimilar([]);
      return;
    }
    let cancelled = false;
    setLoadingSimilar(true);
    ipc
      .get_similar_questions(question.question_id, 8, scopeFilters, scopeText)
      .then((hits) => {
        if (!cancelled) setSimilar(hits);
      })
      .finally(() => {
        if (!cancelled) setLoadingSimilar(false);
      });
    return () => {
      cancelled = true;
    };
  }, [question, scopeFilters, scopeText]);

  const widthVar = { "--panel-w": `${width}px` } as React.CSSProperties;

  if (!question) {
    return (
      <aside
        style={widthVar}
        className="hidden w-[var(--panel-w)] flex-none border-l border-border bg-surface lg:block"
      >
        <div className="p-6 text-sm text-muted">
          Click a question to read it here.
        </div>
      </aside>
    );
  }

  const solution = bestSolution(question);
  const hints = hintTiers(question);

  return (
    <aside
      ref={panelRef}
      style={widthVar}
      data-ui="question-panel"
      aria-label={`Question ${question.question_id}`}
      className="absolute inset-0 z-20 bg-surface lg:relative lg:inset-auto lg:z-auto lg:w-[var(--panel-w)] lg:flex-none lg:border-l lg:border-border"
    >
      <div
        role="separator"
        aria-orientation="vertical"
        aria-label="Resize the question panel"
        aria-valuemin={MIN_WIDTH}
        aria-valuemax={MAX_WIDTH}
        aria-valuenow={width}
        tabIndex={0}
        onPointerDown={onDragStart}
        onPointerMove={onDragMove}
        onPointerUp={onDragEnd}
        onPointerCancel={onDragEnd}
        onKeyDown={onHandleKey}
        className="absolute left-0 top-0 z-20 -ml-px hidden h-full w-1.5 cursor-col-resize touch-none hover:bg-primary/40 focus:outline-none focus-visible:bg-primary lg:block"
      />
      <div className="h-full overflow-y-auto">
      <header className="sticky top-0 z-10 flex items-center justify-between gap-2 border-b border-border bg-surface px-4 py-2">
        <div className="text-xs uppercase tracking-wide text-muted">
          Q{question.question_id} · {question.topic} / {question.branch} / {question.subtopic}
        </div>
        <Button variant="ghost" size="sm" onClick={onClose} aria-label="Close question">
          <X className="h-4 w-4" />
          <span className="lg:hidden">Back to list</span>
        </Button>
      </header>
      <div className="mx-auto max-w-3xl space-y-4 p-4">
        <Metadata question={question} />

        <div className="flex justify-end">
          <BookmarkButton questionId={question.question_id} />
        </div>

        <Section title="Question">
          <div data-ui="question">
            <LatexContent source={question.latexcode} />
          </div>
        </Section>

        {solution && (
          <Disclosure title="Solution" defaultOpen={false}>
            <Flaggable questionId={question.question_id} part="solution">
              <LatexContent source={solution} />
            </Flaggable>
          </Disclosure>
        )}

        {/* The source's own solution, when the generated one is shown above. */}
        {question.generated_solution?.trim() && question.solution?.trim() && (
          <Disclosure title="Original solution" defaultOpen={false}>
            <LatexContent source={question.solution} />
          </Disclosure>
        )}

        {question.solution_outline && (
          <Disclosure title="Outline" defaultOpen={false}>
            <LatexContent source={question.solution_outline} />
          </Disclosure>
        )}

        {hints.length > 0 && (
          <Disclosure title="Hints" defaultOpen={false}>
            <Flaggable questionId={question.question_id} part="hint">
              {hints.map((hint, i) => (
                <div key={i} data-ui="hint-tier" className={i > 0 ? "border-t border-border pt-3" : undefined}>
                  {hints.length > 1 && (
                    <div className="mb-1 text-xs font-medium uppercase tracking-wide text-muted">
                      Hint {i + 1} of {hints.length}
                    </div>
                  )}
                  <LatexContent source={hint} />
                </div>
              ))}
            </Flaggable>
          </Disclosure>
        )}

        <Section title="Your note">
          <NoteEditor questionId={question.question_id} placeholder="Why the method works, where you got stuck, what to remember." />
        </Section>

        <Section
          title="Similar questions"
          aside={
            <label
              className="inline-flex items-center gap-1.5 text-xs text-muted"
              title="Only suggest questions that match the Browser's filters and search text"
            >
              <Checkbox
                state={applyFilters ? "checked" : "unchecked"}
                onChange={() => setApplyFilters((v) => !v)}
              />
              <span>Apply filters</span>
            </label>
          }
        >
          {loadingSimilar && <p className="text-xs text-muted">Loading…</p>}
          {!loadingSimilar && similar.length === 0 && (
            <p className="text-xs text-muted">
              {applyFilters
                ? "No similar questions match the Browser's filters."
                : "No similar questions found for this one."}
            </p>
          )}
          {similar.length > 0 && (
            <ul className="space-y-1 text-xs">
              {similar.map((s) => (
                <li
                  key={s.question_id}
                  className="cursor-pointer rounded-md border border-border bg-background p-2 hover:border-primary"
                  onClick={() => onPickSimilar(s.question_id)}
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="font-medium">
                      Q{s.question_id} · {s.subtopic}
                    </span>
                    <span className="tabular-nums text-muted">
                      {(s.similarity * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div className="mt-1 truncate text-muted">{s.latexcode.slice(0, 100)}</div>
                </li>
              ))}
            </ul>
          )}
        </Section>
      </div>
      </div>
    </aside>
  );
}

function Section({
  title,
  aside,
  children,
}: {
  title: string;
  /** Optional control shown at the right of the heading. */
  aside?: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <section>
      <div className="mb-1 flex items-center justify-between gap-2">
        <h3 className="text-xs font-semibold uppercase tracking-wide text-muted">{title}</h3>
        {aside}
      </div>
      {children}
    </section>
  );
}

/** Collapsible section — solutions, outline and hints hide behind a click so
 * the panel works as a practice surface (read question, attempt, then reveal). */
function Disclosure({
  title,
  defaultOpen,
  children,
}: {
  title: string;
  defaultOpen: boolean;
  children: React.ReactNode;
}) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <section>
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        aria-expanded={open}
        className="flex w-full items-center gap-1 text-xs font-semibold uppercase tracking-wide text-muted hover:text-text"
      >
        <ChevronRight className={cn("h-3 w-3 transition-transform", open && "rotate-90")} />
        {title}
      </button>
      {open && <div className="mt-2">{children}</div>}
    </section>
  );
}

function Metadata({ question }: { question: Question }) {
  return (
    <div className="flex flex-wrap gap-1 text-xs">
      {question.type && (
        <span className="rounded-full border border-border bg-background px-2 py-0.5">
          {question.type}
        </span>
      )}
      {question.source && (
        <span className="rounded-full border border-border bg-background px-2 py-0.5">
          {question.source}
        </span>
      )}
      <span
        className={
          "rounded-full px-2 py-0.5 " +
          (question.in_syllabus
            ? "bg-success/10 text-success"
            : "bg-error/10 text-error")
        }
      >
        {question.in_syllabus ? "in syllabus" : "off syllabus"}
      </span>
      {question.times_used > 0 && (
        <span className="rounded-full border border-border bg-background px-2 py-0.5">
          used ×{question.times_used}
        </span>
      )}
      {question.tags.map((t) => (
        <span
          key={t}
          className="rounded-full border border-primary/30 bg-primary/10 px-2 py-0.5 text-primary"
        >
          {t}
        </span>
      ))}
    </div>
  );
}
