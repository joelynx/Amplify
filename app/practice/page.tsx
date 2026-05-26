import { getServerSupabase } from "@/lib/supabase/server";
import { PracticeFilterForm } from "./filter-form";

export default async function PracticePage() {
  const supabase = await getServerSupabase();

  // Distinct topic/branch/subtopic for the tree, plus types & sources & tags.
  const [
    { data: taxonomyRows },
    { data: typeRows },
    { data: sourceRows },
    { data: tagRows },
  ] = await Promise.all([
    supabase
      .from("questions")
      .select("topic, branch, subtopic")
      .order("topic"),
    supabase.from("questions").select("type"),
    supabase.from("questions").select("source"),
    supabase.from("question_tags").select("tag"),
  ]);

  const tree: Record<string, Record<string, Set<string>>> = {};
  for (const row of taxonomyRows ?? []) {
    const { topic, branch, subtopic } = row as {
      topic: string;
      branch: string;
      subtopic: string;
    };
    if (!tree[topic]) tree[topic] = {};
    if (!tree[topic][branch]) tree[topic][branch] = new Set();
    tree[topic][branch].add(subtopic);
  }

  // Serialise sets → arrays for the client.
  const treeData = Object.fromEntries(
    Object.entries(tree).map(([t, branches]) => [
      t,
      Object.fromEntries(
        Object.entries(branches).map(([b, subs]) => [b, [...subs].sort()])
      ),
    ])
  );

  const types = [...new Set((typeRows ?? []).map((r) => r.type as string))];
  const sources = [
    ...new Set(
      (sourceRows ?? [])
        .map((r) => r.source as string | null)
        .filter((s): s is string => !!s)
    ),
  ].sort();
  const tags = [
    ...new Set((tagRows ?? []).map((r) => r.tag as string)),
  ].sort();

  return (
    <main className="mx-auto max-w-3xl px-6 py-10">
      <h1 className="mb-2 text-3xl font-semibold tracking-tight">Practice</h1>
      <p className="mb-8 text-sm text-ink-500">
        Pick what you want to work on. We&apos;ll serve you a session you can
        grind through with instant feedback.
      </p>

      <PracticeFilterForm
        tree={treeData}
        types={types}
        sources={sources}
        tags={tags}
      />
    </main>
  );
}
