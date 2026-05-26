// POST /api/reports/[id]/resolve
// Marks a flag as resolved. Only the TA who originally submitted the
// underlying question (or admin/moderator) may resolve it.

import { NextResponse, type NextRequest } from "next/server";
import { getServerSupabase } from "@/lib/supabase/server";
import { getAdminSupabase } from "@/lib/supabase/admin";
import { rateLimit, clientKey } from "@/lib/rate-limit";

type Params = { params: Promise<{ id: string }> };

export async function POST(request: NextRequest, { params }: Params) {
  const { id } = await params;
  const reportId = Number.parseInt(id, 10);
  if (!Number.isFinite(reportId)) {
    return NextResponse.json({ error: "bad id" }, { status: 400 });
  }

  const supabase = await getServerSupabase();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }

  const rl = rateLimit(clientKey(request, user.id) + ":resolve", 30, 60_000);
  if (!rl.allowed) {
    return NextResponse.json(
      { error: "rate limited" },
      { status: 429, headers: { "Retry-After": String(Math.ceil(rl.retryAfterMs / 1000)) } }
    );
  }

  const { data: profile } = await supabase
    .from("user_profiles")
    .select("role")
    .eq("user_id", user.id)
    .maybeSingle();
  const role = (profile as { role?: string } | null)?.role;
  if (role !== "faculty" && role !== "admin" && role !== "moderator") {
    return NextResponse.json({ error: "TA-only" }, { status: 403 });
  }

  const admin = getAdminSupabase();

  // Verify the report is on a question the caller owns (or admin/mod can resolve anyone's).
  const { data: report } = await admin
    .from("question_reports")
    .select("id, question_id, resolved_at, questions!inner(submitted_by)")
    .eq("id", reportId)
    .maybeSingle();
  if (!report) {
    return NextResponse.json({ error: "report not found" }, { status: 404 });
  }
  const ownerEmail = (
    report as unknown as { questions: { submitted_by: string | null } }
  ).questions?.submitted_by;
  const canResolve =
    role === "admin" ||
    role === "moderator" ||
    (ownerEmail && ownerEmail === user.email);
  if (!canResolve) {
    return NextResponse.json(
      { error: "you can only resolve flags on your own questions" },
      { status: 403 }
    );
  }

  const { error } = await admin
    .from("question_reports")
    .update({ resolved_at: new Date().toISOString(), resolved_by: user.id })
    .eq("id", reportId);
  if (error) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }

  return NextResponse.json({ ok: true });
}
