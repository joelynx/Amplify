"use client";

import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import { LatexBlock } from "@/components/latex-block";

type Question = {
  id: number;
  topic: string;
  branch: string;
  subtopic: string;
  latexcode: string;
  type: "proof" | "numerical" | "explanation/reasoning";
  source: string | null;
  subsource: string | null;
  answer: string | null;
  solution: string | null;
};

type SessionMeta = {
  id: string;
  mode?: "random" | "diverse" | null;
  diversity_score?: number | null;
};

type SessionState = {
  session?: SessionMeta | null;
  total: number;
  answered: number;
  correct: number;
  next_order: number | null;
  next_question: Question | null;
  completed: boolean;
};

type Feedback = {
  is_correct: boolean | null;
  canonical_answer: string | null;
  solution: string | null;
  gradeable: boolean;
  requires_self_assessment: boolean;
};

type SelfAssessment = "got_it" | "partial" | "missed";

export function PracticeRunner({ sessionId }: { sessionId: string }) {
  const [state, setState] = useState<SessionState | null>(null);
  const [input, setInput] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [feedback, setFeedback] = useState<Feedback | null>(null);
  const [selfAssessed, setSelfAssessed] = useState<SelfAssessment | null>(null);
  const [startedAt, setStartedAt] = useState<number>(Date.now());
  const [error, setError] = useState<string>("");

  const load = useCallback(async () => {
    setError("");
    const res = await fetch(`/api/sessions/${sessionId}`);
    if (!res.ok) {
      setError("Could not load session.");
      return;
    }
    const json = (await res.json()) as SessionState;
    setState(json);
    setInput("");
    setFeedback(null);
    setSelfAssessed(null);
    setStartedAt(Date.now());
  }, [sessionId]);

  useEffect(() => {
    load();
  }, [load]);

  async function submitAnswer(userAnswer: string) {
    if (!state?.next_question) return;
    setSubmitting(true);
    setError("");
    try {
      const res = await fetch(`/api/sessions/${sessionId}/answer`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question_id: state.next_question.id,
          user_answer: userAnswer,
          time_taken_ms: Date.now() - startedAt,
        }),
      });
      if (!res.ok) {
        const j = await res.json().catch(() => ({}));
        throw new Error(j.error || `HTTP ${res.status}`);
      }
      const json = (await res.json()) as Feedback;
      setFeedback(json);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setSubmitting(false);
    }
  }

  async function submitSelfAssessment(assessment: SelfAssessment) {
    if (!state?.next_question) return;
    setSubmitting(true);
    try {
      const res = await fetch(`/api/sessions/${sessionId}/answer`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question_id: state.next_question.id,
          user_answer: input || "(self-assessed)",
          self_assessment: assessment,
          time_taken_ms: Date.now() - startedAt,
        }),
      });
      if (!res.ok) {
        const j = await res.json().catch(() => ({}));
        throw new Error(j.error || `HTTP ${res.status}`);
      }
      setSelfAssessed(assessment);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setSubmitting(false);
    }
  }

  async function handleNext() {
    await load();
  }

  if (!state) {
    return <p className="text-sm text-ink-500">Loading session…</p>;
  }

  if (state.completed) {
    const pct =
      state.total > 0 ? Math.round((state.correct / state.total) * 100) : 0;
    const POINTS_PER_Q = 10;
    const score = state.correct * POINTS_PER_Q;
    const maxScore = state.total * POINTS_PER_Q;
    return (
      <div className="flex flex-col gap-6">
        <h1 className="text-3xl font-semibold tracking-tight">Session done</h1>
        <div className="rounded-md border border-ink-200 bg-ink-50 p-6">
          <div className="text-5xl font-semibold tabular-nums">
            {score}
            <span className="text-2xl text-ink-400"> / {maxScore}</span>
          </div>
          <div className="mt-2 text-sm text-ink-500">
            {state.correct} of {state.total} marked correct · {pct}% accuracy ·{" "}
            {POINTS_PER_Q} pts per question
          </div>
        </div>
        <div className="flex flex-wrap gap-3">
          <Link
            href="/practice"
            className="rounded-md bg-ink-900 px-4 py-2 text-sm font-medium text-white hover:bg-ink-700"
          >
            Start another
          </Link>
          <Link
            href={`/practice/${sessionId}/print`}
            className="rounded-md border border-ink-200 px-4 py-2 text-sm font-medium hover:bg-ink-50"
          >
            Print / Save as PDF
          </Link>
          <Link
            href="/me"
            className="rounded-md border border-ink-200 px-4 py-2 text-sm font-medium hover:bg-ink-50"
          >
            See mastery
          </Link>
        </div>
      </div>
    );
  }

  const q = state.next_question;
  if (!q) {
    return <p className="text-sm text-ink-500">No questions in this session.</p>;
  }

  const progress = `${state.answered + 1} / ${state.total}`;

  return (
    <div className="flex flex-col gap-6">
      {/* Progress + score + crumbs */}
      <div className="flex flex-wrap items-center justify-between gap-2 text-xs text-ink-500">
        <div className="flex items-center gap-3">
          <span>{progress}</span>
          <span className="rounded-full border border-ink-200 px-2 py-0.5 font-medium tabular-nums text-ink-700">
            {state.correct * 10} pts
          </span>
        </div>
        <span>
          {q.topic} › {q.branch} › {q.subtopic}
        </span>
      </div>

      {/* Diversity badge — surfaces the DPP-selection signal when mode=diverse. */}
      {state.session?.mode === "diverse" &&
        state.session.diversity_score !== null &&
        state.session.diversity_score !== undefined && (
          <div className="-mt-2 inline-flex items-center gap-2 self-start rounded-full border border-brand-200 bg-brand-50 px-3 py-1 text-xs font-medium text-brand-700">
            <span className="size-1.5 rounded-full bg-brand-500" />
            Diverse session · diversity {state.session.diversity_score.toFixed(2)}
          </div>
        )}

      {/* Question body */}
      <article>
        <LatexBlock src={q.latexcode} className="text-lg leading-relaxed" />
      </article>

      {/* Answer form */}
      {!feedback && (
        <form
          onSubmit={(e) => {
            e.preventDefault();
            submitAnswer(input);
          }}
          className="flex flex-col gap-3"
        >
          <label className="text-sm text-ink-700">
            {q.type === "proof"
              ? "Sketch your approach"
              : q.type === "numerical"
                ? "Your answer"
                : "Your reasoning"}
            <input
              type="text"
              autoFocus
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder={
                q.type === "numerical"
                  ? "a number, expression, or $\\frac{p}{q}$"
                  : "key idea or final claim — you'll grade yourself"
              }
              className="mt-1 w-full rounded-md border border-ink-200 px-3 py-2 text-sm focus:border-ink-500 focus:outline-none"
            />
          </label>
          <div className="flex gap-2">
            <button
              type="submit"
              disabled={submitting}
              className="rounded-md bg-ink-900 px-4 py-2 text-sm font-medium text-white hover:bg-ink-700 disabled:opacity-50"
            >
              {submitting ? "Submitting..." : "Reveal solution"}
            </button>
            <button
              type="button"
              onClick={() => submitAnswer("skip")}
              className="rounded-md border border-ink-200 px-4 py-2 text-sm font-medium hover:bg-ink-50"
            >
              Skip
            </button>
          </div>
          {error && <p className="text-sm text-red-600">{error}</p>}
        </form>
      )}

      {/* Feedback + self-assessment */}
      {feedback && (
        <div className="flex flex-col gap-4">
          {feedback.is_correct === true && !feedback.requires_self_assessment && (
            <div className="rounded-md border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-900">
              ✓ Correct
            </div>
          )}
          {feedback.is_correct === false &&
            !feedback.requires_self_assessment && (
              <div className="rounded-md border border-red-200 bg-red-50 p-4 text-sm text-red-900">
                ✗ Not quite. Canonical answer:{" "}
                <strong>{feedback.canonical_answer ?? "—"}</strong>
              </div>
            )}

          {/* Solution always available after attempt */}
          {feedback.solution && (
            <div className="rounded-md border border-ink-200 p-4">
              <div className="mb-2 text-xs font-medium uppercase tracking-wide text-ink-400">
                Solution
              </div>
              <LatexBlock src={feedback.solution} />
            </div>
          )}

          {/* Self-assessment buttons for non-gradeable */}
          {feedback.requires_self_assessment && selfAssessed === null && (
            <div className="rounded-md border border-amber-200 bg-amber-50 p-4">
              <div className="mb-3 text-sm text-amber-900">
                How did you do?
              </div>
              <div className="flex flex-wrap gap-2">
                <button
                  onClick={() => submitSelfAssessment("got_it")}
                  disabled={submitting}
                  className="rounded-md bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-700 disabled:opacity-50"
                >
                  ✓ Got it
                </button>
                <button
                  onClick={() => submitSelfAssessment("partial")}
                  disabled={submitting}
                  className="rounded-md bg-amber-500 px-4 py-2 text-sm font-medium text-white hover:bg-amber-600 disabled:opacity-50"
                >
                  ~ Partial
                </button>
                <button
                  onClick={() => submitSelfAssessment("missed")}
                  disabled={submitting}
                  className="rounded-md bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700 disabled:opacity-50"
                >
                  ✗ Missed it
                </button>
              </div>
            </div>
          )}

          {selfAssessed !== null && (
            <div className="rounded-md border border-ink-200 bg-ink-50 p-3 text-sm text-ink-700">
              Recorded: <strong>{selfAssessed.replace("_", " ")}</strong>.
              Mastery updated.
            </div>
          )}

          <button
            onClick={handleNext}
            disabled={feedback.requires_self_assessment && selfAssessed === null}
            className="self-start rounded-md bg-ink-900 px-6 py-3 text-sm font-medium text-white hover:bg-ink-700 disabled:opacity-50"
          >
            Next question →
          </button>
        </div>
      )}
    </div>
  );
}
