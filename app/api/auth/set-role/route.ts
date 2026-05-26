// Sets the current user's role in user_profiles. Used right after signup so
// new TA accounts get faculty privileges (they go through the same form as the
// student signup, just with a different role choice).
//
// Uses service-role to bypass RLS on user_profiles update.

import { NextResponse, type NextRequest } from "next/server";
import { getServerSupabase } from "@/lib/supabase/server";
import { getAdminSupabase } from "@/lib/supabase/admin";

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

  const admin = getAdminSupabase();
  const { error } = await admin
    .from("user_profiles")
    .update({ role })
    .eq("user_id", user.id);

  if (error) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
  return NextResponse.json({ ok: true, role });
}
