import { getServerSupabase } from "@/lib/supabase/server";
import { PbsRunner } from "./runner";

type QuestionRow = {
  id: number;
  topic: string;
  branch: string;
  subtopic: string;
  latexcode: string;
  answer: string | null;
};

export default async function PbsPage() {
  const supabase = await getServerSupabase();

  // Pool: numerical questions. The TEST.csv didn't populate canonical answers
  // for most rows, so we don't filter on `answer IS NOT NULL` — the runner
  // treats null-answer widgets as self-graded (any submit dequeues the widget).
  const { data } = await supabase
    .from("questions")
    .select("id, topic, branch, subtopic, latexcode, answer")
    .eq("type", "numerical")
    .limit(40);

  const pool = (data ?? []) as QuestionRow[];
  // Shuffle so each PBS load gives a fresh order.
  for (let i = pool.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [pool[i], pool[j]] = [pool[j], pool[i]];
  }

  return (
    <main className="mx-auto max-w-5xl px-6 py-10">
      <div className="mb-6">
        <h1 className="text-3xl font-semibold tracking-tight">
          PBS — Parallel Burst Session
        </h1>
        <p className="mt-1 text-sm text-ink-500">
          Three numerical questions, all live at once. Correct answer swaps the
          widget for the next one in the pool. Wrong attempts halve that
          widget&apos;s available score (geometric ×0.5 decay, min 1 pt).
          Beat the clock.
        </p>
      </div>
      <PbsRunner pool={pool} visibleN={3} initialPoints={20} timerSeconds={300} />
    </main>
  );
}
