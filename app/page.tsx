import Link from "next/link";
import { getServerSupabase } from "@/lib/supabase/server";
import { getPublicStats } from "@/lib/stats";
import { getInstitutions } from "@/lib/cached";
import { lowerCredibilityBound } from "@/lib/mastery";
import type { Institution } from "@/lib/db/types";

type MasteryRow = {
  topic: string;
  branch: string;
  subtopic: string;
  alpha: number;
  beta: number;
  total_seen: number;
};

export default async function Home() {
  const supabase = await getServerSupabase();

  const [stats, institutions, { data: { user } }] = await Promise.all([
    getPublicStats(supabase),
    getInstitutions(),
    supabase.auth.getUser(),
  ]);

  // Role-aware strip: students see mastery, TAs/faculty see authoring CTA.
  let weakest: MasteryRow[] = [];
  let userRole: string | null = null;
  if (user) {
    const { data: profileRow } = await supabase
      .from("user_profiles")
      .select("role")
      .eq("user_id", user.id)
      .maybeSingle();
    userRole = (profileRow as { role?: string } | null)?.role ?? "student";

    if (userRole === "student") {
      const { data: mastery } = await supabase
        .from("user_mastery")
        .select("topic, branch, subtopic, alpha, beta, total_seen")
        .eq("user_id", user.id);
      weakest = ((mastery ?? []) as MasteryRow[])
        .filter((r) => r.total_seen >= 2)
        .sort(
          (a, b) =>
            lowerCredibilityBound({
              alpha: a.alpha,
              beta: a.beta,
              total_seen: a.total_seen,
            }) -
            lowerCredibilityBound({
              alpha: b.alpha,
              beta: b.beta,
              total_seen: b.total_seen,
            })
        )
        .slice(0, 3);
    }
  }
  const isFaculty =
    userRole === "faculty" || userRole === "admin" || userRole === "moderator";

  const active = (institutions ?? []).filter(
    (i) => (i as Institution).status === "active"
  ) as Institution[];
  const interested = (institutions ?? []).filter(
    (i) => (i as Institution).status === "interested"
  ) as Institution[];

  return (
    <main className="hero-bg">
      {/* Personalised dashboard strip — role-aware. */}
      {user && (
        <section className="border-b border-ink-200 bg-brand-50/60">
          <div className="mx-auto max-w-5xl px-6 py-6">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div className="min-w-0">
                <div className="text-xs uppercase tracking-wider text-brand-700">
                  Welcome back, {user.email?.split("@")[0]}
                </div>
                {isFaculty ? (
                  <p className="mt-1 text-sm text-ink-900">
                    Contributor account — add new questions to the bank.
                  </p>
                ) : weakest.length > 0 ? (
                  <p className="mt-1 text-sm text-ink-900">
                    Your weakest right now:{" "}
                    <span className="font-medium">
                      {weakest.map((w) => w.subtopic).join(" · ")}
                    </span>
                  </p>
                ) : (
                  <p className="mt-1 text-sm text-ink-500">
                    Practice 2+ questions per subtopic to unlock your mastery view.
                  </p>
                )}
              </div>
              <div className="flex flex-wrap gap-2">
                {isFaculty ? (
                  <Link
                    href="/author"
                    className="rounded-md bg-ink-900 px-4 py-2 text-sm font-medium text-white hover:bg-ink-700"
                  >
                    Add a question →
                  </Link>
                ) : (
                  <>
                    <Link
                      href="/practice"
                      className="rounded-md bg-ink-900 px-4 py-2 text-sm font-medium text-white hover:bg-ink-700"
                    >
                      {weakest.length > 0 ? "Practice these →" : "Start practicing →"}
                    </Link>
                    <Link
                      href="/me"
                      className="rounded-md border border-ink-200 bg-white px-4 py-2 text-sm font-medium hover:bg-ink-50"
                    >
                      Full mastery
                    </Link>
                  </>
                )}
              </div>
            </div>
          </div>
        </section>
      )}

      {/* Hero */}
      <section className="mx-auto max-w-5xl px-6 py-20 sm:py-28">
        <div className="flex flex-col gap-7">
          <span className="self-start rounded-full border border-ink-200 bg-white/60 px-3 py-1 text-xs font-medium uppercase tracking-wider text-ink-500">
            built at IIT-Delhi Abu Dhabi · open commons
          </span>

          <h1 className="display max-w-3xl text-5xl font-semibold sm:text-6xl">
            The problem-bank commons
            <br />
            <span className="text-ink-500">for university STEM.</span>
          </h1>

          <p className="max-w-2xl text-lg text-ink-500">
            A bank of university math, physics, and CS problems built by
            IIT-AD&rsquo;s TAs. Mastery-tracked practice for students.
            One-click contribution for TAs.
          </p>

          <div className="flex flex-wrap gap-3">
            <Link
              href={
                isFaculty
                  ? "/author"
                  : user
                    ? "/practice"
                    : "/auth/login?next=/practice"
              }
              className="rounded-md bg-ink-900 px-5 py-3 text-sm font-medium text-white shadow-sm hover:bg-ink-700"
            >
              {isFaculty
                ? "Add a question →"
                : user
                  ? "Start practicing →"
                  : "Sign in to practice →"}
            </Link>
            <Link
              href="/q"
              className="rounded-md border border-ink-200 bg-white px-5 py-3 text-sm font-medium hover:bg-ink-50"
            >
              Browse the bank
            </Link>
            <Link
              href="/for-institutions"
              className="rounded-md px-5 py-3 text-sm font-medium text-brand-600 hover:bg-brand-50"
            >
              For institutions →
            </Link>
          </div>
        </div>

        {/* Public stats — only show counters that reflect ground truth. */}
        <dl className="mt-16 grid grid-cols-2 gap-4 sm:grid-cols-2">
          <Stat value={stats.questions} label="questions in the bank" />
          <Stat value={stats.contributors} label="contributors" />
        </dl>
      </section>

      {/* Pilot context — honest, no aspirational scaling claims. */}
      {active.length > 0 && (
        <section className="border-y border-ink-200 bg-ink-50">
          <div className="mx-auto max-w-5xl px-6 py-12">
            <h2 className="display text-2xl font-semibold">
              Pilot launching at IIT-AD next semester.
            </h2>
            <ul className="mt-5 grid gap-2 sm:grid-cols-2">
              {active.map((i) => (
                <InstitutionCard key={i.slug} i={i} />
              ))}
            </ul>
          </div>
        </section>
      )}

      {/* Two surfaces. Anything not actually built is dropped. */}
      <section className="mx-auto max-w-5xl px-6 py-20">
        <h2 className="display text-3xl font-semibold">
          One bank. Two surfaces.
        </h2>
        <div className="mt-10 grid gap-8 sm:grid-cols-2">
          <Pillar
            title="For students"
            subtitle="Practice"
            body="LaTeX rendered in the browser. Filter by subtopic. Diverse generation via DPP. Per-subtopic Bayesian mastery so you actually know where you're weak."
            href="/practice"
            cta="Start practicing"
          />
          <Pillar
            title="For TAs"
            subtitle="Authoring"
            body="One form to add a question with live LaTeX preview. Auto-embedded via Gemini, indexed for similarity search the moment you submit."
            href="/author"
            cta="Contribute a question"
          />
        </div>
      </section>

      {/* How Diverse mode works — visual primer */}
      <section className="mx-auto max-w-5xl px-6 py-20">
        <h2 className="display text-3xl font-semibold">
          Random vs Diverse — what changes.
        </h2>
        <p className="mt-3 max-w-2xl text-ink-500">
          Every question gets a vector embedding. Naive selection clusters by
          accident. Diverse mode uses a determinantal point process to pick a
          set that maximally covers the concept space — so a 10-question
          practice set actually spans your topic instead of repeating the
          same skill ten times.
        </p>

        <div className="mt-10 grid gap-6 sm:grid-cols-2">
          {/* Random — clumped */}
          <div className="rounded-lg border border-ink-200 bg-white p-6">
            <div className="mb-3 flex items-baseline justify-between">
              <span className="text-sm font-semibold">Random</span>
              <span className="text-xs text-ink-500 tabular-nums">
                diversity 0.41
              </span>
            </div>
            <svg viewBox="0 0 200 140" className="w-full">
              <rect width="200" height="140" fill="transparent" stroke="currentColor" strokeOpacity="0.1" />
              {/* Concept-space dots, mostly clustered */}
              {[
                [55, 60], [62, 65], [58, 72], [50, 58], [65, 70],
                [60, 55], [70, 75], [54, 80], [115, 40], [140, 100],
              ].map(([x, y], i) => (
                <circle key={i} cx={x} cy={y} r="4" fill="var(--primary, #4759f5)" opacity="0.85" />
              ))}
            </svg>
            <p className="mt-3 text-xs text-ink-500">
              10 questions picked uniformly. Most land in one tight neighbourhood — you drill the same skill ten times.
            </p>
          </div>

          {/* Diverse — spread */}
          <div className="rounded-lg border border-ink-200 bg-white p-6">
            <div className="mb-3 flex items-baseline justify-between">
              <span className="text-sm font-semibold">Diverse (DPP)</span>
              <span className="text-xs text-emerald-700 tabular-nums">
                diversity 0.87
              </span>
            </div>
            <svg viewBox="0 0 200 140" className="w-full">
              <rect width="200" height="140" fill="transparent" stroke="currentColor" strokeOpacity="0.1" />
              {[
                [30, 30], [170, 25], [40, 110], [165, 115], [100, 70],
                [60, 70], [140, 60], [110, 30], [95, 115], [35, 75],
              ].map(([x, y], i) => (
                <circle key={i} cx={x} cy={y} r="4" fill="var(--success, #16a34a)" opacity="0.85" />
              ))}
            </svg>
            <p className="mt-3 text-xs text-ink-500">
              Same 10, picked by a determinantal point process. Every region of the topic gets one — broad coverage, no redundancy.
            </p>
          </div>
        </div>
      </section>

      {/* Why this exists. */}
      <section className="border-t border-ink-200 bg-ink-50">
        <div className="mx-auto max-w-5xl px-6 py-20">
          <h2 className="display text-3xl font-semibold">
            Why this exists.
          </h2>
          <p className="mt-6 max-w-2xl text-ink-700">
            Every STEM student practices typeset problems. Every TA writes them.
            Nobody has a shared home for the result. The systems that exist —{" "}
            <em>WebAssign, Pearson MyLab, ALEKS</em> — are paywalled and locked
            to whichever textbook the publisher sells. Amplify is the
            alternative built from the inside of an actual institution.
          </p>
        </div>
      </section>

      <footer className="border-t border-ink-200">
        <div className="mx-auto max-w-5xl px-6 py-10 text-xs text-ink-500">
          Built at IIT-Delhi Abu Dhabi by Karth Puthiyedathu and Joel Jobi.
        </div>
      </footer>
    </main>
  );
}

function Stat({ value, label }: { value: number; label: string }) {
  return (
    <div className="rounded-lg border border-ink-200 bg-white px-4 py-4">
      <dt className="text-3xl font-semibold tracking-tight">
        {value.toLocaleString()}
      </dt>
      <dd className="mt-0.5 text-xs uppercase tracking-wide text-ink-500">
        {label}
      </dd>
    </div>
  );
}

function InstitutionCard({ i }: { i: Institution }) {
  return (
    <li>
      <Link
        href={`/i/${i.slug}`}
        className="flex items-center justify-between rounded-md border border-ink-200 bg-white px-3 py-2.5 text-sm shadow-sm hover:border-ink-400"
      >
        <div>
          <div className="font-medium">{i.short_name}</div>
          <div className="text-xs text-ink-500">{i.name}</div>
        </div>
        <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2 py-0.5 text-xs font-medium text-emerald-700">
          <span className="size-1.5 rounded-full bg-emerald-500" />
          live
        </span>
      </Link>
    </li>
  );
}

function Pillar({
  title,
  subtitle,
  body,
  href,
  cta,
}: {
  title: string;
  subtitle: string;
  body: string;
  href: string;
  cta: string;
}) {
  return (
    <div className="flex flex-col gap-3">
      <div>
        <div className="text-xs font-medium uppercase tracking-wider text-brand-600">
          {subtitle}
        </div>
        <div className="mt-1 text-lg font-semibold">{title}</div>
      </div>
      <p className="text-sm text-ink-500">{body}</p>
      <Link
        href={href}
        className="self-start text-sm font-medium text-ink-900 underline-offset-4 hover:underline"
      >
        {cta} →
      </Link>
    </div>
  );
}
