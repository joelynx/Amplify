// scripts/seed-demo-data.ts
// Populate a real user account with ~30 realistic practice responses + sessions
// so /me, /history, and the personalized landing strip don't look empty during
// the demo.
//
// Usage:  npx tsx scripts/seed-demo-data.ts <email>
//
// The user must already exist (signed up via /auth/login). The script looks them
// up by email via service-role + writes data straight to the practice tables.

import { createClient } from "@supabase/supabase-js";
import { config } from "dotenv";
config({ path: ".env.local" });

const email = process.argv[2];
if (!email) {
  console.error("Usage: npx tsx scripts/seed-demo-data.ts <email>");
  process.exit(1);
}

async function main() {
  const s = createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.SUPABASE_SERVICE_ROLE_KEY!,
    { auth: { autoRefreshToken: false, persistSession: false } }
  );

  // Find the user via the auth admin API.
  const { data: usersData, error: usersErr } = await s.auth.admin.listUsers();
  if (usersErr) {
    console.error("listUsers failed:", usersErr);
    process.exit(1);
  }
  const user = usersData.users.find((u) => u.email === email);
  if (!user) {
    console.error(`No user found with email "${email}". Sign up at /auth/login first.`);
    process.exit(1);
  }
  console.log(`Seeding demo data for user ${user.id} (${user.email})`);

  // Pull ~50 random questions across topics so the mastery distribution is varied.
  const { data: qs } = await s
    .from("questions")
    .select("id, topic, branch, subtopic")
    .limit(50);
  if (!qs || qs.length === 0) {
    console.error("No questions in the bank — seed the bank first.");
    process.exit(1);
  }

  // Wipe any prior demo data on this user so re-running is idempotent.
  const { data: oldSessions } = await s
    .from("practice_sessions")
    .select("id")
    .eq("user_id", user.id);
  const oldSessionIds = (oldSessions ?? []).map((r) => r.id as string);
  if (oldSessionIds.length > 0) {
    await s
      .from("practice_responses")
      .delete()
      .in("session_id", oldSessionIds);
    await s.from("practice_sessions").delete().in("id", oldSessionIds);
    console.log(`  cleared ${oldSessionIds.length} prior sessions`);
  }
  await s.from("user_mastery").delete().eq("user_id", user.id);

  // Build 5 realistic-looking sessions across recent days.
  // Per session: 6 questions, varied correctness, varied mode.
  const sessionsPlan = [
    { daysAgo: 0, mode: "diverse" as const, n: 6, diversity: 0.31 },
    { daysAgo: 1, mode: "diverse" as const, n: 5, diversity: 0.27 },
    { daysAgo: 2, mode: "random" as const, n: 8, diversity: null },
    { daysAgo: 4, mode: "diverse" as const, n: 6, diversity: 0.29 },
    { daysAgo: 6, mode: "random" as const, n: 5, diversity: null },
  ];

  let totalResponses = 0;
  const masteryAcc = new Map<
    string,
    { topic: string; branch: string; subtopic: string; correct: number; incorrect: number }
  >();

  for (const plan of sessionsPlan) {
    const sessionDate = new Date();
    sessionDate.setDate(sessionDate.getDate() - plan.daysAgo);

    const pickedQs: typeof qs = [];
    const pool = [...qs];
    for (let i = 0; i < plan.n && pool.length > 0; i++) {
      const idx = Math.floor(Math.random() * pool.length);
      pickedQs.push(pool.splice(idx, 1)[0]);
    }

    const { data: ins, error: sErr } = await s
      .from("practice_sessions")
      .insert({
        user_id: user.id,
        anon_key: null,
        filters: { topics: [...new Set(pickedQs.map((q) => q.topic))] },
        n_target: plan.n,
        mode: plan.mode,
        diversity_score: plan.diversity,
        created_at: sessionDate.toISOString(),
        completed_at: sessionDate.toISOString(),
      })
      .select("id")
      .single();
    if (sErr || !ins) {
      console.error("session insert failed:", sErr);
      continue;
    }
    const sessionId = ins.id as string;

    const responses = pickedQs.map((q, idx) => {
      // ~70% correct overall — mirrors a real user's accuracy curve.
      const correct = Math.random() < 0.7;
      const key = `${q.topic}||${q.branch}||${q.subtopic}`;
      const acc = masteryAcc.get(key) ?? {
        topic: q.topic,
        branch: q.branch,
        subtopic: q.subtopic,
        correct: 0,
        incorrect: 0,
      };
      if (correct) acc.correct++;
      else acc.incorrect++;
      masteryAcc.set(key, acc);
      return {
        session_id: sessionId,
        question_id: q.id,
        question_order: idx,
        user_answer: correct ? "answer" : "skip",
        is_correct: correct,
        time_taken_ms: 30_000 + Math.floor(Math.random() * 90_000),
        answered_at: sessionDate.toISOString(),
      };
    });
    const { error: rErr } = await s.from("practice_responses").insert(responses);
    if (rErr) {
      console.error("responses insert failed:", rErr);
      continue;
    }
    totalResponses += responses.length;
    console.log(`  + session ${plan.daysAgo}d ago: ${plan.n} qs, mode=${plan.mode}`);
  }

  // Build user_mastery rows from the accumulated correct/incorrect counts.
  // Beta(α, β) starts at (1, 1) for an uninformative prior, then +correct on α
  // and +incorrect on β.
  const masteryRows = [...masteryAcc.values()].map((m) => ({
    user_id: user.id,
    topic: m.topic,
    branch: m.branch,
    subtopic: m.subtopic,
    alpha: 1 + m.correct,
    beta: 1 + m.incorrect,
    total_seen: m.correct + m.incorrect,
  }));
  if (masteryRows.length > 0) {
    const { error: mErr } = await s
      .from("user_mastery")
      .insert(masteryRows);
    if (mErr) {
      console.error("mastery insert failed:", mErr);
    } else {
      console.log(`  + ${masteryRows.length} mastery rows`);
    }
  }

  console.log(
    `\nDone. ${sessionsPlan.length} sessions, ${totalResponses} responses, ${masteryRows.length} subtopics tracked.`
  );
}

main();
