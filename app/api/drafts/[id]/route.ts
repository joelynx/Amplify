// PATCH /api/drafts/[id]
// Lets the original TA edit a question they submitted. Admins/moderators can
// edit anyone's.

import { NextResponse, type NextRequest } from "next/server";
import crypto from "node:crypto";
import { getServerSupabase } from "@/lib/supabase/server";
import { getAdminSupabase } from "@/lib/supabase/admin";
import { rateLimit, clientKey } from "@/lib/rate-limit";

const MAX_LATEX_BYTES = 16_000;
const MAX_SOLUTION_BYTES = 16_000;

function normalize(s: string): string {
  return s.replace(/\s+/g, " ").trim();
}

type Params = { params: Promise<{ id: string }> };

export async function PATCH(request: NextRequest, { params }: Params) {
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

  const rl = rateLimit(clientKey(request, user.id) + ":edit", 20, 60_000);
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

  // Verify ownership.
  const { data: existing } = await admin
    .from("questions")
    .select("submitted_by")
    .eq("id", questionId)
    .maybeSingle();
  if (!existing) {
    return NextResponse.json({ error: "not found" }, { status: 404 });
  }
  const owner = (existing as { submitted_by: string | null }).submitted_by;
  const isElevated = role === "admin" || role === "moderator";
  if (!isElevated && owner !== user.email) {
    return NextResponse.json(
      { error: "you can only edit questions you submitted" },
      { status: 403 }
    );
  }

  const body = await request.json();
  const updates: Record<string, unknown> = {};
  for (const f of ["topic", "branch", "subtopic", "source", "answer", "solution", "latexcode", "type"]) {
    if (typeof body[f] === "string") updates[f] = body[f];
  }

  // Length guards.
  if (typeof updates.latexcode === "string" && updates.latexcode.length > MAX_LATEX_BYTES) {
    return NextResponse.json({ error: "question body too long" }, { status: 413 });
  }
  if (typeof updates.solution === "string" && updates.solution.length > MAX_SOLUTION_BYTES) {
    return NextResponse.json({ error: "solution too long" }, { status: 413 });
  }
  for (const f of ["topic", "branch", "subtopic", "source", "answer"]) {
    const v = updates[f];
    if (typeof v === "string" && v.length > 200) {
      return NextResponse.json({ error: `${f} too long` }, { status: 413 });
    }
  }

  // Recompute latex_hash if the body changed.
  if (typeof updates.latexcode === "string") {
    updates.latex_hash = crypto
      .createHash("sha256")
      .update(normalize(updates.latexcode))
      .digest("hex");
  }

  const { error } = await admin
    .from("questions")
    .update(updates)
    .eq("id", questionId);

  if (error) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
  return NextResponse.json({ ok: true });
}
