import { redirect } from "next/navigation";
import Link from "next/link";
import { getServerSupabase } from "@/lib/supabase/server";
import type { PracticeFilters } from "@/lib/db/types";
import { RunAgainButton } from "./run-again-button";

type SessionRow = {
  id: string;
  filters: PracticeFilters;
  n_target: number;
  mode: string | null;
  diversity_score: number | null;
  created_at: string;
  completed_at: string | null;
};

export default async function HistoryPage() {
  const supabase = await getServerSupabase();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) {
    redirect("/auth/login?next=/history");
  }
  // TA / faculty don't have practice history — bounce to /author.
  const { data: profileRow } = await supabase
    .from("user_profiles")
    .select("role")
    .eq("user_id", user.id)
    .maybeSingle();
  const r = (profileRow as { role?: string } | null)?.role;
  if (r === "faculty" || r === "admin" || r === "moderator") {
    redirect("/author");
  }

  const { data: rows } = await supabase
    .from("practice_sessions")
    .select(
      "id, filters, n_target, mode, diversity_score, created_at, completed_at"
    )
    .eq("user_id", user.id)
    .order("created_at", { ascending: false })
    .limit(50);
  const sessions = (rows ?? []) as SessionRow[];

  // Fetch response counts per session for the answered/total badges.
  const responsesPerSession = new Map<
    string,
    { total: number; answered: number }
  >();
  const sessionIds = sessions.map((s) => s.id);
  if (sessionIds.length > 0) {
    const { data: responses } = await supabase
      .from("practice_responses")
      .select("session_id, user_answer")
      .in("session_id", sessionIds);
    for (const r of responses ?? []) {
      const row = r as { session_id: string; user_answer: string | null };
      const cur = responsesPerSession.get(row.session_id) ?? {
        total: 0,
        answered: 0,
      };
      cur.total++;
      if (row.user_answer !== null) cur.answered++;
      responsesPerSession.set(row.session_id, cur);
    }
  }

  return (
    <main className="mx-auto max-w-3xl px-6 py-10">
      <h1 className="mb-8 text-3xl font-semibold tracking-tight">History</h1>

      {sessions.length === 0 ? (
        <div className="rounded-md border border-ink-200 bg-ink-50 p-6 text-sm">
          No sessions yet.{" "}
          <Link href="/practice" className="font-medium underline">
            Start your first one →
          </Link>
        </div>
      ) : (
        <ul className="space-y-3">
          {sessions.map((s) => {
            const counts = responsesPerSession.get(s.id) ?? {
              total: s.n_target,
              answered: 0,
            };
            const completed =
              counts.answered === counts.total && counts.total > 0;
            const subtopicSummary =
              (s.filters?.subtopics ?? []).slice(0, 3).join(" · ") ||
              (s.filters?.topics ?? []).slice(0, 3).join(" · ") ||
              "all topics";
            const extraSubs = Math.max(
              0,
              (s.filters?.subtopics ?? []).length - 3
            );
            return (
              <li
                key={s.id}
                className="rounded-md border border-ink-200 p-3 transition hover:border-ink-400"
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0 flex-1">
                    <div className="text-sm font-medium text-ink-900">
                      {new Date(s.created_at).toLocaleString()}
                    </div>
                    <div className="mt-0.5 truncate text-xs text-ink-500">
                      {subtopicSummary}
                      {extraSubs > 0 && (
                        <span className="text-ink-400"> +{extraSubs}</span>
                      )}
                    </div>
                    <div className="mt-1 flex flex-wrap items-center gap-2 text-xs text-ink-500">
                      <Pill>{s.n_target} Qs</Pill>
                      <Pill>{s.mode ?? "random"}</Pill>
                      {s.diversity_score !== null && (
                        <Pill>div {s.diversity_score.toFixed(2)}</Pill>
                      )}
                      <Pill>
                        {counts.answered}/{counts.total} answered
                      </Pill>
                      {completed && (
                        <span className="text-emerald-700">done</span>
                      )}
                    </div>
                  </div>
                  <div className="flex shrink-0 gap-2">
                    <Link
                      href={`/practice/${s.id}`}
                      className="rounded-md border border-ink-200 px-3 py-1.5 text-xs hover:bg-ink-50"
                    >
                      View
                    </Link>
                    <RunAgainButton
                      filters={s.filters}
                      nTarget={s.n_target}
                      mode={(s.mode ?? "random") as "random" | "diverse"}
                    />
                  </div>
                </div>
              </li>
            );
          })}
        </ul>
      )}
    </main>
  );
}

function Pill({ children }: { children: React.ReactNode }) {
  return (
    <span className="rounded-full border border-ink-200 px-2 py-0.5">
      {children}
    </span>
  );
}
