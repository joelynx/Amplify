import { notFound } from "next/navigation";
import Link from "next/link";
import { getServerSupabase } from "@/lib/supabase/server";
import type { Institution, Course } from "@/lib/db/types";

type Props = { params: Promise<{ slug: string; course: string }> };

export default async function CoursePage({ params }: Props) {
  const { slug, course: courseSlug } = await params;

  const supabase = await getServerSupabase();
  const { data: inst } = await supabase
    .from("institutions")
    .select("*")
    .eq("slug", slug)
    .maybeSingle();
  if (!inst) notFound();

  const { data: course } = await supabase
    .from("courses")
    .select("*")
    .eq("institution_id", (inst as Institution).id)
    .eq("slug", courseSlug)
    .maybeSingle();
  if (!course) notFound();

  // Questions in this course — get IDs first, then sample taxonomy.
  const { data: cqRows, count: courseQCount } = await supabase
    .from("course_questions")
    .select("question_id", { count: "exact" })
    .eq("course_id", (course as Course).id);
  const qIds = (cqRows ?? []).map((r) => r.question_id as number);

  let topics: string[] = [];
  let typeCounts: Record<string, number> = {};
  if (qIds.length > 0) {
    const { data: qs } = await supabase
      .from("questions")
      .select("topic, branch, subtopic, type")
      .in("id", qIds.slice(0, 1000));
    const topicSet = new Set<string>();
    for (const q of qs ?? []) {
      topicSet.add(`${q.topic} › ${q.branch}`);
      typeCounts[q.type as string] = (typeCounts[q.type as string] ?? 0) + 1;
    }
    topics = [...topicSet].sort().slice(0, 12);
  }

  const c = course as Course;
  const i = inst as Institution;

  return (
    <main className="hero-bg">
      <section className="mx-auto max-w-4xl px-6 py-16">
        {/* Breadcrumb */}
        <div className="flex flex-wrap items-center gap-2 text-sm text-ink-500">
          <Link href="/" className="hover:text-ink-900">
            Amplify
          </Link>
          <span>›</span>
          <Link href={`/i/${i.slug}`} className="hover:text-ink-900">
            {i.short_name}
          </Link>
          <span>›</span>
          <span>{c.code}</span>
        </div>

        {/* Header */}
        <div className="mt-4 flex flex-col gap-4">
          <div className="font-mono text-xs uppercase tracking-wider text-brand-600">
            {c.code}
          </div>
          <h1 className="display text-4xl font-semibold sm:text-5xl">
            {c.name}
          </h1>
          {c.description && (
            <p className="max-w-2xl text-lg text-ink-500">{c.description}</p>
          )}

          <div className="flex flex-wrap gap-3">
            <Link
              href={`/practice?course=${c.slug}`}
              className="rounded-md bg-ink-900 px-5 py-2.5 text-sm font-medium text-white hover:bg-ink-700"
            >
              Practice {c.code} →
            </Link>
            <Link
              href={`/q?topic=${encodeURIComponent(topics[0]?.split(" › ")[0] ?? "")}`}
              className="rounded-md border border-ink-200 px-5 py-2.5 text-sm font-medium hover:bg-ink-50"
            >
              Browse questions
            </Link>
          </div>
        </div>

        {/* Course stats */}
        <dl className="mt-12 grid grid-cols-3 gap-3">
          <Stat value={courseQCount ?? 0} label="questions" />
          <Stat
            value={typeCounts["numerical"] ?? 0}
            label="numerical"
          />
          <Stat
            value={(typeCounts["proof"] ?? 0) + (typeCounts["explanation/reasoning"] ?? 0)}
            label="proofs & reasoning"
          />
        </dl>

        {/* Topics covered */}
        {topics.length > 0 && (
          <section className="mt-16">
            <h2 className="text-sm font-medium uppercase tracking-wider text-ink-500">
              What this course covers
            </h2>
            <ul className="mt-4 flex flex-wrap gap-2">
              {topics.map((t) => (
                <li
                  key={t}
                  className="rounded-full border border-ink-200 bg-white px-3 py-1 text-sm"
                >
                  {t}
                </li>
              ))}
            </ul>
          </section>
        )}

        {/* Empty state */}
        {(courseQCount ?? 0) === 0 && (
          <div className="mt-12 rounded-md border border-dashed border-ink-200 p-6 text-sm text-ink-500">
            No questions in this course yet. Faculty: contribute the first one
            from{" "}
            <Link href="/author" className="underline">
              /author
            </Link>
            .
          </div>
        )}
      </section>
    </main>
  );
}

function Stat({ value, label }: { value: number; label: string }) {
  return (
    <div className="rounded-md border border-ink-200 bg-white px-4 py-3">
      <dt className="text-2xl font-semibold tracking-tight">
        {value.toLocaleString()}
      </dt>
      <dd className="text-xs uppercase tracking-wider text-ink-500">
        {label}
      </dd>
    </div>
  );
}
