// scripts/clean-test-artifacts.ts
// Nukes anything created by the Playwright E2E suites and other test runs.
//
// Targets:
//  - questions where topic LIKE 'E2E-Sentinel-%'
//  - questions where source LIKE 'Tut Sheet %' (the RUN timestamp ones)
//  - questions where source LIKE 'user:student-%@e2e.amplify' or 'user:ta-%@e2e.amplify'
//  - questions where source LIKE 'user:%@e2e.amplify'
//  - cascades: question_embeddings, question_tags, practice_responses, question_reports
//  - auth users matching student-*@e2e.amplify / ta-*@e2e.amplify
//
// Usage:  npx tsx scripts/clean-test-artifacts.ts

import { createClient } from "@supabase/supabase-js";
import { config } from "dotenv";
config({ path: ".env.local" });

async function main() {
  const s = createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.SUPABASE_SERVICE_ROLE_KEY!,
    { auth: { autoRefreshToken: false, persistSession: false } }
  );

  // ── 1. Find all question IDs that are test artifacts.
  const testIds = new Set<number>();

  const { data: byTopic } = await s
    .from("questions")
    .select("id")
    .like("topic", "E2E-Sentinel-%");
  for (const r of byTopic ?? []) testIds.add((r as { id: number }).id);

  const { data: bySourceTut } = await s
    .from("questions")
    .select("id")
    .like("source", "Tut Sheet 17%"); // RUN timestamps from Date.now()
  for (const r of bySourceTut ?? []) testIds.add((r as { id: number }).id);

  const { data: bySourceUser } = await s
    .from("questions")
    .select("id")
    .like("source", "user:%@e2e.amplify");
  for (const r of bySourceUser ?? []) testIds.add((r as { id: number }).id);

  const { data: bySubmitter } = await s
    .from("questions")
    .select("id")
    .like("submitted_by", "%@e2e.amplify");
  for (const r of bySubmitter ?? []) testIds.add((r as { id: number }).id);

  const ids = [...testIds];
  console.log(`Found ${ids.length} test question(s):`, ids);

  if (ids.length > 0) {
    // ── 2. Wipe child rows first.
    await s.from("question_embeddings").delete().in("question_id", ids);
    await s.from("question_tags").delete().in("question_id", ids);
    await s.from("practice_responses").delete().in("question_id", ids);
    await s.from("question_reports").delete().in("question_id", ids);
    // ── 3. Delete the questions.
    const { error: qErr } = await s.from("questions").delete().in("id", ids);
    if (qErr) console.error("delete questions failed:", qErr);
    else console.log(`  ✓ deleted ${ids.length} question(s) + child rows`);
  }

  // ── 4. Delete test auth users.
  const { data: list } = await s.auth.admin.listUsers();
  const testUsers = list.users.filter(
    (u) =>
      u.email &&
      (u.email.endsWith("@e2e.amplify") || u.email.endsWith("@e2e.test"))
  );
  console.log(`Found ${testUsers.length} test user(s)`);
  for (const u of testUsers) {
    // Clean up their practice sessions / mastery first.
    const { data: sessions } = await s
      .from("practice_sessions")
      .select("id")
      .eq("user_id", u.id);
    const sessionIds = (sessions ?? []).map((r) => (r as { id: string }).id);
    if (sessionIds.length > 0) {
      await s
        .from("practice_responses")
        .delete()
        .in("session_id", sessionIds);
      await s.from("practice_sessions").delete().in("id", sessionIds);
    }
    await s.from("user_mastery").delete().eq("user_id", u.id);
    await s.from("user_profiles").delete().eq("user_id", u.id);
    await s.auth.admin.deleteUser(u.id);
    console.log(`  ✓ deleted ${u.email}`);
  }

  console.log("\nDone.");
}

main();
