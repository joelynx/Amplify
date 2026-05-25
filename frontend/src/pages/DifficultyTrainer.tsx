/**
 * Pairwise difficulty trainer (spec §13.1 last bullet).
 *
 * Loads two random questions from the same (sub)topic. The user picks which
 * is harder + a magnitude (slightly / moderately / much), or marks them
 * equal. Each judgment fires `submit_pairwise_judgment` which runs one
 * gradient step on the per-topic weights stored in
 * `configs.DIFFICULTY_WEIGHTS`. The right rail shows live weights so the
 * user can watch them shift.
 */

import { useCallback, useEffect, useState } from "react";

import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { LatexContent } from "../components/browser/LatexContent";
import { ipc, type DifficultyWeights, type PairwisePair } from "../lib/ipc";

type Magnitude = 0.25 | 0.5 | 0.75;

const MAGNITUDES: { label: string; value: Magnitude }[] = [
  { label: "Slightly", value: 0.25 },
  { label: "Moderately", value: 0.5 },
  { label: "Much", value: 0.75 },
];

export default function DifficultyTrainerPage() {
  const [pair, setPair] = useState<PairwisePair | null>(null);
  const [topicHistory, setTopicHistory] = useState<Record<string, DifficultyWeights>>({});
  const [busy, setBusy] = useState(false);
  const [judged, setJudged] = useState(0);

  const loadNext = useCallback(async () => {
    setBusy(true);
    try {
      const p = await ipc.get_pairwise_pair(null);
      setPair(p);
      if (p) {
        setTopicHistory((prev) => ({ ...prev, [p.topic]: p.weights }));
      }
    } finally {
      setBusy(false);
    }
  }, []);

  useEffect(() => {
    loadNext();
  }, [loadNext]);

  const judge = async (harderSide: "a" | "b", magnitude: Magnitude) => {
    if (!pair) return;
    const harder = harderSide === "a" ? pair.a : pair.b;
    const easier = harderSide === "a" ? pair.b : pair.a;
    setBusy(true);
    try {
      const r = await ipc.submit_pairwise_judgment(
        harder.question.question_id,
        easier.question.question_id,
        magnitude,
      );
      if (r && r.weights) {
        setTopicHistory((prev) => ({ ...prev, [r.topic]: r.weights }));
      }
      setJudged((n) => n + 1);
      await loadNext();
    } finally {
      setBusy(false);
    }
  };

  const equal = async () => {
    // Treat "equal" as a small no-op: skip to the next pair without a gradient step.
    setJudged((n) => n + 1);
    await loadNext();
  };

  return (
    <main className="h-full overflow-y-auto">
      <div className="mx-auto max-w-6xl space-y-4 px-6 py-6">
        <header className="flex items-start justify-between gap-3">
          <div>
            <h1 className="text-2xl font-semibold">Train difficulty</h1>
            <p className="text-sm text-muted">
              Pick which question feels harder. Each judgment nudges the per-topic weights that
              combine length / novelty / depth into the final rating. {judged} judgment
              {judged === 1 ? "" : "s"} this session.
            </p>
          </div>
          <Button variant="outline" size="sm" onClick={loadNext} disabled={busy}>
            Skip pair →
          </Button>
        </header>

        {!pair && busy && <p className="text-muted">Loading a pair…</p>}
        {!pair && !busy && (
          <Card>
            <p className="text-muted">
              No pair available — need a subtopic with ≥2 questions in the bank.
            </p>
          </Card>
        )}

        {pair && (
          <>
            <p className="text-xs text-muted">
              Topic: <strong>{pair.topic}</strong> · current weights{" "}
              <code className="font-mono">
                length {(pair.weights.length * 100).toFixed(0)}% / novelty{" "}
                {(pair.weights.novelty * 100).toFixed(0)}% / depth{" "}
                {(pair.weights.depth * 100).toFixed(0)}%
              </code>
            </p>

            <div className="grid gap-4 md:grid-cols-2">
              <SideCard side="A" pair={pair} disabled={busy} onJudge={(m) => judge("a", m)} />
              <SideCard side="B" pair={pair} disabled={busy} onJudge={(m) => judge("b", m)} />
            </div>

            <div className="flex justify-center">
              <Button variant="ghost" onClick={equal} disabled={busy}>
                Roughly equal — skip
              </Button>
            </div>

            {Object.keys(topicHistory).length > 0 && (
              <Card title="Weights this session">
                <ul className="space-y-1 text-sm">
                  {Object.entries(topicHistory).map(([topic, w]) => (
                    <li key={topic} className="flex items-center justify-between gap-3">
                      <span className="font-medium">{topic}</span>
                      <span className="font-mono text-xs text-muted">
                        L {(w.length * 100).toFixed(0)} · N {(w.novelty * 100).toFixed(0)} · D{" "}
                        {(w.depth * 100).toFixed(0)}
                      </span>
                    </li>
                  ))}
                </ul>
              </Card>
            )}
          </>
        )}
      </div>
    </main>
  );
}

function SideCard({
  side,
  pair,
  disabled,
  onJudge,
}: {
  side: "A" | "B";
  pair: PairwisePair;
  disabled: boolean;
  onJudge: (mag: Magnitude) => void;
}) {
  const data = side === "A" ? pair.a : pair.b;
  return (
    <Card
      title={`Side ${side} · ${data.question.subtopic}`}
      actions={
        <span className="rounded-full bg-primary/10 px-2 py-0.5 text-xs font-semibold text-primary">
          rating {data.rating.toFixed(2)}
        </span>
      }
    >
      <div className="space-y-3">
        <LatexContent source={data.question.latexcode} />
        <dl className="grid grid-cols-3 gap-2 rounded-md border border-border bg-background p-2 text-xs">
          <SubScore label="length" value={data.sub_scores.length} />
          <SubScore label="novelty" value={data.sub_scores.novelty} />
          <SubScore label="depth" value={data.sub_scores.depth} />
        </dl>
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-xs text-muted">{side} is harder:</span>
          {MAGNITUDES.map((m) => (
            <Button
              key={m.value}
              variant="outline"
              size="sm"
              onClick={() => onJudge(m.value)}
              disabled={disabled}
            >
              {m.label}
            </Button>
          ))}
        </div>
      </div>
    </Card>
  );
}

function SubScore({ label, value }: { label: string; value: number }) {
  return (
    <div>
      <dt className="text-[10px] uppercase tracking-wide text-muted">{label}</dt>
      <dd className="font-mono text-sm">{value.toFixed(3)}</dd>
    </div>
  );
}
