import { redirect } from "next/navigation";
import Link from "next/link";
import { getServerSupabase } from "@/lib/supabase/server";

type MasteryRow = {
  topic: string;
  branch: string;
  subtopic: string;
  alpha: number;
  beta: number;
  total_seen: number;
};

function masteryPercent(alpha: number, beta: number): number {
  // Posterior mean of Beta(alpha, beta).
  return (alpha / (alpha + beta)) * 100;
}

function lowerCredibilityBound(alpha: number, beta: number): number {
  // Quick approximation: posterior mean minus 1 SD. Conservative ordering
  // for "weakest" subtopics — penalises low-evidence rows.
  const mean = alpha / (alpha + beta);
  const variance =
    (alpha * beta) / ((alpha + beta) ** 2 * (alpha + beta + 1));
  return Math.max(0, mean - Math.sqrt(variance));
}

export default async function MePage() {
  const supabase = await getServerSupabase();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    redirect("/auth/login?next=/me");
  }

  const { data: mastery } = await supabase
    .from("user_mastery")
    .select("topic, branch, subtopic, alpha, beta, total_seen")
    .eq("user_id", user.id);

  const rows = (mastery ?? []) as MasteryRow[];

  const totalAnswered = rows.reduce((acc, r) => acc + r.total_seen, 0);
  const totalCorrect = rows.reduce(
    (acc, r) => acc + (r.alpha - 1), // alpha starts at 1 prior
    0
  );
  const overall =
    totalAnswered > 0
      ? Math.round((Math.max(0, totalCorrect) / totalAnswered) * 100)
      : 0;

  const strong = [...rows]
    .filter((r) => r.total_seen >= 2)
    .sort(
      (a, b) =>
        masteryPercent(b.alpha, b.beta) - masteryPercent(a.alpha, a.beta)
    )
    .slice(0, 5);

  const weak = [...rows]
    .filter((r) => r.total_seen >= 2)
    .sort(
      (a, b) =>
        lowerCredibilityBound(a.alpha, a.beta) -
        lowerCredibilityBound(b.alpha, b.beta)
    )
    .slice(0, 5);

  return (
    <main className="mx-auto max-w-3xl px-6 py-10">
      <div className="mb-8 flex items-start justify-between">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight">Your mastery</h1>
          <p className="mt-1 text-sm text-ink-500">
            Signed in as {user.email}
          </p>
        </div>
        <form action="/auth/signout" method="post">
          <button className="text-xs text-ink-500 underline hover:text-ink-900">
            sign out
          </button>
        </form>
      </div>

      {/* Headline cards */}
      <div className="mb-10 grid grid-cols-2 gap-3 sm:grid-cols-3">
        <Stat label="Questions answered" value={totalAnswered.toString()} />
        <Stat label="Overall accuracy" value={`${overall}%`} />
        <Stat
          label="Subtopics touched"
          value={rows.length.toString()}
        />
      </div>

      {totalAnswered === 0 ? (
        <div className="rounded-md border border-ink-200 bg-ink-50 p-6 text-sm">
          You haven&apos;t practiced yet. Start your first session →
          <Link href="/practice" className="ml-2 font-medium underline">
            Practice
          </Link>
        </div>
      ) : (
        <div className="grid gap-8 md:grid-cols-2">
          <div>
            <h2 className="mb-3 text-sm font-medium uppercase tracking-wide text-emerald-700">
              Strongest
            </h2>
            <ul className="space-y-2">
              {strong.length === 0 && (
                <li className="text-sm text-ink-500">
                  Need at least 2 answers per subtopic to rank.
                </li>
              )}
              {strong.map((r) => (
                <MasteryRowDisplay key={`${r.topic}|${r.branch}|${r.subtopic}`} r={r} />
              ))}
            </ul>
          </div>
          <div>
            <h2 className="mb-3 text-sm font-medium uppercase tracking-wide text-red-700">
              Weakest
            </h2>
            <ul className="space-y-2">
              {weak.length === 0 && (
                <li className="text-sm text-ink-500">
                  Need at least 2 answers per subtopic to rank.
                </li>
              )}
              {weak.map((r) => (
                <MasteryRowDisplay key={`${r.topic}|${r.branch}|${r.subtopic}`} r={r} />
              ))}
            </ul>
            {weak.length > 0 && (
              <Link
                href="/practice"
                className="mt-4 inline-block rounded-md bg-ink-900 px-4 py-2 text-sm font-medium text-white hover:bg-ink-700"
              >
                Practice your weakest
              </Link>
            )}
          </div>
        </div>
      )}
    </main>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-ink-200 p-4">
      <div className="text-2xl font-semibold">{value}</div>
      <div className="mt-1 text-xs text-ink-500">{label}</div>
    </div>
  );
}

function MasteryRowDisplay({ r }: { r: MasteryRow }) {
  const pct = Math.round(masteryPercent(r.alpha, r.beta));
  return (
    <li className="rounded-md border border-ink-200 px-3 py-2">
      <div className="flex items-center justify-between text-sm">
        <span className="font-medium">{r.subtopic}</span>
        <span className="text-ink-500">{pct}%</span>
      </div>
      <div className="text-xs text-ink-400">
        {r.topic} · {r.branch} · {r.total_seen} seen
      </div>
    </li>
  );
}
