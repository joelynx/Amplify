import { notFound } from "next/navigation";
import { getServerSupabase } from "@/lib/supabase/server";
import { LatexBlock } from "@/components/latex-block";
import { PrintButton } from "./print-button";

type Props = { params: Promise<{ sessionId: string }> };

type ResponseRow = {
  question_id: number;
  question_order: number;
};

type QuestionRow = {
  id: number;
  topic: string;
  branch: string;
  subtopic: string;
  latexcode: string;
  type: string;
  solution: string | null;
  answer: string | null;
};

export default async function PrintSessionPage({ params }: Props) {
  const { sessionId } = await params;
  const supabase = await getServerSupabase();

  const { data: session } = await supabase
    .from("practice_sessions")
    .select("id, n_target, mode, diversity_score, created_at, filters")
    .eq("id", sessionId)
    .maybeSingle();
  if (!session) notFound();

  const { data: responses } = await supabase
    .from("practice_responses")
    .select("question_id, question_order")
    .eq("session_id", sessionId)
    .order("question_order");
  const responseRows = (responses ?? []) as ResponseRow[];

  const ids = responseRows.map((r) => r.question_id);
  const { data: qs } = await supabase
    .from("questions")
    .select("id, topic, branch, subtopic, latexcode, type, solution, answer")
    .in("id", ids);
  const qById = new Map<number, QuestionRow>();
  for (const q of (qs ?? []) as QuestionRow[]) qById.set(q.id, q);
  const ordered = responseRows
    .map((r) => qById.get(r.question_id))
    .filter((q): q is QuestionRow => Boolean(q));

  const sess = session as {
    id: string;
    n_target: number;
    mode: string | null;
    diversity_score: number | null;
    created_at: string;
  };

  return (
    <>
      <style>{`
        @media print {
          .no-print { display: none !important; }
          @page { margin: 0.7in; }
          body { font-size: 11pt; }
          .pagebreak { page-break-after: always; }
          .question { page-break-inside: avoid; }
        }
      `}</style>

      <main className="mx-auto max-w-3xl px-6 py-10">
        <header className="mb-8 border-b border-ink-200 pb-6">
          <div className="no-print mb-4 flex items-center justify-between">
            <span className="text-xs uppercase tracking-wider text-ink-500">
              Print / Save as PDF
            </span>
            <PrintButton />
          </div>
          <h1 className="text-2xl font-semibold">Practice set</h1>
          <p className="mt-1 text-sm text-ink-500">
            {new Date(sess.created_at).toLocaleString()} ·{" "}
            {ordered.length} questions ·{" "}
            {sess.mode === "diverse" && sess.diversity_score !== null
              ? `DPP-diverse (score ${sess.diversity_score.toFixed(2)})`
              : sess.mode ?? "random"}
          </p>
        </header>

        <ol className="space-y-10 list-none">
          {ordered.map((q, i) => (
            <li
              key={q.id}
              className="question border-b border-ink-100 pb-8 last:border-0"
            >
              <div className="mb-2 flex items-baseline justify-between text-xs text-ink-500">
                <span className="font-semibold text-ink-900">
                  Q{i + 1}.
                </span>
                <span>
                  {q.topic} · {q.subtopic}
                </span>
              </div>
              <article className="prose prose-ink max-w-none">
                <LatexBlock src={q.latexcode} className="text-base leading-relaxed" />
              </article>
            </li>
          ))}
        </ol>

        <section className="pagebreak mt-16 border-t-2 border-ink-300 pt-8">
          <h2 className="mb-6 text-xl font-semibold">Solutions</h2>
          <ol className="space-y-8 list-none">
            {ordered.map((q, i) => (
              <li key={q.id} className="question">
                <div className="mb-2 text-sm font-semibold text-ink-900">
                  Solution to Q{i + 1}.
                </div>
                {q.answer && q.answer !== "N/A" && (
                  <div className="mb-2">
                    <span className="text-xs uppercase tracking-wide text-ink-400 mr-2">
                      Answer:
                    </span>
                    <LatexBlock src={q.answer} className="inline" />
                  </div>
                )}
                {q.solution ? (
                  <LatexBlock
                    src={q.solution}
                    className="leading-relaxed text-sm"
                  />
                ) : (
                  <p className="text-sm italic text-ink-400">
                    No solution recorded.
                  </p>
                )}
              </li>
            ))}
          </ol>
        </section>
      </main>
    </>
  );
}
