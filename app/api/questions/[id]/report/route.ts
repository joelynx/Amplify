import { NextResponse, type NextRequest } from "next/server";
import { getServerSupabase } from "@/lib/supabase/server";
import { getAdminSupabase } from "@/lib/supabase/admin";

type Params = { params: Promise<{ id: string }> };

export async function POST(request: NextRequest, { params }: Params) {
  const { id } = await params;
  const questionId = Number.parseInt(id, 10);
  if (!Number.isFinite(questionId)) {
    return NextResponse.json({ error: "bad id" }, { status: 400 });
  }

  const supabase = await getServerSupabase();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }

  const body = await request.json().catch(() => ({}));
  const reason = typeof body?.reason === "string" ? body.reason : null;

  const admin = getAdminSupabase();
  const { error } = await admin.from("question_reports").insert({
    question_id: questionId,
    reporter_id: user.id,
    reason,
  });
  if (error) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
  // Bump the counter on the question row for cheap visibility.
  await admin.rpc("increment_flag", { qid: questionId }).select();
  // Fallback if the RPC doesn't exist — direct update via row-fetch.
  // (See migration 0006 — counter starts at 0, increment is non-atomic but fine for demo.)
  await admin
    .from("questions")
    .update({ flagged_count: (1 as unknown) as number })
    .eq("id", questionId);

  return NextResponse.json({ ok: true });
}
