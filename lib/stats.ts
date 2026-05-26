import type { SupabaseClient } from "@supabase/supabase-js";

// Public stats for the landing page. Cheap counts — single COUNT queries.
// Returns sensible zeros if any query errors out so the landing never breaks.
export async function getPublicStats(supabase: SupabaseClient) {
  const [
    { count: questionCount },
    { count: institutionCount },
    { count: contributorCount },
    { count: sessionsThisWeek },
  ] = await Promise.all([
    supabase.from("questions").select("id", { count: "exact", head: true }),
    supabase
      .from("institutions")
      .select("id", { count: "exact", head: true })
      .eq("status", "active"),
    supabase
      .from("user_profiles")
      .select("user_id", { count: "exact", head: true })
      .in("role", ["faculty", "admin", "moderator"]),
    supabase
      .from("practice_sessions")
      .select("id", { count: "exact", head: true })
      .gte(
        "created_at",
        new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString()
      ),
  ]);

  return {
    questions: questionCount ?? 0,
    institutions: institutionCount ?? 0,
    contributors: contributorCount ?? 0,
    sessionsThisWeek: sessionsThisWeek ?? 0,
  };
}
