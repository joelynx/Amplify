import { useCallback, useEffect, useMemo, useState } from "react";
import { Settings as Gear } from "lucide-react";

import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { StatsCards } from "../components/stats/StatsCards";
import { DistributionPie } from "../components/stats/DistributionPie";
import { StatsFiltersDialog } from "../components/stats/StatsFiltersDialog";
import { ipc, type DateRange, type DistributionDatum, type StatsBundle } from "../lib/ipc";

function defaultRange(): DateRange {
  const today = new Date();
  const past = new Date();
  past.setDate(today.getDate() - 30);
  return { from: iso(past), to: iso(today) };
}

function iso(d: Date): string {
  return d.toISOString().slice(0, 10);
}

function formatRange(range: DateRange): string {
  if (!range.from && !range.to) return "all time";
  return `${range.from ?? "…"} → ${range.to ?? "…"}`;
}

export default function StatsPage() {
  const [subject, setSubject] = useState<string | null>(null);
  const [dateRange, setDateRange] = useState<DateRange>(defaultRange);
  const [filtersOpen, setFiltersOpen] = useState(false);

  const [subjects, setSubjects] = useState<string[]>([]);
  const [stats, setStats] = useState<StatsBundle | null>(null);
  const [distribution, setDistribution] = useState<DistributionDatum[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    ipc.list_subjects().then(setSubjects);
  }, []);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const [s, dist] = await Promise.all([
        ipc.get_stats(subject, dateRange),
        subject
          ? ipc.get_topic_distribution(subject, dateRange)
          : ipc.get_subject_distribution(dateRange),
      ]);
      setStats(s);
      setDistribution(dist);
    } finally {
      setLoading(false);
    }
  }, [subject, dateRange]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const chartTitle = useMemo(
    () => (subject ? `Topic distribution — ${subject}` : "Subject distribution"),
    [subject],
  );

  return (
    <div className="flex h-full flex-col overflow-hidden">
      <header className="flex items-center justify-between border-b border-border bg-surface px-6 py-3">
        <div>
          <h1 className="text-2xl font-semibold">Stats</h1>
          <p className="text-xs text-muted">
            {subject ?? "All subjects"} · {formatRange(dateRange)}
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={() => setFiltersOpen(true)}>
          <Gear className="h-4 w-4" />
          Filters
        </Button>
      </header>

      <main className="flex-1 overflow-y-auto">
        <div className="mx-auto max-w-5xl space-y-6 px-6 py-6">
          <StatsCards stats={stats} />

          <Card title={chartTitle}>
            {loading && distribution.length === 0 ? (
              <p className="text-muted">Loading…</p>
            ) : distribution.length === 0 ? (
              <p className="text-muted">No data found for the selected filters.</p>
            ) : (
              <DistributionPie data={distribution} />
            )}
          </Card>
        </div>
      </main>

      <StatsFiltersDialog
        open={filtersOpen}
        onClose={() => setFiltersOpen(false)}
        initial={{ subject, dateRange }}
        subjects={subjects}
        onApply={(s, r) => {
          setSubject(s);
          setDateRange(r);
        }}
      />
    </div>
  );
}
