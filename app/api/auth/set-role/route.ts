// Sets the current user's role in user_profiles. Used right after signup so
// new TA accounts get faculty privileges. Locked down: a user can only set
// their role once — if a row already exists with a non-null role, the call
// is rejected. Stops trivial in-session self-promotion via devtools.

import { NextResponse, type NextRequest } from "next/server";
import { getServerSupabase } from "@/lib/supabase/server";
import { getAdminSupabase } from "@/lib/supabase/admin";
import { rateLimit, clientKey } from "@/lib/rate-limit";

const ALLOWED_ROLES = new Set(["student", "faculty"]);

export async function POST(req: NextRequest) {
  const { role } = (await req.json()) as { role?: string };
  if (!role || !ALLOWED_ROLES.has(role)) {
    return NextResponse.json({ error: "invalid role" }, { status: 400 });
  }

  const supabase = await getServerSupabase();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }

  // Rate limit — at most 3 set-role attempts per user per minute. Even one is
  // suspicious post-signup; 3 leaves room for transient failures.
  const rl = rateLimit(clientKey(req, user.id) + ":set-role", 3, 60_000);
  if (!rl.allowed) {
    return NextResponse.json(
      { error: "rate limited" },
      { status: 429, headers: { "Retry-After": String(Math.ceil(rl.retryAfterMs / 1000)) } }
    );
  }

  const admin = getAdminSupabase();

  // First-time-only: reject if a role is already set on this user.
  const { data: existing } = await admin
    .from("user_profiles")
    .select("role")
    .eq("user_id", user.id)
    .maybeSingle();
  const currentRole = (existing as { role?: string } | null)?.role;
  if (currentRole && currentRole !== "student") {
    return NextResponse.json(
      { error: "role already set; cannot re-promote" },
      { status: 403 }
    );
  }

  // Also reject if the account was created more than 5 minutes ago — the only
  // legitimate use of this endpoint is right after the signup form.
  const ageMs = Date.now() - new Date(user.created_at).getTime();
  if (ageMs > 5 * 60_000) {
    return NextResponse.json(
      { error: "role can only be set immediately after signup" },
      { status: 403 }
    );
  }

  const { error } = await admin
    .from("user_profiles")
    .update({ role })
    .eq("user_id", user.id);

  if (error) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
  return NextResponse.json({ ok: true, role });
}
