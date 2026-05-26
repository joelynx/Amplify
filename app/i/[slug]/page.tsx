import { notFound } from "next/navigation";
import Link from "next/link";
import { getServerSupabase } from "@/lib/supabase/server";
import type { Institution, Course } from "@/lib/db/types";

type Props = { params: Promise<{ slug: string }> };

export default async function InstitutionPage({ params }: Props) {
  const { slug } = await params;

  const supabase = await getServerSupabase();
  const { data: institution } = await supabase
    .from("institutions")
    .select("*")
    .eq("slug", slug)
    .maybeSingle();

  if (!institution) notFound();
  const inst = institution as Institution;

  const [{ data: courses }, { count: questionCount }] = await Promise.all([
    supabase
      .from("courses")
      .select("*")
      .eq("institution_id", inst.id)
      .order("code"),
    supabase
      .from("course_questions")
      .select("question_id", { count: "exact", head: true })
      .in(
        "course_id",
        (
          await supabase
            .from("courses")
            .select("id")
            .eq("institution_id", inst.id)
        ).data?.map((c) => c.id) ?? [0]
      ),
  ]);

  const isActive = inst.status === "active";

  return (
    <main className="hero-bg">
      <section className="mx-auto max-w-4xl px-6 py-16">
        {/* Institution header */}
        <div className="flex flex-col gap-4">
          <div className="flex items-center gap-3 text-sm text-ink-500">
            <Link href="/" className="hover:text-ink-900">
              Amplify
            </Link>
            <span>›</span>
            <span>{inst.short_name}</span>
          </div>

          <div className="flex items-start justify-between gap-6">
            <div>
              <div className="text-sm font-mono uppercase tracking-wider text-ink-500">
                {inst.short_name}
              </div>
              <h1 className="display mt-1 text-4xl font-semibold sm:text-5xl">
                {inst.name}
              </h1>
              {inst.description && (
                <p className="mt-4 max-w-2xl text-ink-700">
                  {inst.description}
                </p>
              )}
            </div>
            <span
              className={
                "inline-flex shrink-0 items-center gap-1.5 rounded-full px-3 py-1 text-xs font-medium " +
                (isActive
                  ? "bg-emerald-50 text-emerald-700"
                  : "bg-ink-100 text-ink-700")
              }
            >
              <span
                className={
                  "size-1.5 rounded-full " +
                  (isActive ? "bg-emerald-500" : "bg-ink-400")
                }
              />
              {isActive ? "live since " + new Date(inst.joined_at).toLocaleDateString("en-US", { year: "numeric", month: "short" }) : "interested · not yet live"}
            </span>
          </div>

          {/* Stats */}
          <dl className="mt-8 grid grid-cols-3 gap-3">
            <Stat value={(courses ?? []).length} label="courses" />
            <Stat value={questionCount ?? 0} label="questions" />
            <Stat value={inst.country === "AE" ? "Abu Dhabi" : inst.country} label="campus" />
          </dl>
        </div>

        {/* Courses */}
        {isActive && (
          <section className="mt-16">
            <h2 className="display text-2xl font-semibold">Courses</h2>
            {(courses ?? []).length === 0 ? (
              <p className="mt-4 rounded-md border border-dashed border-ink-200 p-6 text-sm text-ink-500">
                No courses yet. Faculty: add the first course from{" "}
                <Link href="/author" className="underline">
                  /author
                </Link>
                .
              </p>
            ) : (
              <ul className="mt-6 grid gap-3 sm:grid-cols-2">
                {(courses as Course[]).map((c) => (
                  <li key={c.id}>
                    <Link
                      href={`/i/${inst.slug}/c/${c.slug}`}
                      className="block rounded-lg border border-ink-200 bg-white p-5 shadow-sm hover:border-ink-400"
                    >
                      <div className="flex items-baseline justify-between">
                        <span className="font-mono text-xs font-medium uppercase tracking-wider text-brand-600">
                          {c.code}
                        </span>
                      </div>
                      <div className="mt-1.5 text-lg font-semibold">
                        {c.name}
                      </div>
                      {c.description && (
                        <p className="mt-2 text-sm text-ink-500">
                          {c.description}
                        </p>
                      )}
                    </Link>
                  </li>
                ))}
              </ul>
            )}
          </section>
        )}

        {/* Inactive CTA */}
        {!isActive && (
          <section className="mt-16 rounded-lg border border-ink-200 bg-ink-50 p-8">
            <h2 className="display text-2xl font-semibold">
              We&apos;re not at {inst.short_name} yet.
            </h2>
            <p className="mt-3 text-ink-700">
              Are you faculty or a student at {inst.short_name}? We&apos;d love
              to start a conversation. Pilot programs are free for the first
              two semesters.
            </p>
            <a
              href={`mailto:24a1cseb0015@iitdabudhabi.ac.ae?subject=Amplify%20at%20${encodeURIComponent(inst.short_name)}`}
              className="mt-6 inline-block rounded-md bg-ink-900 px-5 py-2.5 text-sm font-medium text-white hover:bg-ink-700"
            >
              Bring Amplify to {inst.short_name}
            </a>
          </section>
        )}
      </section>
    </main>
  );
}

function Stat({ value, label }: { value: string | number; label: string }) {
  return (
    <div className="rounded-md border border-ink-200 bg-white px-4 py-3">
      <dt className="text-2xl font-semibold tracking-tight">
        {typeof value === "number" ? value.toLocaleString() : value}
      </dt>
      <dd className="text-xs uppercase tracking-wider text-ink-500">
        {label}
      </dd>
    </div>
  );
}
