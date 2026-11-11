/**
 * The top of the Welcome page: the active subject, what is due for review in
 * it, and the three things a student comes here to do (practise, review,
 * create a paper). A running session is offered first.
 */

import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { FileText, NotebookPen, Play, RotateCcw } from "lucide-react";

import { Button } from "../ui/Button";
import { ipc, type ReviewList, type ReviewSummary } from "../../lib/ipc";
import { formatWhen } from "./ReviewPanel";
import { useQuizStore } from "../../state/quiz";
import { useSubjectStore } from "../../state/subject";

/** The line under "Today" and the review worth starting, if any. */
export function todayStatus(summary: ReviewSummary | null): {
  headline: string;
  action: { label: string; kind: ReviewList } | null;
} {
  if (!summary) return { headline: "Practise from the question bank, or create a paper to print.", action: null };
  const { due, mistakes, assisted } = summary.counts;
  if (due > 0) {
    return {
      headline: `${due} question${due === 1 ? "" : "s"} due for review`,
      action: { label: "Review due questions", kind: "due" },
    };
  }
  if (mistakes > 0) {
    return {
      headline: `Nothing due${summary.next_due ? ` until ${formatWhen(summary.next_due)}` : ""} · ${mistakes} past mistake${mistakes === 1 ? "" : "s"} to revisit`,
      action: { label: "Revisit mistakes", kind: "mistakes" },
    };
  }
  if (assisted > 0) {
    return {
      headline: `Nothing due · ${assisted} question${assisted === 1 ? "" : "s"} to try without help`,
      action: { label: "Try independently", kind: "assisted" },
    };
  }
  if (summary.tracked > 0) {
    return { headline: `All caught up${summary.next_due ? ` · next review ${formatWhen(summary.next_due)}` : ""}`, action: null };
  }
  return { headline: "Answer questions in Quiz and they come back here when they are due for review.", action: null };
}

export function TodayCard() {
  const navigate = useNavigate();
  const subject = useSubjectStore((s) => s.active);
  const running = useQuizStore((s) => s.isStarted);
  const [summary, setSummary] = useState<ReviewSummary | null>(null);

  useEffect(() => {
    let cancelled = false;
    ipc
      .get_review_summary(subject)
      .catch(() => null)
      .then((s) => {
        if (!cancelled) setSummary(s);
      });
    return () => {
      cancelled = true;
    };
  }, [subject]);

  const { headline, action } = todayStatus(summary);
  // One filled button: the session in progress, else the review that is waiting, else practice.
  const main = running ? "resume" : action ? "review" : "practice";

  return (
    <section className="w-full rounded-lg border border-border bg-surface p-5" aria-label="Today">
      <div className="flex flex-wrap items-center gap-x-6 gap-y-4">
        <div className="min-w-[14rem] flex-1">
          <div className="text-xs font-medium uppercase tracking-wide text-muted">
            Today · {subject ?? "All subjects"}
          </div>
          <h2 className="mt-0.5 text-lg font-semibold">{running ? "A practice session is in progress" : headline}</h2>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          {running ? (
            <Button variant="primary" onClick={() => navigate("/quiz")}>
              <Play className="h-4 w-4" />
              Resume session
            </Button>
          ) : (
            <>
              {action && (
                <Button
                  variant="primary"
                  onClick={() => navigate("/quiz", { state: { startReview: action.kind, subject } })}
                >
                  <RotateCcw className="h-4 w-4" />
                  {action.label}
                </Button>
              )}
              <Button variant={main === "practice" ? "primary" : "outline"} onClick={() => navigate("/quiz")}>
                <Play className="h-4 w-4" />
                Start practice
              </Button>
              <Button variant="outline" onClick={() => navigate("/quiz", { state: { mode: "lecture" } })}>
                <NotebookPen className="h-4 w-4" />
                From a lecture
              </Button>
            </>
          )}
          <Button variant="outline" onClick={() => navigate("/generate")}>
            <FileText className="h-4 w-4" />
            Create a paper
          </Button>
        </div>
      </div>
    </section>
  );
}
