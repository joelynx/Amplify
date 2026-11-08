/**
 * The daily loop on the Welcome page: what is due for review in the active
 * subject, one button to start a short review, and a way in from a lecture.
 * Hidden until there is something to review or the queue has been used.
 */

import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { CalendarClock, NotebookPen } from "lucide-react";

import { Button } from "../ui/Button";
import { ipc, type ReviewList, type ReviewSummary } from "../../lib/ipc";
import { formatWhen } from "./ReviewPanel";

export function TodayCard() {
  const navigate = useNavigate();
  const [subject, setSubject] = useState<string | null>(null);
  const [summary, setSummary] = useState<ReviewSummary | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      const active = await ipc.get_active_subject().catch(() => null);
      const s = await ipc.get_review_summary(active).catch(() => null);
      if (!cancelled) {
        setSubject(active);
        setSummary(s);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const start = (kind: ReviewList) => navigate("/quiz", { state: { startReview: kind, subject } });

  if (!summary) return null;
  const { due, mistakes, assisted } = summary.counts;

  let headline: string;
  let action: { label: string; kind: ReviewList } | null = null;
  if (due > 0) {
    headline = `${due} question${due === 1 ? "" : "s"} due for review`;
    action = { label: "Start a short review", kind: "due" };
  } else if (mistakes > 0) {
    headline = `Nothing due${summary.next_due ? ` until ${formatWhen(summary.next_due)}` : ""} · ${mistakes} past mistake${mistakes === 1 ? "" : "s"} to revisit`;
    action = { label: "Revisit mistakes", kind: "mistakes" };
  } else if (assisted > 0) {
    headline = `Nothing due · ${assisted} question${assisted === 1 ? "" : "s"} to try without help`;
    action = { label: "Try independently", kind: "assisted" };
  } else if (summary.tracked > 0) {
    headline = `All caught up${summary.next_due ? ` · next review ${formatWhen(summary.next_due)}` : ""}`;
  } else {
    headline = "Answer questions in Quiz and they come back here when they are due for review.";
  }

  return (
    <section className="w-full rounded-lg border border-border bg-surface p-4">
      <div className="flex flex-wrap items-center gap-3">
        <CalendarClock className="h-5 w-5 text-primary" />
        <div className="min-w-0 flex-1">
          <div className="text-xs font-medium uppercase tracking-wide text-muted">Today{subject ? ` · ${subject}` : ""}</div>
          <div className="text-sm font-semibold">{headline}</div>
        </div>
        {action && (
          <Button variant="primary" size="sm" onClick={() => start(action.kind)}>
            {action.label}
          </Button>
        )}
        <Button variant="outline" size="sm" onClick={() => navigate("/quiz", { state: { mode: "lecture" } })}>
          <NotebookPen className="h-4 w-4" />
          From a lecture
        </Button>
      </div>
    </section>
  );
}
