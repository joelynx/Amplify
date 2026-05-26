import { NextResponse, type NextRequest } from "next/server";
import { getServerSupabase } from "@/lib/supabase/server";
import { pickRandomQuestionIds, pickDiverseQuestionIds } from "@/lib/queries";
import type { PracticeFilters } from "@/lib/db/types";

export async function POST(request: NextRequest) {
  const body = (await request.json()) as {
    filters?: PracticeFilters;
    n_target?: number;
    anon_key?: string;
    mode?: "random" | "diverse";
  };
  const filters = body.filters ?? {};
  const n = Math.max(1, Math.min(50, body.n_target ?? 10));
  const requestedMode: "random" | "diverse" =
    body.mode === "diverse" ? "diverse" : "random";

  const supabase = await getServerSupabase();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  let ids: number[];
  let total: number;
  let shortfall: number;
  let diversity_score: number | null = null;
  let actualMode: "random" | "diverse" = requestedMode;
  let usedFallback = false;

  if (requestedMode === "diverse") {
    const r = await pickDiverseQuestionIds(supabase, filters, n);
    ids = r.ids;
    total = r.total;
    shortfall = r.shortfall;
    diversity_score = r.diversity_score;
    usedFallback = r.used_fallback;
    if (usedFallback) actualMode = "random";
  } else {
    const r = await pickRandomQuestionIds(supabase, filters, n);
    ids = r.ids;
    total = r.total;
    shortfall = r.shortfall;
  }

  if (ids.length === 0) {
    return NextResponse.json(
      { error: "No questions match the selected filters." },
      { status: 400 }
    );
  }

  const sessionInsert = await supabase
    .from("practice_sessions")
    .insert({
      user_id: user?.id ?? null,
      anon_key: user ? null : (body.anon_key ?? null),
      filters,
      n_target: n,
      mode: actualMode,
      diversity_score,
    })
    .select("id")
    .single();

  if (sessionInsert.error) {
    return NextResponse.json(
      { error: sessionInsert.error.message },
      { status: 500 }
    );
  }

  const sessionId = sessionInsert.data.id as string;

  const placeholders = ids.map((qid, idx) => ({
    session_id: sessionId,
    question_id: qid,
    question_order: idx,
  }));
  const respInsert = await supabase
    .from("practice_responses")
    .insert(placeholders);
  if (respInsert.error) {
    return NextResponse.json(
      { error: respInsert.error.message },
      { status: 500 }
    );
  }

  return NextResponse.json({
    session_id: sessionId,
    n_questions: ids.length,
    total_matching: total,
    shortfall,
    mode: actualMode,
    diversity_score,
    used_fallback: usedFallback,
  });
}
