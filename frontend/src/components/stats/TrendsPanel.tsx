/**
 * Step 21: the "Trends" panel. Surfaces 0–5 detected patterns. Each row's CTA
 * navigates to /generate with a pre-filled template payload — same plumbing
 * History uses for "Generate similar". When there are no insights the panel
 * hides itself entirely (no "no trends" message).
 */

import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Lightbulb } from "lucide-react";

import { Button } from "../ui/Button";
import { Card } from "../ui/Card";
import { ipc, type TrendInsight } from "../../lib/ipc";

interface Props {
  subject: string | null;
}

export function TrendsPanel({ subject }: Props) {
  const navigate = useNavigate();
  const [insights, setInsights] = useState<TrendInsight[]>([]);

  useEffect(() => {
    let cancelled = false;
    ipc.get_trends(subject).then((rows) => {
      if (!cancelled) setInsights(rows);
    });
    return () => {
      cancelled = true;
    };
  }, [subject]);

  if (insights.length === 0) return null;

  return (
    <Card
      title={
        <span className="inline-flex items-center gap-2">
          <Lightbulb className="h-4 w-4 text-primary" />
          Trends
        </span>
      }
    >
      <ul className="space-y-3">
        {insights.map((insight) => (
          <li
            key={insight.id}
            className="flex flex-col gap-2 rounded-md border border-border/60 bg-background p-3 sm:flex-row sm:items-center sm:justify-between"
          >
            <div className="flex-1">
              <div className="text-sm font-semibold">{insight.title}</div>
              <p className="mt-0.5 text-xs text-muted">{insight.body}</p>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() =>
                navigate("/generate", { state: { template: insight.cta_filters } })
              }
            >
              {insight.cta_label}
            </Button>
          </li>
        ))}
      </ul>
    </Card>
  );
}
