import { getServerSupabase } from "@/lib/supabase/server";
import { Card } from "@/components/ui/Card";
import { StatsCards } from "@/components/stats/StatsCards";
import { DistributionPie } from "@/components/stats/DistributionPie";
import { MultiplicityHistogram } from "@/components/stats/MultiplicityHistogram";
import { CalendarHeatmap } from "@/components/stats/CalendarHeatmap";
import { ActivityLine } from "@/components/stats/ActivityLine";
import type {
  StatsBundle,
  DistributionDatum,
  ActivityDatum,
} from "@/lib/ipc";

function isoDay(d: Date): string {
  const y = d.getFullYear();
  const m = `${d.getMonth() + 1}`.padStart(2, "0");
  const day = `${d.getDate()}`.padStart(2, "0");
  return `${y}-${m}-${day}`;
}

export default async function StatsPage() {
  const supabase = await getServerSupabase();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  // ── Sessions scoped to user (if signed in) or global. ────────────────────
  let sessionQ = supabase
    .from("practice_sessions")
    .select("id, n_target, created_at");
  if (user) sessionQ = sessionQ.eq("user_id", user.id);
  const { data: sessions } = await sessionQ;
  const sessionRows = (sessions ?? []) as {
    id: string;
    n_target: number;
    created_at: string;
  }[];

  const psetsGenerated = sessionRows.length;
  const maxQsInOnePset = sessionRows.reduce(
    (m, s) => Math.max(m, s.n_target),
    0
  );

  // ── Responses for total/unique questions seen + activity. ────────────────
  const sessionIds = sessionRows.map((s) => s.id);
  let totalAnswered = 0;
  const uniqueQs = new Set<number>();
  const dailyCounts = new Map<string, { papers: Set<string>; q: number }>();
  if (sessionIds.length > 0) {
    const { data: responses } = await supabase
      .from("practice_responses")
      .select("question_id, user_answer, session_id, answered_at")
      .in("session_id", sessionIds);
    for (const r of responses ?? []) {
      const row = r as {
        question_id: number;
        user_answer: string | null;
        session_id: string;
        answered_at: string | null;
      };
      if (row.user_answer !== null) {
        totalAnswered++;
        uniqueQs.add(row.question_id);
        if (row.answered_at) {
          const day = isoDay(new Date(row.answered_at));
          const cur = dailyCounts.get(day) ?? {
            papers: new Set<string>(),
            q: 0,
          };
          cur.papers.add(row.session_id);
          cur.q++;
          dailyCounts.set(day, cur);
        }
      }
    }
  }

  // ── Bank-level question stats. ──────────────────────────────────────────
  const { data: qStats } = await supabase
    .from("questions")
    .select("times_used, difficulty_rating, topic");
  const qRows = (qStats ?? []) as {
    times_used: number;
    difficulty_rating: number | null;
    topic: string;
  }[];

  const totalQuestionsInBank = qRows.length;
  let maxMult = 0;
  let multSum = 0;
  let multCount = 0;
  let diffSum = 0;
  let diffCount = 0;
  const multHist: Record<number, number> = {};
  const topicCounts = new Map<string, number>();
  for (const r of qRows) {
    if (r.times_used > maxMult) maxMult = r.times_used;
    if (r.times_used > 0) {
      multSum += r.times_used;
      multCount++;
      multHist[r.times_used] = (multHist[r.times_used] ?? 0) + 1;
    }
    if (r.difficulty_rating && r.difficulty_rating > 0) {
      diffSum += r.difficulty_rating;
      diffCount++;
    }
    topicCounts.set(r.topic, (topicCounts.get(r.topic) ?? 0) + 1);
  }

  const stats: StatsBundle = {
    psets_generated: psetsGenerated,
    total_questions_seen: totalAnswered,
    unique_questions_seen: uniqueQs.size,
    total_questions_in_subject: totalQuestionsInBank,
    fraction_questions_seen:
      totalQuestionsInBank > 0
        ? (uniqueQs.size / totalQuestionsInBank) * 100
        : 0,
    max_questions_in_single_pset: maxQsInOnePset,
    max_question_multiplicity: maxMult,
    avg_question_multiplicity: multCount > 0 ? multSum / multCount : 0,
    avg_difficulty_rating: diffCount > 0 ? diffSum / diffCount : null,
  };

  const distribution: DistributionDatum[] = [...topicCounts.entries()]
    .map(([label, count]) => ({ label, count }))
    .sort((a, b) => b.count - a.count);

  // Calendar heatmap — current year, papers (sessions) per day.
  const year = new Date().getFullYear();
  const heatmap: Record<string, number> = {};
  for (const s of sessionRows) {
    const day = isoDay(new Date(s.created_at));
    heatmap[day] = (heatmap[day] ?? 0) + 1;
  }

  // Activity line — last 30 days from now.
  const activity: ActivityDatum[] = [];
  const now = new Date();
  for (let i = 29; i >= 0; i--) {
    const d = new Date(now);
    d.setDate(d.getDate() - i);
    const day = isoDay(d);
    const v = dailyCounts.get(day);
    activity.push({
      date: day,
      papers: v ? v.papers.size : 0,
      questions: v ? v.q : 0,
    });
  }

  return (
    <main className="mx-auto max-w-5xl px-6 py-10">
      <header className="mb-8">
        <h1 className="text-3xl font-semibold tracking-tight">Stats</h1>
        <p className="mt-1 text-sm text-muted">
          {user
            ? `Scoped to ${user.email}`
            : "Global bank stats — sign in for per-user numbers"}
        </p>
      </header>

      {/* The 8 cards */}
      <div className="mb-10">
        <StatsCards stats={stats} />
      </div>

      {/* Two-column: topic distribution pie + multiplicity histogram */}
      <div className="mb-10 grid gap-6 md:grid-cols-2">
        <Card title="Bank composition by topic">
          {distribution.length > 0 ? (
            <DistributionPie data={distribution} />
          ) : (
            <p className="text-sm text-muted">No data.</p>
          )}
        </Card>

        <Card title="Question multiplicity">
          {Object.keys(multHist).length > 0 ? (
            <MultiplicityHistogram data={multHist} />
          ) : (
            <p className="text-sm text-muted">
              No questions have been practiced yet.
            </p>
          )}
        </Card>
      </div>

      {/* Activity line — last 30 days */}
      <div className="mb-10">
        <Card title="Activity — last 30 days">
          {activity.some((d) => d.papers + d.questions > 0) ? (
            <ActivityLine data={activity} />
          ) : (
            <p className="text-sm text-muted">No activity in the last 30 days.</p>
          )}
        </Card>
      </div>

      {/* Calendar heatmap — current year */}
      <Card title={`Calendar — ${year}`}>
        <CalendarHeatmap data={heatmap} year={year} />
      </Card>
    </main>
  );
}
