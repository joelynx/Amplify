import { NextResponse, type NextRequest } from "next/server";
import { getServerSupabase } from "@/lib/supabase/server";

type Params = { params: Promise<{ id: string }> };

// Loose numerical equivalence: parse both sides, compare with relative tolerance.
function looselyEqual(a: string, b: string): boolean {
  const norm = (s: string) =>
    s.trim().toLowerCase().replace(/\s+/g, "").replace(/^\\boxed\{|\}$/g, "");
  const na = norm(a);
  const nb = norm(b);
  if (na === nb) return true;
  const fa = Number.parseFloat(na);
  const fb = Number.parseFloat(nb);
  if (Number.isFinite(fa) && Number.isFinite(fb)) {
    if (fa === fb) return true;
    const diff = Math.abs(fa - fb);
    const scale = Math.max(1, Math.abs(fa), Math.abs(fb));
    return diff / scale < 1e-3;
  }
  return false;
}

export async function POST(request: NextRequest, { params }: Params) {
  const { id } = await params;
  const body = (await request.json()) as {
    question_id: number;
    user_answer?: string;
    time_taken_ms?: number;
    self_assessment?: "got_it" | "partial" | "missed";
  };

  const supabase = await getServerSupabase();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  // Load the question to grade.
  const { data: q, error: qErr } = await supabase
    .from("questions")
    .select("id, topic, branch, subtopic, answer, type, solution")
    .eq("id", body.question_id)
    .maybeSingle();
  if (qErr || !q) {
    return NextResponse.json({ error: "question_not_found" }, { status: 404 });
  }

  // Grade.
  // Priority: explicit self-assessment > auto-grade > null.
  let isCorrect: boolean | null = null;
  let masteryUpdate: { correct: number; partial: number } | null = null;

  if (body.self_assessment) {
    if (body.self_assessment === "got_it") {
      isCorrect = true;
      masteryUpdate = { correct: 1, partial: 0 };
    } else if (body.self_assessment === "partial") {
      isCorrect = false;
      masteryUpdate = { correct: 0.5, partial: 0.5 };
    } else {
      isCorrect = false;
      masteryUpdate = { correct: 0, partial: 1 };
    }
  } else if (q.answer && q.answer !== "N/A" && body.user_answer) {
    isCorrect = looselyEqual(body.user_answer, q.answer);
    masteryUpdate = isCorrect
      ? { correct: 1, partial: 0 }
      : { correct: 0, partial: 1 };
  }

  // Record the response. Use upsert in case the answer endpoint is called
  // twice (first for attempt, second for self-assessment).
  const { error: updErr } = await supabase
    .from("practice_responses")
    .update({
      user_answer: body.user_answer ?? null,
      is_correct: isCorrect,
      time_taken_ms: body.time_taken_ms ?? null,
      answered_at: new Date().toISOString(),
    })
    .eq("session_id", id)
    .eq("question_id", body.question_id);

  if (updErr) {
    return NextResponse.json({ error: updErr.message }, { status: 500 });
  }

  // Update mastery if signed in and we have an outcome.
  if (user && masteryUpdate) {
    const { data: m } = await supabase
      .from("user_mastery")
      .select("alpha, beta, total_seen")
      .eq("user_id", user.id)
      .eq("topic", q.topic)
      .eq("branch", q.branch)
      .eq("subtopic", q.subtopic)
      .maybeSingle();

    const alpha = (m?.alpha ?? 1) + masteryUpdate.correct;
    const beta = (m?.beta ?? 1) + masteryUpdate.partial;
    const total = (m?.total_seen ?? 0) + 1;

    await supabase.from("user_mastery").upsert(
      {
        user_id: user.id,
        topic: q.topic,
        branch: q.branch,
        subtopic: q.subtopic,
        alpha,
        beta,
        total_seen: total,
        last_updated: new Date().toISOString(),
      },
      { onConflict: "user_id,topic,branch,subtopic" }
    );
  }

  // Whether the question is gradeable (has a canonical answer) drives the UI.
  const gradeable = Boolean(q.answer && q.answer !== "N/A");

  return NextResponse.json({
    is_correct: isCorrect,
    canonical_answer: q.answer,
    solution: q.solution,
    gradeable,
    requires_self_assessment: !gradeable,
  });
}
