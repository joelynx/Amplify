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
 */

import { useEffect, useState } from "react";
import { ChevronRight, X } from "lucide-react";

import { cn } from "../../lib/cn";

import { Button } from "../ui/Button";
import { Checkbox } from "../ui/Checkbox";
import { bestSolution, ipc, type Filters, type Question, type SimilarQuestion } from "../../lib/ipc";
import { LatexContent } from "./LatexContent";
import { BookmarkButton, NoteEditor } from "../notes/QuestionNotes";

interface Props {
  question: Question | null;
  /** The Browser's current filters and search text, used when "Apply filters" is on. */
  filters: Filters;
  textQuery: string;
  onClose: () => void;
  onPickSimilar: (qid: number) => void;
}

export function QuestionSidePanel({ question, filters, textQuery, onClose, onPickSimilar }: Props) {
  const [similar, setSimilar] = useState<SimilarQuestion[]>([]);
  const [loadingSimilar, setLoadingSimilar] = useState(false);
  const [applyFilters, setApplyFilters] = useState(false);

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

  if (!question) {
    return (
      <aside className="hidden w-[420px] flex-none border-l border-border bg-surface lg:block">
        <div className="p-6 text-sm text-muted">
          Click a row to view it.
        </div>
      </aside>
    );
  }

  const solution = bestSolution(question);

  return (
    <aside className="w-[420px] flex-none overflow-y-auto border-l border-border bg-surface">
      <header className="sticky top-0 z-10 flex items-center justify-between border-b border-border bg-surface px-4 py-2">
        <div className="text-xs uppercase tracking-wide text-muted">
          Q{question.question_id} · {question.topic} / {question.branch} / {question.subtopic}
        </div>
        <Button variant="ghost" size="sm" onClick={onClose} aria-label="Close">
          <X className="h-4 w-4" />
        </Button>
      </header>
      <div className="space-y-4 p-4">
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
            <LatexContent source={solution} />
          </Disclosure>
        )}

        {/* The source's own solution, when the generated one is shown above. */}
        {question.generated_solution?.trim() && question.solution?.trim() && (
          <Disclosure title="Original solution" defaultOpen={false}>
            <LatexContent source={question.solution} />
          </Disclosure>
        )}

        {question.solution_outline && (
          <Disclosure title="Outline" defaultOpen={true}>
            <LatexContent source={question.solution_outline} />
          </Disclosure>
        )}

        {question.hints && (
          <Disclosure title="Hints" defaultOpen={true}>
            <LatexContent source={question.hints} />
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
                : "No similar questions — this row may have no embedding (augmented seed)."}
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

/** Collapsible section — solutions hide behind a click so the panel works
 * as a practice surface (read question, attempt, then reveal). Outline /
 * hints default open since they're short. */
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
