/**
 * Side panel for the Browser (spec §8.6).
 *
 * Renders question / solution / hints / solution_outline (KaTeX'd), plus a
 * "similar questions" list driven by `get_similar_questions`. Read-only —
 * no edit / new / delete affordances anywhere.
 */

import { useEffect, useState } from "react";
import { X } from "lucide-react";

import { Button } from "../ui/Button";
import { ipc, type Question, type SimilarQuestion } from "../../lib/ipc";
import { LatexContent } from "./LatexContent";

interface Props {
  question: Question | null;
  onClose: () => void;
  onPickSimilar: (qid: number) => void;
}

export function QuestionSidePanel({ question, onClose, onPickSimilar }: Props) {
  const [similar, setSimilar] = useState<SimilarQuestion[]>([]);
  const [loadingSimilar, setLoadingSimilar] = useState(false);

  useEffect(() => {
    if (!question) {
      setSimilar([]);
      return;
    }
    let cancelled = false;
    setLoadingSimilar(true);
    ipc
      .get_similar_questions(question.question_id, 8)
      .then((hits) => {
        if (!cancelled) setSimilar(hits);
      })
      .finally(() => {
        if (!cancelled) setLoadingSimilar(false);
      });
    return () => {
      cancelled = true;
    };
  }, [question]);

  if (!question) {
    return (
      <aside className="hidden w-[420px] flex-none border-l border-border bg-surface lg:block">
        <div className="p-6 text-sm text-muted">
          Click a row to view it.
        </div>
      </aside>
    );
  }

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

        <Section title="Question">
          <LatexContent source={question.latexcode} />
        </Section>

        {question.solution && (
          <Section title="Solution">
            <LatexContent source={question.solution} />
          </Section>
        )}

        {question.solution_outline && (
          <Section title="Outline">
            <LatexContent source={question.solution_outline} />
          </Section>
        )}

        {question.hints && (
          <Section title="Hints">
            <LatexContent source={question.hints} />
          </Section>
        )}

        <Section title="Similar questions">
          {loadingSimilar && <p className="text-xs text-muted">Loading…</p>}
          {!loadingSimilar && similar.length === 0 && (
            <p className="text-xs text-muted">
              No similar questions — this row may have no embedding (augmented seed).
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

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section>
      <h3 className="mb-1 text-xs font-semibold uppercase tracking-wide text-muted">{title}</h3>
      {children}
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
