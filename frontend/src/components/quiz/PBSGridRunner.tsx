/**
 * PBS parallel-pool runner (spec §10.1).
 *
 * N visible widgets, drawn from a pool of size > N. A widget is consumed only
 * on a correct numerical submission; wrong submissions decay the available
 * score (geometric ×0.5, floor 1). The user can switch focus between widgets
 * at any time — implicit skip, no advance penalty.
 *
 * Each widget answers its question's answer-key parts. A submission with a
 * wrong auto-graded part is wrong (the card marks which parts, reveals
 * nothing); parts that need self-assessment are revealed and marked in the
 * card once the auto-graded ones are right.
 */

/**
 * @deprecated Replaced by TraverseRunner and DiscoverRunner.
 */
import { useEffect, useState } from "react";

import { Button } from "../ui/Button";
import { Card } from "../ui/Card";
import { LatexContent } from "../browser/LatexContent";
import { AnswerPanel } from "./AnswerPanel";
import { QuizCountdown } from "./QuizCountdown";
import { cn } from "../../lib/cn";
import { ipc, type QuizAnswerResult, type QuizSettings, type QuizSlot } from "../../lib/ipc";

interface Props {
  quizId: string;
  settings: QuizSettings;
  initial: QuizSlot[];
  totalTimeS: number | null;
  onFinished: (attemptId: string) => void;
}

export function PBSGridRunner({ quizId, settings, initial, totalTimeS, onFinished }: Props) {
  const [slots, setSlots] = useState<QuizSlot[]>(initial);
  // The last result per slot while its question stays up (a retry or a pending reveal).
  const [results, setResults] = useState<Record<number, QuizAnswerResult | null>>({});
  const [totalScore, setTotalScore] = useState(0);
  const [busy, setBusy] = useState(false);
  const [deadlineMs] = useState<number | null>(() => (totalTimeS ? Date.now() + totalTimeS * 1000 : null));
  const [flash, setFlash] = useState<Record<number, "ok" | "wrong" | null>>({});

  const allEmpty = slots.every((s) => s.question == null);

  useEffect(() => {
    if (allEmpty) {
      finish();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [allEmpty]);

  const finish = async () => {
    setBusy(true);
    try {
      const r = await ipc.quiz_finish(quizId);
      onFinished(r.attempt_id);
    } finally {
      setBusy(false);
    }
  };

  const applyResult = async (slotIndex: number, r: QuizAnswerResult) => {
    if (r.current_total != null) setTotalScore(r.current_total);
    // A pending reveal or a retry keeps the question (and its panel) up.
    setResults((prev) => ({ ...prev, [slotIndex]: r.pending || r.retry ? r : null }));
    if (!r.pending) {
      setFlash((f) => ({ ...f, [slotIndex]: r.correct ? "ok" : "wrong" }));
      window.setTimeout(() => setFlash((f) => ({ ...f, [slotIndex]: null })), 600);
    }
    const repl = r.replacement as QuizSlot | null | undefined;
    if (repl && "slot_index" in repl) {
      setSlots((prev) => {
        const next = [...prev];
        next[slotIndex] = repl;
        return next;
      });
    }
    if (r.finished) {
      await finish();
    }
  };

  return (
    <div className="mx-auto max-w-6xl space-y-4 px-6 py-6">
      <header className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-border bg-surface px-4 py-3">
        <div>
          <h1 className="text-lg font-semibold">[PBS] Physics Brawl</h1>
          <p className="text-xs text-muted">
            {slots.filter((s) => s.question != null).length}/{slots.length} active widgets ·
            score {totalScore.toFixed(1)}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <QuizCountdown deadlineMs={deadlineMs} onExpire={finish} />
          <Button variant="outline" size="sm" onClick={finish} disabled={busy}>
            Finish
          </Button>
        </div>
      </header>

      <div
        className={cn(
          "grid gap-3",
          slots.length <= 2 && "sm:grid-cols-2",
          slots.length === 3 && "sm:grid-cols-2 lg:grid-cols-3",
          slots.length >= 4 && "sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4",
        )}
      >
        {slots.map((slot, i) => {
          const q = slot.question;
          const f = flash[i];
          return (
            <Card
              key={`slot-${i}-${q?.question_id ?? "empty"}`}
              className={cn(
                "transition-colors",
                f === "ok" && "border-success",
                f === "wrong" && "border-error",
                !q && "opacity-50",
              )}
              title={`Slot ${i + 1}`}
              actions={
                q && (
                  <span className="rounded-full bg-primary/10 px-2 py-0.5 text-xs font-semibold text-primary">
                    {slot.available_score.toFixed(1)} pts
                  </span>
                )
              }
            >
              {!q ? (
                <p className="text-sm text-muted">— pool exhausted —</p>
              ) : (
                <>
                  <div className="mb-2 text-xs text-muted">
                    {q.topic} / {q.subtopic}
                  </div>
                  <div className="mb-3">
                    <LatexContent source={q.latexcode} />
                  </div>
                  <AnswerPanel
                    compact
                    autoFocus={false}
                    fields={q.answer_fields}
                    result={results[i] ?? null}
                    disabled={busy}
                    submit={(answers) => ipc.quiz_submit_answer(quizId, i, { answers })}
                    assess={(marks) => ipc.quiz_self_assess(quizId, i, { marks })}
                    onResult={(r) => void applyResult(i, r)}
                  />
                </>
              )}
            </Card>
          );
        })}
      </div>
      {void settings}
    </div>
  );
}
