"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { LatexBlock } from "@/components/latex-block";
import { looselyEqual } from "@/lib/grade";

type Question = {
  id: number;
  topic: string;
  branch: string;
  subtopic: string;
  latexcode: string;
  answer: string | null;
};

type WidgetState = {
  q: Question;
  points: number;
  input: string;
  flash: "none" | "correct" | "wrong";
};

export function PbsRunner({
  pool,
  visibleN,
  initialPoints,
  timerSeconds,
}: {
  pool: Question[];
  visibleN: number;
  initialPoints: number;
  timerSeconds: number;
}) {
  // Phase: setup → running → done
  const [phase, setPhase] = useState<"setup" | "running" | "done">("setup");
  const [widgets, setWidgets] = useState<WidgetState[]>([]);
  const [poolIdx, setPoolIdx] = useState(visibleN);
  const [score, setScore] = useState(0);
  const [solved, setSolved] = useState(0);
  const [secondsLeft, setSecondsLeft] = useState(timerSeconds);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const haveEnough = pool.length >= visibleN;

  function start() {
    if (!haveEnough) return;
    const initial: WidgetState[] = pool.slice(0, visibleN).map((q) => ({
      q,
      points: initialPoints,
      input: "",
      flash: "none",
    }));
    setWidgets(initial);
    setPoolIdx(visibleN);
    setScore(0);
    setSolved(0);
    setSecondsLeft(timerSeconds);
    setPhase("running");
  }

  useEffect(() => {
    if (phase !== "running") return;
    timerRef.current = setInterval(() => {
      setSecondsLeft((s) => {
        if (s <= 1) {
          if (timerRef.current) clearInterval(timerRef.current);
          setPhase("done");
          return 0;
        }
        return s - 1;
      });
    }, 1000);
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [phase]);

  function submit(idx: number) {
    setWidgets((prev) => {
      const w = prev[idx];
      if (!w) return prev;
      if (!w.input.trim()) return prev;
      // If a canonical answer is present, grade strictly; otherwise self-grade
      // (treat the attempt as correct — pool turns over, decay still applies on
      // empty/blank submits via the early-return above).
      const correct = w.q.answer ? looselyEqual(w.input, w.q.answer) : true;
      const next = [...prev];
      if (correct) {
        // Award points, dequeue next from pool.
        setScore((s) => s + Math.max(1, Math.floor(w.points)));
        setSolved((n) => n + 1);
        // Pull next question; if pool exhausted, keep current widget hidden.
        let nextQ: Question | undefined;
        setPoolIdx((cur) => {
          if (cur < pool.length) {
            nextQ = pool[cur];
            return cur + 1;
          }
          return cur;
        });
        // setPoolIdx is async — use a synchronous read of `poolIdx` is unsafe.
        // Use a deterministic local read: pool[curIdx] right now.
        const localIdx = poolIdx; // captured before increment commits
        nextQ = pool[localIdx];
        if (nextQ) {
          next[idx] = {
            q: nextQ,
            points: initialPoints,
            input: "",
            flash: "correct",
          };
        } else {
          next[idx] = { ...w, input: "", flash: "correct" };
        }
      } else {
        // Halve points (min 1), flash wrong.
        next[idx] = {
          ...w,
          points: Math.max(1, w.points / 2),
          flash: "wrong",
        };
      }
      // Clear flash after 600ms.
      setTimeout(() => {
        setWidgets((p2) => {
          const n2 = [...p2];
          if (n2[idx]) n2[idx] = { ...n2[idx], flash: "none" };
          return n2;
        });
      }, 600);
      return next;
    });
  }

  function updateInput(idx: number, val: string) {
    setWidgets((prev) => {
      const next = [...prev];
      if (next[idx]) next[idx] = { ...next[idx], input: val };
      return next;
    });
  }

  const minutes = Math.floor(secondsLeft / 60);
  const seconds = secondsLeft % 60;

  const remainingPool = useMemo(
    () => Math.max(0, pool.length - poolIdx),
    [pool.length, poolIdx]
  );

  if (phase === "setup") {
    return (
      <div className="flex flex-col gap-4 rounded-md border border-ink-200 p-6">
        <div className="text-sm text-ink-500">
          Pool size: <span className="font-medium text-ink-900">{pool.length}</span>{" "}
          numerical questions
          {!haveEnough && (
            <span className="ml-2 text-red-600">
              (need ≥ {visibleN} — try again later)
            </span>
          )}
        </div>
        <div className="text-sm text-ink-500">
          Visible at once: <span className="font-medium text-ink-900">{visibleN}</span>{" "}
          · Starting points per widget:{" "}
          <span className="font-medium text-ink-900">{initialPoints}</span> · Timer:{" "}
          <span className="font-medium text-ink-900">
            {Math.floor(timerSeconds / 60)}:{(timerSeconds % 60).toString().padStart(2, "0")}
          </span>
        </div>
        <button
          type="button"
          onClick={start}
          disabled={!haveEnough}
          className="self-start rounded-md bg-ink-900 px-6 py-3 text-sm font-medium text-white hover:bg-ink-700 disabled:opacity-50"
        >
          Start PBS
        </button>
      </div>
    );
  }

  if (phase === "done") {
    return (
      <div className="flex flex-col gap-6">
        <div className="rounded-md border border-ink-200 bg-ink-50 p-6">
          <div className="text-5xl font-semibold tabular-nums">{score}</div>
          <div className="mt-2 text-sm text-ink-500">
            {solved} solved in {Math.floor(timerSeconds / 60)} min ·{" "}
            {remainingPool} questions left in pool
          </div>
        </div>
        <button
          type="button"
          onClick={() => setPhase("setup")}
          className="self-start rounded-md bg-ink-900 px-4 py-2 text-sm font-medium text-white hover:bg-ink-700"
        >
          Run again
        </button>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-6">
      {/* Top bar — score + timer (sticky) */}
      <div className="sticky top-14 z-10 -mx-6 flex items-center justify-between border-y border-ink-200 bg-white px-6 py-3 backdrop-blur">
        <div>
          <div className="text-2xl font-semibold tabular-nums">{score}</div>
          <div className="text-xs uppercase tracking-wider text-ink-500">
            score
          </div>
        </div>
        <div className="text-right">
          <div
            className={`text-2xl font-semibold tabular-nums ${secondsLeft < 30 ? "text-red-600" : "text-ink-900"}`}
          >
            {minutes}:{seconds.toString().padStart(2, "0")}
          </div>
          <div className="text-xs uppercase tracking-wider text-ink-500">
            remaining
          </div>
        </div>
      </div>

      {/* Tiled widget grid */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {widgets.map((w, idx) => (
          <div
            key={`${idx}-${w.q.id}`}
            className={`flex flex-col gap-3 rounded-md border-2 p-4 transition ${
              w.flash === "correct"
                ? "border-emerald-500 bg-emerald-50"
                : w.flash === "wrong"
                  ? "border-red-500 bg-red-50"
                  : "border-ink-200"
            }`}
          >
            <div className="flex items-center justify-between text-xs">
              <span className="text-ink-500">{w.q.subtopic}</span>
              <span className="rounded-full bg-brand-50 px-2 py-0.5 font-semibold tabular-nums text-brand-700">
                {Math.max(1, Math.floor(w.points))} pts
              </span>
            </div>
            <div className="flex-1">
              <LatexBlock src={w.q.latexcode} className="text-sm" />
            </div>
            <form
              onSubmit={(e) => {
                e.preventDefault();
                submit(idx);
              }}
              className="flex gap-2"
            >
              <input
                type="text"
                value={w.input}
                onChange={(e) => updateInput(idx, e.target.value)}
                placeholder="answer"
                className="flex-1 rounded-md border border-ink-200 px-2 py-1.5 text-sm focus:border-ink-500 focus:outline-none"
              />
              <button
                type="submit"
                className="rounded-md bg-ink-900 px-3 py-1.5 text-xs font-medium text-white hover:bg-ink-700"
              >
                ↵
              </button>
            </form>
          </div>
        ))}
      </div>
    </div>
  );
}
