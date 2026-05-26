import type { StatsBundle } from "@/lib/ipc";

interface Props {
  stats: StatsBundle | null;
}

interface CardSpec {
  label: string;
  value: (s: StatsBundle) => string;
  hint?: (s: StatsBundle) => string | null;
}

const CARDS: readonly CardSpec[] = [
  {
    label: "PSets Generated",
    value: (s) => s.psets_generated.toLocaleString(),
  },
  {
    label: "Total Questions Seen",
    value: (s) => s.total_questions_seen.toLocaleString(),
  },
  {
    label: "Unique Questions Seen",
    value: (s) => s.unique_questions_seen.toLocaleString(),
    hint: (s) =>
      s.total_questions_in_subject > 0
        ? `of ${s.total_questions_in_subject.toLocaleString()} in scope`
        : null,
  },
  {
    label: "Fraction Seen",
    value: (s) => `${s.fraction_questions_seen.toFixed(1)}%`,
  },
  {
    label: "Max in single PSet",
    value: (s) => s.max_questions_in_single_pset.toLocaleString(),
  },
  {
    label: "Max Multiplicity",
    value: (s) => s.max_question_multiplicity.toLocaleString(),
  },
  {
    label: "Avg Multiplicity",
    value: (s) => s.avg_question_multiplicity.toFixed(2),
  },
  {
    label: "Avg Difficulty",
    value: (s) =>
      s.avg_difficulty_rating == null ? "—" : s.avg_difficulty_rating.toFixed(2),
  },
];

export function StatsCards({ stats }: Props) {
  return (
    <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
      {CARDS.map((spec) => (
        <div
          key={spec.label}
          className="rounded-lg border border-border bg-surface p-4"
        >
          <div className="text-xs font-medium uppercase tracking-wide text-muted">
            {spec.label}
          </div>
          <div className="mt-1 text-2xl font-semibold tabular-nums">
            {stats ? spec.value(stats) : "—"}
          </div>
          {stats && spec.hint?.(stats) && (
            <div className="mt-1 text-xs text-muted">{spec.hint?.(stats)}</div>
          )}
        </div>
      ))}
    </div>
  );
}
