import { redirect } from "next/navigation";
import Link from "next/link";
import { getServerSupabase } from "@/lib/supabase/server";

export default async function FacultyPage() {
  const supabase = await getServerSupabase();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) redirect("/auth/login?next=/faculty");

  const { data: profile } = await supabase
    .from("user_profiles")
    .select("*, institution:institutions(*)")
    .eq("user_id", user.id)
    .maybeSingle();

  const role = (profile as { role?: string } | null)?.role;
  if (role !== "faculty" && role !== "admin" && role !== "moderator") {
    return (
      <main className="mx-auto max-w-2xl px-6 py-16">
        <h1 className="display text-3xl font-semibold">Faculty access</h1>
        <p className="mt-3 text-ink-500">
          This dashboard is for faculty, moderators, and admins. You&apos;re
          signed in as <strong>{user.email}</strong>, role:{" "}
          <code>{role ?? "student"}</code>.
        </p>
        <p className="mt-3 text-ink-500">
          To request faculty access at your institution, email{" "}
          <a
            href="mailto:24a1cseb0015@iitdabudhabi.ac.ae?subject=Faculty%20access%20request"
            className="underline"
          >
            24a1cseb0015@iitdabudhabi.ac.ae
          </a>{" "}
          from your institution&apos;s email address with a one-liner about
          which department.
        </p>
        <div className="mt-6 flex gap-3">
          <Link
            href="/me"
            className="rounded-md bg-ink-900 px-4 py-2 text-sm font-medium text-white hover:bg-ink-700"
          >
            Back to your mastery
          </Link>
        </div>
      </main>
    );
  }

  const institution = (
    profile as { institution?: { id: number; short_name: string; name: string; slug: string } | null } | null
  )?.institution;

  // Aggregate mastery across all signed-in students at this institution.
  // Bayesian beta: lower CI bound identifies "weakest" subtopics with confidence.
  const { data: cohortMastery } = await supabase
    .from("user_mastery")
    .select("topic, branch, subtopic, alpha, beta, total_seen, user_id")
    .limit(5000);

  // Group by subtopic.
  const subtopicAgg = new Map<
    string,
    { topic: string; branch: string; subtopic: string; totalAlpha: number; totalBeta: number; students: Set<string>; totalSeen: number }
  >();

  for (const r of cohortMastery ?? []) {
    const key = `${r.topic}|${r.branch}|${r.subtopic}`;
    const agg = subtopicAgg.get(key);
    if (agg) {
      agg.totalAlpha += r.alpha;
      agg.totalBeta += r.beta;
      agg.totalSeen += r.total_seen;
      agg.students.add(r.user_id);
    } else {
      subtopicAgg.set(key, {
        topic: r.topic,
        branch: r.branch,
        subtopic: r.subtopic,
        totalAlpha: r.alpha,
        totalBeta: r.beta,
        totalSeen: r.total_seen,
        students: new Set([r.user_id]),
      });
    }
  }

  const ranked = [...subtopicAgg.values()].map((a) => {
    const mean = a.totalAlpha / (a.totalAlpha + a.totalBeta);
    const variance =
      (a.totalAlpha * a.totalBeta) /
      ((a.totalAlpha + a.totalBeta) ** 2 *
        (a.totalAlpha + a.totalBeta + 1));
    return {
      ...a,
      mean,
      lcb: Math.max(0, mean - Math.sqrt(variance)),
    };
  });

  const weakest = [...ranked]
    .filter((r) => r.students.size >= 1)
    .sort((a, b) => a.lcb - b.lcb)
    .slice(0, 8);

  const strongest = [...ranked]
    .filter((r) => r.students.size >= 1)
    .sort((a, b) => b.mean - a.mean)
    .slice(0, 5);

  // Sessions this week, institution-scoped if we had institution_id on session;
  // for now, all-sessions in the last 7 days.
  const { count: sessionsThisWeek } = await supabase
    .from("practice_sessions")
    .select("id", { count: "exact", head: true })
    .gte(
      "created_at",
      new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString()
    );

  const totalStudents = new Set(
    (cohortMastery ?? []).map((r) => r.user_id)
  ).size;

  return (
    <main className="hero-bg">
      <section className="mx-auto max-w-5xl px-6 py-16">
        <div className="flex flex-col gap-2">
          <div className="text-sm font-mono uppercase tracking-wider text-brand-600">
            faculty dashboard
          </div>
          <h1 className="display text-4xl font-semibold">
            Cohort mastery — {institution?.short_name ?? "your institution"}
          </h1>
          <p className="mt-1 text-ink-500">
            Aggregate across {totalStudents} student
            {totalStudents === 1 ? "" : "s"} who&apos;ve practiced. Use the
            weakest subtopics to plan your next session or quiz.
          </p>
        </div>

        <dl className="mt-10 grid grid-cols-2 gap-3 sm:grid-cols-4">
          <Stat value={totalStudents.toString()} label="students practicing" />
          <Stat value={sessionsThisWeek?.toString() ?? "0"} label="sessions this week" />
          <Stat value={subtopicAgg.size.toString()} label="subtopics touched" />
          <Stat
            value={
              ranked.length > 0
                ? Math.round(
                    (ranked.reduce((s, r) => s + r.mean, 0) / ranked.length) *
                      100
                  ).toString() + "%"
                : "—"
            }
            label="cohort accuracy"
          />
        </dl>

        {ranked.length === 0 ? (
          <div className="mt-12 rounded-lg border border-dashed border-ink-200 p-8 text-center text-ink-500">
            No practice data yet. As students start practicing, you&apos;ll see
            cohort-level mastery rollups here.
          </div>
        ) : (
          <div className="mt-12 grid gap-10 md:grid-cols-2">
            <div>
              <h2 className="mb-3 text-sm font-medium uppercase tracking-wider text-red-700">
                Where your cohort struggles
              </h2>
              <p className="mb-4 text-sm text-ink-500">
                Ranked by lower credibility bound. Address these in your next
                session.
              </p>
              <ul className="space-y-2">
                {weakest.map((r) => (
                  <SubtopicRow
                    key={`${r.topic}|${r.branch}|${r.subtopic}`}
                    r={r}
                    variant="weak"
                  />
                ))}
              </ul>
            </div>
            <div>
              <h2 className="mb-3 text-sm font-medium uppercase tracking-wider text-emerald-700">
                Where they shine
              </h2>
              <p className="mb-4 text-sm text-ink-500">
                Don&apos;t over-emphasise these — your cohort already has them.
              </p>
              <ul className="space-y-2">
                {strongest.map((r) => (
                  <SubtopicRow
                    key={`${r.topic}|${r.branch}|${r.subtopic}`}
                    r={r}
                    variant="strong"
                  />
                ))}
              </ul>
            </div>
          </div>
        )}

        <section className="mt-16 rounded-lg border border-ink-200 bg-ink-50 p-8">
          <h2 className="display text-xl font-semibold">
            Next: author a question
          </h2>
          <p className="mt-2 text-sm text-ink-700">
            Spotted a gap? Add a question to the bank. Live LaTeX preview,
            instant peer review queue, full attribution.
          </p>
          <Link
            href="/author"
            className="mt-4 inline-block rounded-md bg-ink-900 px-5 py-2.5 text-sm font-medium text-white hover:bg-ink-700"
          >
            Open the authoring page →
          </Link>
        </section>
      </section>
    </main>
  );
}

function Stat({ value, label }: { value: string; label: string }) {
  return (
    <div className="rounded-md border border-ink-200 bg-white px-4 py-3">
      <dt className="text-2xl font-semibold tracking-tight">{value}</dt>
      <dd className="text-xs uppercase tracking-wider text-ink-500">
        {label}
      </dd>
    </div>
  );
}

function SubtopicRow({
  r,
  variant,
}: {
  r: {
    topic: string;
    branch: string;
    subtopic: string;
    mean: number;
    students: Set<string>;
    totalSeen: number;
  };
  variant: "weak" | "strong";
}) {
  const pct = Math.round(r.mean * 100);
  return (
    <li className="rounded-md border border-ink-200 bg-white px-4 py-3">
      <div className="flex items-center justify-between">
        <div className="font-medium">{r.subtopic}</div>
        <div
          className={
            "text-sm font-semibold " +
            (variant === "weak" ? "text-red-600" : "text-emerald-600")
          }
        >
          {pct}%
        </div>
      </div>
      <div className="mt-0.5 text-xs text-ink-500">
        {r.topic} · {r.branch} · {r.students.size} student
        {r.students.size === 1 ? "" : "s"} · {r.totalSeen} attempts
      </div>
    </li>
  );
}
