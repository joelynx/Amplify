/**
 * The review queue on the Quiz page: questions due again, open mistakes,
 * questions only solved with help, and bookmarks. Each list starts a short
 * session; rows can be taken off the queue (back when answered again).
 *
 * Scheduling lives in app/core/review.py: a miss or an assisted answer comes
 * back the next day; independent successes come back after 3, 7 and 21 days,
 * then retire.
 */

import { useCallback, useEffect, useState } from "react";
import { CalendarClock, ChevronDown, ChevronRight, Lightbulb, RotateCcw, Star, X } from "lucide-react";

import { Button } from "../ui/Button";
import { cn } from "../../lib/cn";
import { ipc, type ReviewList, type ReviewRow, type ReviewSummary } from "../../lib/ipc";

interface Props {
  subject: string | null;
  onStart: (kind: ReviewList) => void;
}

const LISTS: { kind: ReviewList; title: string; blurb: string; Icon: typeof RotateCcw }[] = [
  {
    kind: "due",
    title: "Review due",
    blurb: "Scheduled to come back today: missed ones after a day, solved ones after a longer gap.",
    Icon: CalendarClock,
  },
  { kind: "mistakes", title: "Review mistakes", blurb: "Your last try was missed or only partly right.", Icon: RotateCcw },
  {
    kind: "assisted",
    title: "Try independently",
    blurb: "Solved with a hint, or you opened the answer or solution first.",
    Icon: Lightbulb,
  },
  { kind: "bookmarked", title: "Bookmarks", blurb: "Questions you starred.", Icon: Star },
];

const OUTCOME_LABEL: Record<string, string> = {
  missed: "missed",
  partial: "partly right",
  assisted: "with help",
  independent: "solved",
};

export function formatWhen(iso: string | null | undefined): string {
  if (!iso) return "—";
  const d = new Date(iso);
  const days = Math.round((d.getTime() - Date.now()) / 86_400_000);
  if (days === 0) return "today";
  if (days === 1) return "tomorrow";
  if (days === -1) return "yesterday";
  return days > 0 ? `in ${days} days` : `${-days} days ago`;
}

export function ReviewPanel({ subject, onStart }: Props) {
  const [summary, setSummary] = useState<ReviewSummary | null>(null);
  const [open, setOpen] = useState<ReviewList | null>(null);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(() => {
    ipc
      .get_review_summary(subject)
      .then((s) => {
        setSummary(s);
        setError(null);
      })
      .catch((e) => setError(e instanceof Error ? e.message : String(e)));
  }, [subject]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const dismiss = async (row: ReviewRow) => {
    await ipc.dismiss_review(row.question_id);
    refresh();
  };

  if (error) return <p className="text-sm text-error">{error}</p>;
  if (!summary) return <p className="text-sm text-muted">Loading your review queue…</p>;

  const empty = summary.tracked === 0 && summary.counts.bookmarked === 0;

  return (
    <div className="space-y-3">
      {empty ? (
        <p className="text-sm text-muted">
          Nothing to review yet. Answer questions in Traverse, Discover or a lecture session (or record results
          for a printed paper in History) and they will come back here when they are due.
        </p>
      ) : (
        <p className="text-xs text-muted">
          {summary.tracked} question{summary.tracked === 1 ? "" : "s"} tracked · {summary.retired} retired after
          three successful reviews
          {summary.next_due && summary.counts.due === 0 ? ` · next one due ${formatWhen(summary.next_due)}` : ""}
        </p>
      )}
      {LISTS.map(({ kind, title, blurb, Icon }) => {
        const count = summary.counts[kind];
        const rows = summary.lists[kind] ?? [];
        const expanded = open === kind;
        return (
          <div key={kind} className="rounded-lg border border-border bg-background">
            <div className="flex items-center gap-3 p-3">
              <button
                type="button"
                className="flex flex-1 items-center gap-3 text-left disabled:cursor-default"
                onClick={() => setOpen(expanded ? null : kind)}
                disabled={count === 0}
              >
                {count > 0 ? (
                  expanded ? <ChevronDown className="h-4 w-4 text-muted" /> : <ChevronRight className="h-4 w-4 text-muted" />
                ) : (
                  <span className="w-4" />
                )}
                <Icon className={cn("h-4 w-4", count > 0 ? "text-primary" : "text-muted")} />
                <span className="flex-1">
                  <span className="block text-sm font-semibold">
                    {title} <span className="tabular-nums text-muted">· {count}</span>
                  </span>
                  <span className="block text-xs text-muted">{blurb}</span>
                </span>
              </button>
              <Button size="sm" variant={kind === "due" ? "primary" : "outline"} disabled={count === 0} onClick={() => onStart(kind)}>
                {kind === "due" ? "Start a short review" : "Start"}
              </Button>
            </div>
            {expanded && rows.length > 0 && (
              <ul className="divide-y divide-border border-t border-border">
                {rows.map((row) => (
                  <li key={row.question_id} className="flex items-start gap-3 px-3 py-2 text-xs">
                    <span className="w-14 shrink-0 font-mono text-muted">#{row.question_id}</span>
                    <span className="min-w-0 flex-1">
                      <span className="block truncate font-medium text-text">
                        {row.topic} › {row.subtopic}
                      </span>
                      <span className="block truncate text-muted">{row.preview}</span>
                    </span>
                    <span className="shrink-0 text-right text-muted">
                      {row.last_outcome && <span className="block">{OUTCOME_LABEL[row.last_outcome]} {formatWhen(row.last_at)}</span>}
                      {row.due_at && <span className="block">due {formatWhen(row.due_at)}</span>}
                    </span>
                    {kind !== "bookmarked" && (
                      <button
                        type="button"
                        title="Take off the review queue (it returns if you answer it again)"
                        className="shrink-0 rounded p-1 text-muted hover:bg-surface hover:text-text"
                        onClick={() => void dismiss(row)}
                      >
                        <X className="h-3.5 w-3.5" />
                      </button>
                    )}
                  </li>
                ))}
                {count > rows.length && (
                  <li className="px-3 py-2 text-xs text-muted">…and {count - rows.length} more</li>
                )}
              </ul>
            )}
          </div>
        );
      })}
    </div>
  );
}
