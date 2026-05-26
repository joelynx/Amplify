import { NextResponse, type NextRequest } from "next/server";
import { getServerSupabase } from "@/lib/supabase/server";

export async function POST(request: NextRequest) {
  const body = await request.json();
  const supabase = await getServerSupabase();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }

  const { data: profile } = await supabase
    .from("user_profiles")
    .select("role, institution_id")
    .eq("user_id", user.id)
    .maybeSingle();

  const role = (profile as { role?: string } | null)?.role;
  if (role !== "faculty" && role !== "admin" && role !== "moderator") {
    return NextResponse.json(
      { error: "faculty_role_required" },
      { status: 403 }
    );
  }

  const insert = await supabase
    .from("question_drafts")
    .insert({
      author_id: user.id,
      institution_id:
        (profile as { institution_id?: number | null }).institution_id ?? null,
      course_id: body.course_id ?? null,
      topic: body.topic,
      branch: body.branch,
      subtopic: body.subtopic,
      type: body.type,
      latexcode: body.latexcode,
      answer: body.answer ?? null,
      solution: body.solution ?? null,
      source: body.source ?? null,
    })
    .select("id")
    .single();

  if (insert.error) {
    return NextResponse.json({ error: insert.error.message }, { status: 500 });
  }

  return NextResponse.json({ id: insert.data.id });
}
