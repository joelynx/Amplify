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
import { useSubjectStore } from "../state/subject";
import { Card } from "../components/ui/Card";
import { StatsCards } from "../components/stats/StatsCards";
import { DistributionPie } from "../components/stats/DistributionPie";
import { StatsFiltersDialog } from "../components/stats/StatsFiltersDialog";
import { MultiplicityHistogram } from "../components/stats/MultiplicityHistogram";
import { CalendarHeatmap } from "../components/stats/CalendarHeatmap";
import { ActivityLine } from "../components/stats/ActivityLine";
import { TrendsPanel } from "../components/stats/TrendsPanel";
import { LearningPanel } from "../components/stats/LearningPanel";
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
  // Scope: the active subject, unless another is picked in Filters.
  const activeSubject = useSubjectStore((s) => s.active);
  const [subject, setSubject] = useState<string | null>(activeSubject);
  useEffect(() => setSubject(activeSubject), [activeSubject]);
  const [dateRange, setDateRange] = useState<DateRange>(defaultRange);
  const [filtersOpen, setFiltersOpen] = useState(false);

  const [mode, setMode] = useState<"generate" | "quiz">("generate");
  const [subjects, setSubjects] = useState<string[]>([]);
  const [stats, setStats] = useState<StatsBundle | null>(null);
  const [distribution, setDistribution] = useState<DistributionDatum[]>([]);
  const [sourceAttribution, setSourceAttribution] = useState<DistributionDatum[]>([]);
  const [multiplicity, setMultiplicity] = useState<Record<number, number>>({});
  const [heatmap, setHeatmap] = useState<Record<string, number>>({});
  const [activity, setActivity] = useState<ActivityDatum[]>([]);
  const [heatmapYear, setHeatmapYear] = useState<number>(() => new Date().getFullYear());
  const [heatmapMonth, setHeatmapMonth] = useState<number>(() => new Date().getMonth());
  const [heatmapMode, setHeatmapMode] = useState<"year" | "month">("year");
  const [loading, setLoading] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);

  useEffect(() => {
    ipc.list_subjects().then(setSubjects);
  }, []);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const [s, dist, src, mult, heat, act] = await Promise.all([
        ipc.get_stats(subject, dateRange, mode),
        subject
          ? ipc.get_topic_distribution(subject, dateRange, mode)
          : ipc.get_subject_distribution(dateRange, mode),
        ipc.get_source_attribution(subject, dateRange, mode),
        ipc.get_question_multiplicity_dist(subject, mode, dateRange),
        ipc.get_calendar_heatmap(heatmapYear, mode),
        ipc.get_activity_line(dateRange, mode),
      ]);
      setStats(s);
      setDistribution(dist);
      setSourceAttribution(src);
      setMultiplicity(mult);
      setHeatmap(heat);
      setActivity(act);
      setRefreshKey((k) => k + 1);
    } finally {
      setLoading(false);
    }
  }, [subject, dateRange, heatmapYear, mode]);

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
          <div role="group" aria-label="Activity shown" className="flex bg-background border border-border rounded-md p-1 mr-2 text-sm font-medium">
            <button
              aria-pressed={mode === "generate"}
              className={`px-3 py-1 rounded-sm transition-colors ${mode === "generate" ? "bg-primary text-on-primary shadow-sm" : "text-text/80 hover:bg-surface hover:text-text"}`}
              onClick={() => setMode("generate")}
            >
              Papers
            </button>
            <button
              aria-pressed={mode === "quiz"}
              className={`px-3 py-1 rounded-sm transition-colors ${mode === "quiz" ? "bg-primary text-on-primary shadow-sm" : "text-text/80 hover:bg-surface hover:text-text"}`}
              onClick={() => setMode("quiz")}
            >
              Quizzes
            </button>
          </div>
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
          {/* Learning first; how much the app was used comes after. */}
          <LearningPanel subject={subject} dateRange={dateRange} refreshKey={refreshKey} />

          <div className="border-t border-border pt-5">
            <h2 className="text-lg font-semibold">Usage</h2>
            <p className="text-xs text-muted">
              {mode === "generate" ? "Papers created" : "Quizzes taken"} · {subject ?? "All subjects"} ·{" "}
              {formatRange(dateRange)}
            </p>
          </div>

          <StatsCards stats={stats} mode={mode} />

          <TrendsPanel subject={subject} mode={mode} refreshKey={refreshKey} />

          <Card title={chartTitle}>
            {loading && distribution.length === 0 ? (
              <p className="text-muted">Loading…</p>
            ) : distribution.length === 0 ? (
              <p className="text-muted">No data found for the selected filters.</p>
            ) : (
              <DistributionPie data={distribution} />
            )}
          </Card>

          <Card title="Source fraction (attempted questions)">
            {loading && sourceAttribution.length === 0 ? (
              <p className="text-muted">Loading…</p>
            ) : sourceAttribution.length === 0 ? (
              <p className="text-muted">
                No questions practiced in the selected range yet — {mode === "generate" ? "create a paper" : "take a quiz"} to fill this in.
              </p>
            ) : (
              <DistributionPie data={sourceAttribution} />
            )}
          </Card>

          <Card title="How often each question was used (in range)">
            {Object.keys(multiplicity).length === 0 ? (
              <p className="text-muted">No questions used in the selected range under the current subject filter.</p>
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
                No {mode === "generate" ? "papers created" : "quizzes taken"} in {heatmapMode === "year" ? heatmapYear : monthLabel}.
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
