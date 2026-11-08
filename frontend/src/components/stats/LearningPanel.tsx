/**
 * Learning measures on the Stats page (app/core/learning.py). Quiz answers
 * and recorded paper results together, inside the selected range.
 *
 * Every number shows its denominator ("4 of 6"), not a bare percentage.
 * Self-assessed answers are the student's own marks and answers from before
 * hint use was recorded are "assistance unknown"; both are counted apart from
 * auto-graded unaided ones. These are decision aids: each topic row has a
 * "Practise this" action, and reviews due start a session directly.
 */

import { type ReactNode, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { GraduationCap } from "lucide-react";

import { Button } from "../ui/Button";
import { Card } from "../ui/Card";
import { ipc, type DateRange, type LearningStats, type TemplatePayload } from "../../lib/ipc";
import { formatWhen } from "../quiz/ReviewPanel";

interface Props {
  subject: string | null;
  dateRange: DateRange;
  /** Bumped by the page's refresh button. */
  refreshKey?: number;
}

function ofText(k: number, n: number): string {
  return n === 0 ? "—" : `${k} of ${n}`;
}

function topicTemplate(subject: string | null, topic: string): TemplatePayload {
  return {
    name: "",
    subject,
    topic_list: [topic],
    branch_list: [],
    subtopic_list: [],
    type_list: [],
    source_list: [],
    tag_list: { compulsory: [], optional: [], excluded: [] },
    n_questions: 10,
    reuse_questions: false,
    include_sources: true,
    in_syllabus_only: true,
    min_difficulty: null,
    save_directory: null,
    solutions: null,
  };
}

function Tile({ label, value, hint, action }: { label: string; value: string; hint?: string; action?: ReactNode }) {
  return (
    <div className="flex flex-col rounded-lg border border-border bg-background p-3">
      <div className="text-xs font-medium uppercase tracking-wide text-muted">{label}</div>
      <div className="mt-1 text-xl font-semibold tabular-nums">{value}</div>
      {hint && <div className="mt-0.5 text-xs text-muted">{hint}</div>}
      {action && <div className="mt-2">{action}</div>}
    </div>
  );
}

export function LearningPanel({ subject, dateRange, refreshKey = 0 }: Props) {
  const navigate = useNavigate();
  const [stats, setStats] = useState<LearningStats | null>(null);
  const [showAll, setShowAll] = useState(false);

  useEffect(() => {
    let cancelled = false;
    ipc.get_learning_stats(subject, dateRange).then((s) => {
      if (!cancelled) setStats(s);
    });
    return () => {
      cancelled = true;
    };
  }, [subject, dateRange, refreshKey]);

  if (!stats) return null;

  const { funnel, first_attempts: fa, delayed, reviews } = stats;
  const practised = stats.topics.filter((t) => t.attempted > 0 || t.first_attempts > 0);
  const rows = showAll || practised.length === 0 ? stats.topics.filter((t) => t.in_scope > 0) : practised;
  const review = (kind: "due" | "mistakes" | "assisted") =>
    navigate("/quiz", { state: { startReview: kind, subject } });
  const unaidedNote = [
    funnel.independent_self ? `${funnel.independent_self} self-assessed` : "",
    funnel.independent_unknown ? `${funnel.independent_unknown} with hint use not recorded` : "",
  ]
    .filter(Boolean)
    .join(" · ");

  return (
    <Card
      title={
        <span className="inline-flex items-center gap-2">
          <GraduationCap className="h-4 w-4 text-primary" />
          Learning
        </span>
      }
    >
      <p className="mb-3 text-xs text-muted">
        Quiz answers and paper results you recorded in History. Generated {funnel.generated} · shown{" "}
        {funnel.presented} · attempted {funnel.attempted} · with help {funnel.assisted} · solved unaided{" "}
        {funnel.independent}
        {unaidedNote ? ` (${unaidedNote})` : ""}.
      </p>

      <div className="grid grid-cols-2 gap-3 md:grid-cols-5">
        <Tile
          label="First try, unaided"
          value={ofText(fa.independent, fa.n)}
          hint="questions met for the first time in this range"
        />
        <Tile
          label="To revisit"
          value={String(stats.revisit)}
          hint="last try missed, partial or with help"
          action={
            reviews.mistakes + reviews.assisted > 0 ? (
              <Button size="sm" variant="outline" onClick={() => review(reviews.mistakes > 0 ? "mistakes" : "assisted")}>
                Revisit
              </Button>
            ) : undefined
          }
        />
        <Tile
          label="Delayed reviews"
          value={ofText(delayed.independent, delayed.n)}
          hint="solved unaided a day or more later"
        />
        <Tile
          label="Coverage"
          value={`${practised.length} of ${stats.topics.filter((t) => t.in_scope > 0).length}`}
          hint="topics practised"
        />
        <Tile
          label="Reviews due"
          value={String(reviews.due)}
          hint={reviews.due === 0 && reviews.next_due ? `next ${formatWhen(reviews.next_due)}` : "right now"}
          action={
            reviews.due > 0 ? (
              <Button size="sm" variant="primary" onClick={() => review("due")}>
                Start
              </Button>
            ) : undefined
          }
        />
      </div>

      <div className="mt-4 overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border text-left text-xs uppercase tracking-wide text-muted">
              <th className="py-2 pr-3 font-medium">Topic</th>
              <th className="py-2 pr-3 font-medium">Attempted</th>
              <th className="py-2 pr-3 font-medium">First try unaided</th>
              <th className="py-2 pr-3 font-medium">Solved unaided</th>
              <th className="py-2 pr-3 font-medium">To revisit</th>
              <th className="py-2 pr-3 font-medium">Delayed reviews</th>
              <th className="py-2 pr-3 font-medium">Avg difficulty</th>
              <th className="py-2" />
            </tr>
          </thead>
          <tbody>
            {rows.map((t) => (
              <tr key={t.topic} className="border-b border-border/60">
                <td className="py-2 pr-3 font-medium">{t.topic}</td>
                <td className="py-2 pr-3 tabular-nums">
                  {t.attempted} <span className="text-xs text-muted">of {t.in_scope}</span>
                </td>
                <td className="py-2 pr-3 tabular-nums">{ofText(t.first_independent, t.first_attempts)}</td>
                <td className="py-2 pr-3 tabular-nums">
                  {t.independent}
                  {t.independent_self > 0 && (
                    <span className="text-xs text-muted"> ({t.independent_self} self-assessed)</span>
                  )}
                </td>
                <td className="py-2 pr-3 tabular-nums">{t.revisit || "—"}</td>
                <td className="py-2 pr-3 tabular-nums">{ofText(t.delayed_success, t.delayed)}</td>
                <td className="py-2 pr-3 tabular-nums">{t.avg_difficulty ?? "—"}</td>
                <td className="py-2 text-right">
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => navigate("/quiz", { state: { template: topicTemplate(subject, t.topic) } })}
                  >
                    Practise this
                  </Button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {practised.length === 0 && (
          <p className="mt-2 text-xs text-muted">No answers in this range yet; every topic in scope is listed.</p>
        )}
        {practised.length > 0 && (
          <button type="button" className="mt-2 text-xs text-primary hover:underline" onClick={() => setShowAll((v) => !v)}>
            {showAll ? "Only topics practised in this range" : "Also show topics not practised yet"}
          </button>
        )}
      </div>

      {fa.n > 0 && (
        <p className="mt-3 text-xs text-muted">
          First try unaided by difficulty band:{" "}
          {stats.bands
            .filter((b) => b.first_attempts > 0)
            .map((b) => `${b.band}: ${b.first_independent} of ${b.first_attempts}`)
            .join(" · ")}
          . Difficulty is a heuristic (solution length, novelty, topic depth), so compare like with like rather
          than reading it as a skill score.
        </p>
      )}
    </Card>
  );
}
