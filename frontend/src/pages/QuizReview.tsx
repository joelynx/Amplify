/**
 * Quiz review page — `/quiz/review/:attemptId`. Spec §10 mandate: per-question
 * score, user answer vs correct, hints used, solutions. Solutions are revealed
 * unconditionally on review (spec: "review page always shows solutions
 * regardless").
 */

/**
 * @deprecated Kept for backward compatibility with old quiz attempts.
 */
import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { ArrowLeft } from "lucide-react";

import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { LatexContent } from "../components/browser/LatexContent";
import { cn } from "../lib/cn";
import { ipc, type QuizAttemptDetail, type Question } from "../lib/ipc";

export default function QuizReviewPage() {
  const { attemptId } = useParams<{ attemptId: string }>();
  const navigate = useNavigate();
  const [attempt, setAttempt] = useState<QuizAttemptDetail | null>(null);
  const [questions, setQuestions] = useState<Record<number, Question>>({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!attemptId) return;
    let cancelled = false;
    (async () => {
      const a = await ipc.get_quiz_attempt(attemptId);
      if (cancelled) return;
      setAttempt(a);
      if (a) {
        // Fetch each question for context (latex / answer / solution).
        const ids = Array.from(new Set(a.answers.map((x) => x.question_id)));
        const fetched = await Promise.all(ids.map((id) => ipc.get_question(id)));
        const map: Record<number, Question> = {};
        for (const q of fetched) if (q) map[q.question_id] = q;
        if (!cancelled) setQuestions(map);
      }
      if (!cancelled) setLoading(false);
    })();
    return () => {
      cancelled = true;
    };
  }, [attemptId]);

  if (loading) {
    return (
      <main className="h-full overflow-y-auto p-6">
        <p className="text-muted">Loading attempt…</p>
      </main>
    );
  }

  if (!attempt) {
    return (
      <main className="h-full overflow-y-auto p-6">
        <p className="text-error">Attempt not found.</p>
      </main>
    );
  }

  const correct = attempt.answers.filter((a) => a.correct === true).length;

  return (
    <main className="h-full overflow-y-auto">
      <div className="mx-auto max-w-4xl space-y-4 px-6 py-6">
        <header className="flex items-start justify-between gap-3">
          <div>
            <Button variant="ghost" size="sm" onClick={() => navigate("/history")}>
              <ArrowLeft className="h-4 w-4" />
              Back
            </Button>
            <h1 className="mt-2 text-2xl font-semibold">{attempt.template_name ?? "Quiz"} review</h1>
            <p className="text-xs text-muted">
              {attempt.date_started} → {attempt.date_finished ?? "—"} ·{" "}
              {attempt.subject ?? "(no subject)"}
            </p>
          </div>
          <div className="text-right">
            <div className="text-2xl font-semibold">{attempt.total_score?.toFixed(1) ?? "0"}</div>
            <div className="text-xs text-muted">
              {correct} / {attempt.answers.length} correct
            </div>
          </div>
        </header>

        {attempt.answers.map((a, i) => {
          const q = questions[a.question_id];
          return (
            <Card
              key={`${a.question_id}-${i}`}
              title={`Q${i + 1} · ${q?.subtopic ?? "—"}`}
              actions={
                <span
                  className={cn(
                    "rounded-full px-2 py-0.5 text-xs font-semibold",
                    a.correct === true && "bg-success/15 text-success",
                    a.correct === false && "bg-error/15 text-error",
                    a.correct === null && "bg-muted/15 text-muted",
                  )}
                >
                  {a.correct === true ? "Correct" : a.correct === false ? "Wrong" : "—"} · {a.score.toFixed(1)}
                </span>
              }
            >
              {q && (
                <>
                  <LatexContent source={q.latexcode} />
                  <dl className="mt-3 grid grid-cols-1 gap-2 text-sm sm:grid-cols-2">
                    <Detail label="Your answer" value={a.user_answer || <em className="text-muted">no answer</em>} />
                    <Detail label="Canonical answer" value={q.answer ?? <em className="text-muted">—</em>} />
                    {a.self_assessment && <Detail label="Self-assessed" value={a.self_assessment} />}
                    {a.wrong_attempts > 0 && (
                      <Detail label="Prior wrong attempts" value={a.wrong_attempts.toString()} />
                    )}
                    {a.hints_used > 0 && <Detail label="Hints used" value={a.hints_used.toString()} />}
                    {a.time_taken_ms > 0 && (
                      <Detail label="Time taken" value={`${(a.time_taken_ms / 1000).toFixed(1)}s`} />
                    )}
                  </dl>
                  {q.solution && (
                    <div className="mt-3 border-t border-border pt-3">
                      <div className="mb-1 text-xs font-medium uppercase tracking-wide text-muted">
                        Solution
                      </div>
                      <LatexContent source={q.solution} />
                    </div>
                  )}
                </>
              )}
            </Card>
          );
        })}
      </div>
    </main>
  );
}

function Detail({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div>
      <dt className="text-xs font-medium uppercase tracking-wide text-muted">{label}</dt>
      <dd className="mt-0.5">{value}</dd>
    </div>
  );
}
