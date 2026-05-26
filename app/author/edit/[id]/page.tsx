import { notFound, redirect } from "next/navigation";
import Link from "next/link";
import { getServerSupabase } from "@/lib/supabase/server";
import { getAdminSupabase } from "@/lib/supabase/admin";
import { EditForm } from "./edit-form";

type Params = { params: Promise<{ id: string }> };

export default async function EditPage({ params }: Params) {
  const { id } = await params;
  const questionId = Number.parseInt(id, 10);
  if (!Number.isFinite(questionId)) notFound();

  const supabase = await getServerSupabase();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) redirect(`/auth/login?next=/author/edit/${questionId}`);

  const { data: profile } = await supabase
    .from("user_profiles")
    .select("role")
    .eq("user_id", user.id)
    .maybeSingle();
  const role = (profile as { role?: string } | null)?.role;
  if (role !== "faculty" && role !== "admin" && role !== "moderator") {
    redirect("/author");
  }

  const admin = getAdminSupabase();
  const { data: q } = await admin
    .from("questions")
    .select(
      "id, topic, branch, subtopic, latexcode, type, source, answer, solution, submitted_by"
    )
    .eq("id", questionId)
    .maybeSingle();
  if (!q) notFound();

  const isElevated = role === "admin" || role === "moderator";
  const owner = (q as { submitted_by: string | null }).submitted_by;
  if (!isElevated && owner !== user.email) {
    return (
      <main className="mx-auto max-w-2xl px-6 py-16">
        <h1 className="display text-3xl font-semibold">Not your question</h1>
        <p className="mt-3 text-ink-700">
          You can only edit questions you submitted. Q#{questionId} was
          submitted by {owner ?? "someone else"}.
        </p>
        <Link
          href="/author"
          className="mt-6 inline-block rounded-md bg-ink-900 px-4 py-2 text-sm font-medium text-white hover:bg-ink-700"
        >
          Back to /author
        </Link>
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-5xl px-6 py-12">
      <div className="mb-8">
        <Link href="/author" className="text-xs text-ink-500 underline">
          ← Back
        </Link>
        <h1 className="display mt-1 text-3xl font-semibold">
          Edit Q#{questionId}
        </h1>
      </div>
      <EditForm
        questionId={questionId}
        initial={{
          topic: (q as { topic: string }).topic,
          branch: (q as { branch: string }).branch,
          subtopic: (q as { subtopic: string }).subtopic,
          type: (q as { type: string }).type,
          latexcode: (q as { latexcode: string }).latexcode,
          answer: (q as { answer: string | null }).answer ?? "",
          solution: (q as { solution: string | null }).solution ?? "",
          source: (q as { source: string | null }).source ?? "",
        }}
      />
    </main>
  );
}
