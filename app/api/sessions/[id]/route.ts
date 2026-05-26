import { NextResponse, type NextRequest } from "next/server";
import { getServerSupabase } from "@/lib/supabase/server";

type Params = { params: Promise<{ id: string }> };

export async function GET(_request: NextRequest, { params }: Params) {
  const { id } = await params;
  const supabase = await getServerSupabase();

  const { data: session, error: sErr } = await supabase
    .from("practice_sessions")
    .select("*")
    .eq("id", id)
    .maybeSingle();
  if (sErr || !session) {
    return NextResponse.json({ error: "session_not_found" }, { status: 404 });
  }

  const { data: responses } = await supabase
    .from("practice_responses")
    .select("question_id, question_order, user_answer, is_correct, answered_at")
    .eq("session_id", id)
    .order("question_order");

  const total = responses?.length ?? 0;
  const answered =
    responses?.filter((r) => r.user_answer !== null).length ?? 0;
  const correct =
    responses?.filter((r) => r.is_correct === true).length ?? 0;

  // Next unanswered.
  const next = responses?.find((r) => r.user_answer === null);
  let nextQuestion = null;
  if (next) {
    const { data: q } = await supabase
      .from("questions")
      .select(
        "id, topic, branch, subtopic, latexcode, type, source, subsource, answer, solution"
      )
      .eq("id", next.question_id)
      .single();
    nextQuestion = q;
  }

  return NextResponse.json({
    session,
    total,
    answered,
    correct,
    next_order: next?.question_order ?? null,
    next_question: nextQuestion,
    completed: answered === total && total > 0,
  });
}
