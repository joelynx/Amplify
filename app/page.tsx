import Link from "next/link";
import { getServerSupabase } from "@/lib/supabase/server";
import { getPublicStats } from "@/lib/stats";
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

  const [
    stats,
    { data: institutions },
    {
      data: { user },
    },
  ] = await Promise.all([
    getPublicStats(supabase),
    supabase
      .from("institutions")
      .select("*")
      .order("status", { ascending: true })
      .order("short_name"),
    supabase.auth.getUser(),
  ]);

  // For logged-in users, surface their three weakest subtopics for instant CTA.
  let weakest: MasteryRow[] = [];
  if (user) {
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

  const active = (institutions ?? []).filter(
    (i) => (i as Institution).status === "active"
  ) as Institution[];
  const interested = (institutions ?? []).filter(
    (i) => (i as Institution).status === "interested"
  ) as Institution[];

  return (
    <main className="hero-bg">
      {/* Personalised dashboard strip — only for signed-in users with mastery data */}
      {user && (
        <section className="border-b border-ink-200 bg-brand-50/60">
          <div className="mx-auto max-w-5xl px-6 py-6">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div className="min-w-0">
                <div className="text-xs uppercase tracking-wider text-brand-700">
                  Welcome back, {user.email?.split("@")[0]}
                </div>
                {weakest.length > 0 ? (
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
            A peer-reviewed, open bank of university math, physics, and CS
            problems. Mastery-tracked practice for students. Overleaf-grade
            authoring for professors. Assessment infrastructure for
            institutions. Free for individuals, forever.
          </p>

          <div className="flex flex-wrap gap-3">
            <Link
              href="/practice"
              className="rounded-md bg-ink-900 px-5 py-3 text-sm font-medium text-white shadow-sm hover:bg-ink-700"
            >
              Start practicing →
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

        {/* Public stats */}
        <dl className="mt-16 grid grid-cols-2 gap-4 sm:grid-cols-4">
          <Stat value={stats.questions} label="curated questions" />
          <Stat value={stats.institutions} label="active institutions" />
          <Stat value={stats.contributors} label="faculty contributors" />
          <Stat value={stats.sessionsThisWeek} label="sessions this week" />
        </dl>
      </section>

      {/* Universities — the IIT system → global story */}
      <section className="border-y border-ink-200 bg-ink-50">
        <div className="mx-auto max-w-5xl px-6 py-16">
          <h2 className="display text-3xl font-semibold">
            Live at IIT-AD. Scaling to every IIT. Then everywhere.
          </h2>
          <p className="mt-3 max-w-2xl text-ink-500">
            The IIT system is 23 campuses and 16,000 STEM students per year.
            Amplify started at the Abu Dhabi campus. We&apos;re working with
            faculty to expand across the system, then to engineering colleges
            across India, then globally.
          </p>

          <div className="mt-10 grid gap-4 sm:grid-cols-2">
            <div>
              <h3 className="mb-3 text-xs font-medium uppercase tracking-wider text-emerald-700">
                Live now
              </h3>
              <ul className="space-y-2">
                {active.map((i) => (
                  <InstitutionCard key={i.slug} i={i} />
                ))}
              </ul>
            </div>
            <div>
              <h3 className="mb-3 text-xs font-medium uppercase tracking-wider text-ink-500">
                Coming next — IIT campuses we&apos;re talking to
              </h3>
              <ul className="space-y-2">
                {interested.slice(0, 9).map((i) => (
                  <li
                    key={i.slug}
                    className="flex items-center justify-between rounded-md border border-dashed border-ink-200 bg-white/60 px-3 py-2 text-sm"
                  >
                    <span>{i.name}</span>
                    <span className="text-xs text-ink-400">{i.short_name}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* Three pillars */}
      <section className="mx-auto max-w-5xl px-6 py-20">
        <h2 className="display text-3xl font-semibold">
          One commons. Three surfaces.
        </h2>
        <div className="mt-10 grid gap-8 sm:grid-cols-3">
          <Pillar
            title="For students"
            subtitle="Practice"
            body="Browse-friendly LaTeX in the browser. Filter by subtopic. Grade yourself. Watch your mastery score climb. No PDFs, no installs."
            href="/practice"
            cta="Start practicing"
          />
          <Pillar
            title="For professors"
            subtitle="Authoring"
            body="Write questions in LaTeX with live KaTeX preview. Peer-review queue. Revision history. Your contributions live in the commons under your name."
            href="/author"
            cta="Contribute a question"
          />
          <Pillar
            title="For institutions"
            subtitle="Adopt"
            body="Get a branded problem-bank for your university. Faculty dashboards. Cohort mastery analytics. SSO, LMS integration, exams — coming."
            href="/for-institutions"
            cta="Bring Amplify to your campus"
          />
        </div>
      </section>

      {/* Why now */}
      <section className="border-t border-ink-200 bg-ink-50">
        <div className="mx-auto max-w-5xl px-6 py-20">
          <h2 className="display text-3xl font-semibold">
            Why this didn&apos;t exist already.
          </h2>
          <div className="mt-8 grid gap-8 sm:grid-cols-2">
            <p className="text-ink-700">
              Every STEM student practices typeset problems. Every STEM
              professor sets typeset problem sets. None of it has a canonical
              home. The systems that exist —{" "}
              <em>WebAssign, Pearson MyLab, ALEKS</em> — are paywalled, hated by
              students, and locked to whichever textbook the publisher sells.
            </p>
            <p className="text-ink-700">
              We&apos;re building the alternative: an open commons of
              peer-reviewed problems, with practice and assessment apps on top.
              Universities pay; students and professors don&apos;t. Funded by
              institutional licenses, governed by faculty contributors.
            </p>
          </div>
        </div>
      </section>

      <footer className="border-t border-ink-200">
        <div className="mx-auto max-w-5xl px-6 py-10 text-xs text-ink-500">
          Built at IIT-Delhi Abu Dhabi · MIT licensed · open source on{" "}
          <a
            href="https://github.com/joelynx/Amplify"
            className="underline hover:text-ink-900"
          >
            GitHub
          </a>
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
