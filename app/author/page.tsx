import { redirect } from "next/navigation";
import Link from "next/link";
import { getServerSupabase } from "@/lib/supabase/server";
import { getAdminSupabase } from "@/lib/supabase/admin";
import { getPracticeTaxonomy } from "@/lib/cached";
import { AuthorForm } from "./form";
import { ResolveButton } from "./resolve-button";

type ReportRow = {
  id: string;
  question_id: number;
  reason: string | null;
  created_at: string;
  resolved_at: string | null;
  questions: { topic: string; subtopic: string; latexcode: string; submitted_by: string | null } | null;
};

type PublishedRow = {
  id: number;
  topic: string;
  branch: string;
  subtopic: string;
  latexcode: string;
  flagged_count: number;
  created_at: string;
};

export default async function AuthorPage() {
  const supabase = await getServerSupabase();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) redirect("/auth/login?next=/author");

  const { data: profile } = await supabase
    .from("user_profiles")
    .select("role, institution_id, institution:institutions(*)")
    .eq("user_id", user.id)
    .maybeSingle();

  const role = (profile as { role?: string } | null)?.role;
  if (role !== "faculty" && role !== "admin" && role !== "moderator") {
    return (
      <main className="mx-auto max-w-2xl px-6 py-16">
        <h1 className="display text-3xl font-semibold">Authoring is TA-gated</h1>
        <p className="mt-3 text-ink-700">
          You&apos;re signed in as a student. To contribute questions, sign up
          again with the <strong>TA</strong> role selected.
        </p>
        <div className="mt-8 flex gap-3">
          <Link
            href="/practice"
            className="rounded-md bg-ink-900 px-4 py-2 text-sm font-medium text-white hover:bg-ink-700"
          >
            Practice instead
          </Link>
          <Link
            href="/auth/signout"
            className="rounded-md border border-ink-200 px-4 py-2 text-sm font-medium hover:bg-ink-50"
          >
            Sign out
          </Link>
        </div>
      </main>
    );
  }

  // Load courses for the institution scope dropdown.
  const institutionId = (
    profile as { institution_id?: number | null } | null
  )?.institution_id;
  const { data: courses } = await supabase
    .from("courses")
    .select("id, code, name, slug")
    .eq("institution_id", institutionId ?? -1)
    .order("code");

  // Questions this TA has published.
  const admin = getAdminSupabase();
  const { data: pubRows } = await admin
    .from("questions")
    .select("id, topic, branch, subtopic, latexcode, flagged_count, created_at")
    .eq("submitted_by", user.email ?? "")
    .order("id", { ascending: false })
    .limit(20);
  const published = (pubRows ?? []) as PublishedRow[];

  // Flags scoped to this TA's questions only (unless admin/moderator).
  const isElevated = role === "admin" || role === "moderator";
  let reportsQuery = admin
    .from("question_reports")
    .select(
      "id, question_id, reason, created_at, resolved_at, questions!inner(topic, subtopic, latexcode, submitted_by)"
    )
    .is("resolved_at", null)
    .order("created_at", { ascending: false })
    .limit(10);
  if (!isElevated) {
    reportsQuery = reportsQuery.eq("questions.submitted_by", user.email ?? "");
  }
  const { data: reportRows } = await reportsQuery;
  const reports = (reportRows ?? []) as unknown as ReportRow[];

  // Existing taxonomy so the TA can pick from the current list or add their own.
  const { tree } = await getPracticeTaxonomy();
  const knownTopics = Object.keys(tree).sort();
  const knownBranches = [
    ...new Set(
      Object.values(tree).flatMap((branches) => Object.keys(branches))
    ),
  ].sort();
  const knownSubtopics = [
    ...new Set(
      Object.values(tree).flatMap((branches) =>
        Object.values(branches).flat()
      )
    ),
  ].sort();

  return (
    <main className="hero-bg">
      <section className="mx-auto max-w-5xl px-6 py-12">
        <div className="mb-8 flex items-baseline justify-between">
          <div>
            <div className="text-sm font-mono uppercase tracking-wider text-brand-600">
              author a question
            </div>
            <h1 className="display mt-1 text-3xl font-semibold">
              Add to the commons
            </h1>
            <p className="mt-2 text-sm text-ink-500">
              Goes live the moment you submit. Embedded, indexed, and searchable,
              with full attribution to you.
            </p>
          </div>
        </div>

        <AuthorForm
          courses={(courses ?? []).map((c) => ({
            id: c.id as number,
            code: c.code as string,
            name: c.name as string,
            slug: c.slug as string,
          }))}
          knownTopics={knownTopics}
          knownBranches={knownBranches}
          knownSubtopics={knownSubtopics}
        />

        {/* Published by this TA. */}
        <div className="mt-16">
          <div className="mb-4 flex items-baseline justify-between">
            <h2 className="text-xl font-semibold">Published by you</h2>
            <span className="text-xs text-ink-500">
              {published.length} question{published.length === 1 ? "" : "s"}
            </span>
          </div>
          {published.length === 0 ? (
            <p className="rounded-md border border-ink-200 bg-ink-50 p-4 text-sm text-ink-500">
              You haven&apos;t submitted any questions yet.
            </p>
          ) : (
            <ul className="flex flex-col gap-2">
              {published.map((p) => (
                <li
                  key={p.id}
                  className="rounded-md border border-ink-200 bg-white p-3 text-sm"
                >
                  <div className="flex items-baseline justify-between gap-3">
                    <Link
                      href={`/q/${p.id}`}
                      className="font-medium underline"
                    >
                      Q#{p.id}
                    </Link>
                    <div className="flex items-center gap-2 text-xs text-ink-500">
                      {p.flagged_count > 0 && (
                        <span className="rounded-full bg-red-50 px-2 py-0.5 text-red-700">
                          {p.flagged_count} flag{p.flagged_count === 1 ? "" : "s"}
                        </span>
                      )}
                      <span>{new Date(p.created_at).toLocaleDateString()}</span>
                      <Link
                        href={`/author/edit/${p.id}`}
                        className="rounded-md border border-ink-200 px-2 py-0.5 hover:bg-ink-50"
                      >
                        Edit
                      </Link>
                    </div>
                  </div>
                  <div className="mt-1 text-xs text-ink-500">
                    {p.topic} › {p.branch} › {p.subtopic}
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>

        {/* Open flags on this TA's questions. */}
        <div className="mt-12">
          <div className="mb-4 flex items-baseline justify-between">
            <h2 className="text-xl font-semibold">
              Open flags{isElevated ? " (all)" : " on your questions"}
            </h2>
            <span className="text-xs text-ink-500">{reports.length} pending</span>
          </div>
          {reports.length === 0 ? (
            <p className="rounded-md border border-ink-200 bg-ink-50 p-4 text-sm text-ink-500">
              No open flags. Students can report questions from the question page.
            </p>
          ) : (
            <ul className="flex flex-col gap-2">
              {reports.map((r) => (
                <li
                  key={r.id}
                  className="rounded-md border border-ink-200 bg-white p-3 text-sm"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0 flex-1">
                      <div className="flex items-baseline gap-2">
                        <Link
                          href={`/q/${r.question_id}`}
                          className="font-medium underline"
                        >
                          Q#{r.question_id}
                        </Link>
                        <span className="text-xs text-ink-500">
                          {new Date(r.created_at).toLocaleString()}
                        </span>
                      </div>
                      {r.questions && (
                        <div className="mt-1 text-xs text-ink-500">
                          {r.questions.topic} › {r.questions.subtopic}
                        </div>
                      )}
                      {r.reason && (
                        <p className="mt-2 rounded bg-ink-50 px-2 py-1 text-xs text-ink-700">
                          {r.reason}
                        </p>
                      )}
                    </div>
                    <ResolveButton reportId={r.id} />
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
      </section>
    </main>
  );
}
