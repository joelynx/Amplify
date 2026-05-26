import { notFound } from "next/navigation";
import Link from "next/link";
import { getServerSupabase } from "@/lib/supabase/server";
import { LatexBlock } from "@/components/latex-block";
import { SolutionToggle } from "./solution-toggle";
import type { Question } from "@/lib/db/types";

type SimilarRow = {
  id: number;
  topic: string;
  branch: string;
  subtopic: string;
  latexcode: string;
  type: string;
  similarity: number;
};

type Props = { params: Promise<{ id: string }> };

export default async function QuestionPage({ params }: Props) {
  const { id } = await params;
  const numericId = Number.parseInt(id, 10);
  if (!Number.isFinite(numericId)) notFound();

  const supabase = await getServerSupabase();
  const { data, error } = await supabase
    .from("questions")
    .select("*")
    .eq("id", numericId)
    .maybeSingle();

  if (error || !data) notFound();
  const q = data as Question;

  const { data: tagRows } = await supabase
    .from("question_tags")
    .select("tag")
    .eq("question_id", numericId);
  const tags = (tagRows ?? []).map((r) => r.tag as string);

  // Cosine-KNN similar questions via pgvector. Returns [] if this question has
  // no embedding yet (graceful — section just doesn't render).
  const { data: similarRows } = await supabase.rpc("match_questions", {
    source_id: numericId,
    match_count: 6,
  });
  const similar = (similarRows ?? []) as SimilarRow[];

  return (
    <main className="mx-auto max-w-3xl px-6 py-10">
      <Link
        href="/practice"
        className="mb-6 inline-block text-sm text-ink-500 hover:text-ink-900"
      >
        ← back to practice
      </Link>

      <div className="mb-4 flex flex-wrap items-center gap-2 text-xs">
        <span className="rounded-full bg-ink-100 px-2 py-1 text-ink-700">
          {q.topic}
        </span>
        <span className="text-ink-400">›</span>
        <span className="text-ink-500">{q.branch}</span>
        <span className="text-ink-400">›</span>
        <span className="text-ink-500">{q.subtopic}</span>
      </div>

      <article className="prose prose-ink max-w-none">
        <LatexBlock src={q.latexcode} className="text-lg leading-relaxed" />
      </article>

      <div className="mt-6 flex flex-wrap gap-2 text-xs">
        <span className="rounded border border-ink-200 px-2 py-1 text-ink-600">
          {q.type}
        </span>
        {q.source && (
          <span className="rounded border border-ink-200 px-2 py-1 text-ink-600">
            {q.source}
            {q.subsource ? ` · ${q.subsource}` : ""}
          </span>
        )}
        {q.difficulty_rating > 0 && (
          <span className="rounded border border-ink-200 px-2 py-1 text-ink-600">
            difficulty {q.difficulty_rating.toFixed(1)}
          </span>
        )}
        {tags.map((t) => (
          <span
            key={t}
            className="rounded-full bg-ink-50 px-2 py-1 text-ink-600"
          >
            #{t}
          </span>
        ))}
      </div>

      {q.solution && (
        <SolutionToggle solution={q.solution} answer={q.answer ?? undefined} />
      )}

      {similar.length > 0 && (
        <section className="mt-12 border-t border-ink-200 pt-8">
          <div className="mb-4 flex items-baseline justify-between">
            <h2 className="text-sm font-medium uppercase tracking-wider text-ink-500">
              Similar questions
            </h2>
            <span className="text-xs text-ink-400">
              cosine-KNN over gemini-embedding-001 vectors
            </span>
          </div>
          <ul className="space-y-2">
            {similar.map((s) => (
              <li key={s.id}>
                <Link
                  href={`/q/${s.id}`}
                  className="block rounded-md border border-ink-200 px-3 py-3 transition hover:border-ink-400"
                >
                  <div className="mb-1 flex items-center justify-between text-xs">
                    <span className="text-ink-500">
                      {s.subtopic}
                      <span className="text-ink-400"> · {s.type}</span>
                    </span>
                    <span className="rounded-full bg-brand-50 px-2 py-0.5 font-medium text-brand-700">
                      {Math.round(s.similarity * 100)}% similar
                    </span>
                  </div>
                  <div className="line-clamp-2 text-sm text-ink-900">
                    <LatexBlock src={s.latexcode} />
                  </div>
                </Link>
              </li>
            ))}
          </ul>
        </section>
      )}
    </main>
  );
}
