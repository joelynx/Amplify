import type { StatsBundle } from "../../lib/ipc";

interface Props {
  stats: StatsBundle | null;
  mode: "generate" | "quiz";
}

interface CardSpec {
  label: (mode: "generate" | "quiz") => string;
  value: (s: StatsBundle) => string;
  hint?: (s: StatsBundle, mode: "generate" | "quiz") => string | null;
}

const CARDS: readonly CardSpec[] = [
  {
    label: (mode) => mode === "generate" ? "Papers created" : "Quizzes completed",
    value: (s) => (s.sessions_completed ?? (s as any).psets_generated ?? 0).toLocaleString(),
  },
  {
    label: (mode) => mode === "generate" ? "Partial papers" : "Partial quizzes",
    value: (s) => (s.sessions_partial ?? 0).toLocaleString(),
  },
  {
    label: () => "Questions seen, with repeats",
    value: (s) => (s.total_questions_seen ?? 0).toLocaleString(),
  },
  {
    label: () => "Different questions seen",
    value: (s) => (s.unique_questions_seen ?? 0).toLocaleString(),
    hint: (s) =>
      (s.total_questions_in_subject ?? 0) > 0
        ? `of ${(s.total_questions_in_subject ?? 0).toLocaleString()} in scope`
        : null,
  },
  {
    label: () => "Share of the bank seen",
    value: (s) => `${(s.fraction_questions_seen ?? 0).toFixed(1)}%`,
  },
  {
    label: (mode) => mode === "generate" ? "Largest paper" : "Longest quiz",
    value: (s) => (s.max_questions_in_single_pset ?? 0).toLocaleString(),
  },
  {
    label: () => "Most uses of one question",
    value: (s) => (s.max_question_multiplicity ?? 0).toLocaleString(),
  },
  {
    label: () => "Average uses per question",
    value: (s) => (s.avg_question_multiplicity ?? 0).toFixed(2),
  },
  {
    label: () => "Average difficulty",
    value: (s) =>
      s.avg_difficulty_rating == null ? "—" : s.avg_difficulty_rating.toFixed(2),
  },
];

export function StatsCards({ stats, mode }: Props) {
  return (
    <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
      {CARDS.map((spec) => (
        <div
          key={spec.label(mode)}
          className="rounded-lg border border-border bg-surface p-4"
        >
          <div className="text-xs font-medium uppercase tracking-wide text-muted">
            {spec.label(mode)}
          </div>
          <div className="mt-1 text-2xl font-semibold tabular-nums">
            {stats ? spec.value(stats) : "—"}
          </div>
          {stats && spec.hint?.(stats, mode) && (
            <div className="mt-1 text-xs text-muted">{spec.hint?.(stats, mode)}</div>
          )}
        </div>
      ))}
    </div>
  );
}
