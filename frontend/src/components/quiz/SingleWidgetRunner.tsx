/**
 * Non-PBS quiz runner — one visible widget. Handles allow_skips, wait_for_correct,
 * instant_scoring, show_solutions, and the self-assessment fallback for
 * non-auto-gradable answer types.
 */

import { useEffect, useState } from "react";
import { Lightbulb, Send, SkipForward } from "lucide-react";

import { Button } from "../ui/Button";
import { Card } from "../ui/Card";
import { Input } from "../ui/Input";
import { LatexContent } from "../browser/LatexContent";
import { QuizCountdown } from "./QuizCountdown";
import {
  ipc,
  type QuizAnswerResult,
  type QuizSettings,
  type QuizSlot,
} from "../../lib/ipc";

interface Props {
  quizId: string;
  settings: QuizSettings;
  initial: QuizSlot;
  totalTimeS: number | null;
  onFinished: (attemptId: string) => void;
}

type LastResult = QuizAnswerResult & { questionId?: number };

export function SingleWidgetRunner({ quizId, settings, initial, totalTimeS, onFinished }: Props) {
  const [slot, setSlot] = useState<QuizSlot>(initial);
  const [input, setInput] = useState("");
  const [lastResult, setLastResult] = useState<LastResult | null>(null);
  const [busy, setBusy] = useState(false);
  const [totalScore, setTotalScore] = useState(0);
  const [questionsAnswered, setQuestionsAnswered] = useState(0);
  const [startedAt, setStartedAt] = useState<number>(() => Date.now());
  const [hint, setHint] = useState<string | null>(null);
  const [deadlineMs] = useState<number | null>(() => (totalTimeS ? Date.now() + totalTimeS * 1000 : null));

  const q = slot.question;
  const isAutoGradable = q?.type === "numerical";
  const finished = q == null;

  useEffect(() => {
    setStartedAt(Date.now());
    setInput("");
    setLastResult(null);
    setHint(null);
  }, [slot.question?.question_id]);

  const finish = async () => {
    setBusy(true);
    try {
      const r = await ipc.quiz_finish(quizId);
      onFinished(r.attempt_id);
    } finally {
      setBusy(false);
    }
  };

  const submit = async (selfAssessment?: "got_it" | "partial" | "missed") => {
    if (!q) return;
    setBusy(true);
    try {
      const r = await ipc.quiz_submit_answer(quizId, slot.slot_index, {
        user_answer: input,
        self_assessment: selfAssessment ?? null,
        time_taken_ms: Date.now() - startedAt,
      });
      setLastResult({ ...r, questionId: q.question_id });
      if (r.partial_score !== undefined) setTotalScore((t) => t + r.partial_score!);
      setQuestionsAnswered((n) => n + 1);
      if (r.finished) {
        await finish();
        return;
      }
      if (settings.wait_for_correct && r.correct === false && !selfAssessment) {
        // Stay on the question; backend kept slot the same.
        return;
      }
      const repl = r.replacement;
      if (repl && "question_id" in repl) {
        // Backend non-PBS returns a Question shape (not the slot wrapper).
        setSlot({ slot_index: 0, question: repl as QuizSlot["question"], available_score: slot.available_score });
      } else if (repl && "slot_index" in repl) {
        setSlot(repl as QuizSlot);
      } else {
        // No replacement -> pool exhausted in some flows; backend's `finished` covers it.
      }
    } finally {
      setBusy(false);
    }
  };

  const skip = async () => {
    if (!q) return;
    setBusy(true);
    try {
      const r = await ipc.quiz_skip(quizId, slot.slot_index);
      if (r.partial_score !== undefined) setTotalScore((t) => t + r.partial_score!);
      if (r.finished) {
        await finish();
        return;
      }
      const repl = r.replacement;
      if (repl && "question_id" in repl) {
        setSlot({ slot_index: 0, question: repl as QuizSlot["question"], available_score: 0 });
      }
    } finally {
      setBusy(false);
    }
  };

  const requestHint = async () => {
    if (!q) return;
    const r = await ipc.quiz_request_hint(quizId, slot.slot_index);
    setHint(r.hint ?? "(no hint available for this question)");
  };

  if (finished) {
    return (
      <div className="mx-auto max-w-3xl px-6 py-6 text-center">
        <p className="text-muted">Wrapping up…</p>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-3xl space-y-4 px-6 py-6">
      <header className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-lg font-semibold">Quiz · {q.type}</h1>
          <p className="text-xs text-muted">
            {q.topic} / {q.branch} / {q.subtopic} · answered {questionsAnswered}
            {settings.show_scoring && <> · score {totalScore.toFixed(1)}</>}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <QuizCountdown deadlineMs={deadlineMs} onExpire={finish} />
          <Button variant="outline" size="sm" onClick={finish} disabled={busy}>
            Finish
          </Button>
        </div>
      </header>

      <Card>
        <LatexContent source={q.latexcode} />
        {q.instructions && (
          <p className="mt-3 text-xs italic text-muted">
            <LatexContent source={q.instructions} />
          </p>
        )}
      </Card>

      {hint && (
        <Card title="Hint">
          <LatexContent source={hint} />
        </Card>
      )}

      <Card title="Your answer">
        <Input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={isAutoGradable ? "e.g. 1/2 or 0.5 or \\boxed{1/2}" : "Free-form answer (you'll self-assess)"}
          disabled={busy || lastResult !== null}
          autoFocus
          onKeyDown={(e) => {
            if (e.key === "Enter" && !busy && lastResult === null && isAutoGradable) submit();
          }}
        />
        <div className="mt-3 flex flex-wrap items-center gap-2">
          {settings.enable_hints && !hint && (
            <Button variant="outline" size="sm" onClick={requestHint} disabled={busy}>
              <Lightbulb className="h-4 w-4" />
              Hint
            </Button>
          )}
          {settings.allow_skips && (
            <Button variant="ghost" size="sm" onClick={skip} disabled={busy || lastResult !== null}>
              <SkipForward className="h-4 w-4" />
              Skip
            </Button>
          )}
          {isAutoGradable && !lastResult && (
            <Button variant="primary" onClick={() => submit()} disabled={busy || !input.trim()}>
              <Send className="h-4 w-4" />
              Submit
            </Button>
          )}
          {!isAutoGradable && !lastResult && (
            <div className="ml-auto flex flex-wrap items-center gap-2">
              <span className="text-xs text-muted">Self-assess:</span>
              <Button variant="ghost" size="sm" onClick={() => submit("missed")} disabled={busy}>
                Missed
              </Button>
              <Button variant="outline" size="sm" onClick={() => submit("partial")} disabled={busy}>
                Partial
              </Button>
              <Button variant="primary" size="sm" onClick={() => submit("got_it")} disabled={busy}>
                Got it
              </Button>
            </div>
          )}
        </div>
      </Card>

      {lastResult && (
        <Card
          title={
            lastResult.correct === true
              ? "Correct"
              : lastResult.correct === false
                ? "Not quite"
                : "Recorded"
          }
        >
          <div className="space-y-2 text-sm">
            {settings.show_scoring && lastResult.partial_score !== undefined && (
              <p>+{lastResult.partial_score.toFixed(1)} points</p>
            )}
            {lastResult.canonical_answer && (
              <p>
                Canonical answer: <code className="font-mono">{lastResult.canonical_answer}</code>
              </p>
            )}
            {lastResult.solution && (
              <div>
                <div className="mb-1 text-xs font-medium uppercase tracking-wide text-muted">
                  Solution
                </div>
                <LatexContent source={lastResult.solution} />
              </div>
            )}
            <Button
              variant="primary"
              size="sm"
              onClick={() => setLastResult(null)}
              disabled={busy}
            >
              Next →
            </Button>
          </div>
        </Card>
      )}
    </div>
  );
}
