import { useCallback, useEffect, useMemo, useState } from "react";
import {
  ChevronLeft,
  ChevronRight,
  RotateCw,
  Settings as Gear,
  ZoomIn,
  ZoomOut,
} from "lucide-react";

import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { StatsCards } from "../components/stats/StatsCards";
import { DistributionPie } from "../components/stats/DistributionPie";
import { StatsFiltersDialog } from "../components/stats/StatsFiltersDialog";
import { MultiplicityHistogram } from "../components/stats/MultiplicityHistogram";
import { CalendarHeatmap } from "../components/stats/CalendarHeatmap";
import { ActivityLine } from "../components/stats/ActivityLine";
import {
  ipc,
  type ActivityDatum,
  type DateRange,
  type DistributionDatum,
  type StatsBundle,
} from "../lib/ipc";

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
  const [multiplicity, setMultiplicity] = useState<Record<number, number>>({});
  const [heatmap, setHeatmap] = useState<Record<string, number>>({});
  const [activity, setActivity] = useState<ActivityDatum[]>([]);
  const [heatmapYear, setHeatmapYear] = useState<number>(() => new Date().getFullYear());
  const [heatmapMonth, setHeatmapMonth] = useState<number>(() => new Date().getMonth());
  const [heatmapMode, setHeatmapMode] = useState<"year" | "month">("year");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    ipc.list_subjects().then(setSubjects);
  }, []);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const [s, dist, mult, heat, act] = await Promise.all([
        ipc.get_stats(subject, dateRange),
        subject
          ? ipc.get_topic_distribution(subject, dateRange)
          : ipc.get_subject_distribution(dateRange),
        ipc.get_question_multiplicity_dist(subject),
        ipc.get_calendar_heatmap(heatmapYear),
        ipc.get_activity_line(dateRange),
      ]);
      setStats(s);
      setDistribution(dist);
      setMultiplicity(mult);
      setHeatmap(heat);
      setActivity(act);
    } finally {
      setLoading(false);
    }
  }, [subject, dateRange, heatmapYear]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const chartTitle = useMemo(
    () => (subject ? `Topic distribution — ${subject}` : "Subject distribution"),
    [subject],
  );

  // Heatmap navigation — clamped so the user can't drift past "now".
  const now = new Date();
  const atToday =
    heatmapMode === "year"
      ? heatmapYear >= now.getFullYear()
      : heatmapYear > now.getFullYear() ||
        (heatmapYear === now.getFullYear() && heatmapMonth >= now.getMonth());
  const goPrev = () => {
    if (heatmapMode === "year") setHeatmapYear((y) => y - 1);
    else {
      if (heatmapMonth === 0) {
        setHeatmapMonth(11);
        setHeatmapYear((y) => y - 1);
      } else setHeatmapMonth((m) => m - 1);
    }
  };
  const goNext = () => {
    if (atToday) return;
    if (heatmapMode === "year") setHeatmapYear((y) => y + 1);
    else {
      if (heatmapMonth === 11) {
        setHeatmapMonth(0);
        setHeatmapYear((y) => y + 1);
      } else setHeatmapMonth((m) => m + 1);
    }
  };
  const goToday = () => {
    setHeatmapYear(now.getFullYear());
    setHeatmapMonth(now.getMonth());
  };
  const monthLabel = new Date(heatmapYear, heatmapMonth, 1).toLocaleString(undefined, {
    month: "long",
    year: "numeric",
  });
  const heatmapTitle =
    heatmapMode === "year" ? `Activity heatmap · ${heatmapYear}` : `Activity heatmap · ${monthLabel}`;

  return (
    <div className="flex h-full flex-col overflow-hidden">
      <header className="flex items-center justify-between border-b border-border bg-surface px-6 py-3">
        <div>
          <h1 className="text-2xl font-semibold">Stats</h1>
          <p className="text-xs text-muted">
            {subject ?? "All subjects"} · {formatRange(dateRange)}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={refresh}
            disabled={loading}
            aria-label="Refresh"
            title="Refresh stats"
          >
            <RotateCw className={"h-4 w-4 " + (loading ? "animate-spin" : "")} />
          </Button>
          <Button variant="outline" size="sm" onClick={() => setFiltersOpen(true)}>
            <Gear className="h-4 w-4" />
            Filters
          </Button>
        </div>
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

          <Card title="Question multiplicity">
            {Object.keys(multiplicity).length === 0 ? (
              <p className="text-muted">No questions used yet under the current subject filter.</p>
            ) : (
              <MultiplicityHistogram data={multiplicity} />
            )}
          </Card>

          <Card
            title={heatmapTitle}
            actions={
              <div className="flex items-center gap-1">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setHeatmapMode((m) => (m === "year" ? "month" : "year"))}
                  aria-label={heatmapMode === "year" ? "Zoom into month" : "Zoom out to year"}
                  title={heatmapMode === "year" ? "Zoom into month" : "Zoom out to year"}
                >
                  {heatmapMode === "year" ? (
                    <ZoomIn className="h-4 w-4" />
                  ) : (
                    <ZoomOut className="h-4 w-4" />
                  )}
                </Button>
                <Button variant="ghost" size="sm" onClick={goPrev} aria-label="Previous">
                  <ChevronLeft className="h-4 w-4" />
                </Button>
                <Button variant="ghost" size="sm" onClick={goToday}>
                  Today
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={goNext}
                  disabled={atToday}
                  aria-label="Next"
                  title={atToday ? "Already at the current period" : "Next"}
                >
                  <ChevronRight className="h-4 w-4" />
                </Button>
              </div>
            }
          >
            <CalendarHeatmap
              data={heatmap}
              year={heatmapYear}
              month={heatmapMonth}
              mode={heatmapMode}
            />
            {Object.keys(heatmap).length === 0 && (
              <p className="mt-2 text-xs text-muted">
                No PSets generated in {heatmapMode === "year" ? heatmapYear : monthLabel}.
              </p>
            )}
          </Card>

          <Card title="Activity over selected range">
            {activity.length === 0 ? (
              <p className="text-muted">No activity in the selected date range.</p>
            ) : (
              <ActivityLine data={activity} />
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
