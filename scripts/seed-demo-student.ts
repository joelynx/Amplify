// scripts/seed-demo-student.ts
// One-shot: creates a confirmed demo student account, then seeds it with
// realistic practice data so /me, /history, /stats all light up for the pitch.
//
// Usage:  npx tsx scripts/seed-demo-student.ts <email> <password>

import { createClient } from "@supabase/supabase-js";
import { config } from "dotenv";
config({ path: ".env.local" });

const email = process.argv[2];
const password = process.argv[3];
if (!email || !password) {
  console.error("Usage: npx tsx scripts/seed-demo-student.ts <email> <password>");
  process.exit(1);
}

async function main() {
  const s = createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.SUPABASE_SERVICE_ROLE_KEY!,
    { auth: { autoRefreshToken: false, persistSession: false } }
  );

  // ── 1. Ensure the user exists (create if not).
  let userId: string;
  const { data: list } = await s.auth.admin.listUsers();
  const existing = list.users.find((u) => u.email === email);
  if (existing) {
    userId = existing.id;
    console.log(`User exists: ${email} (${userId})`);
    // Update password so the credentials are guaranteed correct.
    await s.auth.admin.updateUserById(userId, { password });
    console.log("  password reset to provided value");
  } else {
    const { data: created, error: createErr } = await s.auth.admin.createUser({
      email,
      password,
      email_confirm: true,
    });
    if (createErr || !created.user) {
      console.error("createUser failed:", createErr);
      process.exit(1);
    }
    userId = created.user.id;
    console.log(`Created user: ${email} (${userId})`);
  }

  // ── 2. Pull questions from the bank.
  const { data: qs } = await s
    .from("questions")
    .select("id, topic, branch, subtopic")
    .limit(80);
  if (!qs || qs.length === 0) {
    console.error("No questions in bank.");
    process.exit(1);
  }

  // ── 3. Wipe prior demo data on this user.
  const { data: oldSessions } = await s
    .from("practice_sessions")
    .select("id")
    .eq("user_id", userId);
  const oldSessionIds = (oldSessions ?? []).map((r) => r.id as string);
  if (oldSessionIds.length > 0) {
    await s.from("practice_responses").delete().in("session_id", oldSessionIds);
    await s.from("practice_sessions").delete().in("id", oldSessionIds);
    console.log(`  cleared ${oldSessionIds.length} prior sessions`);
  }
  await s.from("user_mastery").delete().eq("user_id", userId);

  // ── 4. Build sessions across the last ~10 days for a healthy calendar/heatmap.
  const sessionsPlan = [
    { daysAgo: 0, mode: "diverse" as const, n: 8, diversity: 0.34 },
    { daysAgo: 1, mode: "diverse" as const, n: 6, diversity: 0.31 },
    { daysAgo: 2, mode: "random" as const, n: 10, diversity: null },
    { daysAgo: 3, mode: "diverse" as const, n: 7, diversity: 0.29 },
    { daysAgo: 5, mode: "random" as const, n: 6, diversity: null },
    { daysAgo: 7, mode: "diverse" as const, n: 8, diversity: 0.33 },
    { daysAgo: 9, mode: "diverse" as const, n: 5, diversity: 0.26 },
  ];

  const masteryAcc = new Map<
    string,
    {
      topic: string;
      branch: string;
      subtopic: string;
      correct: number;
      incorrect: number;
    }
  >();
  let totalResponses = 0;

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
        user_id: userId,
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
      // Bias accuracy by topic so weakest/strongest lists are not flat.
      const baseRate = q.topic.length % 2 === 0 ? 0.78 : 0.58;
      const correct = Math.random() < baseRate;
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
        user_answer: correct ? "user answer" : "skip",
        is_correct: correct,
        time_taken_ms: 25_000 + Math.floor(Math.random() * 80_000),
        answered_at: sessionDate.toISOString(),
      };
    });
    const { error: rErr } = await s.from("practice_responses").insert(responses);
    if (rErr) {
      console.error("responses insert failed:", rErr);
      continue;
    }
    totalResponses += responses.length;
    console.log(
      `  + session ${plan.daysAgo}d ago: ${plan.n} qs, mode=${plan.mode}`
    );
  }

  // ── 5. Build user_mastery rows from accumulated counts.
  const masteryRows = [...masteryAcc.values()].map((m) => ({
    user_id: userId,
    topic: m.topic,
    branch: m.branch,
    subtopic: m.subtopic,
    alpha: 1 + m.correct,
    beta: 1 + m.incorrect,
    total_seen: m.correct + m.incorrect,
  }));
  if (masteryRows.length > 0) {
    const { error: mErr } = await s.from("user_mastery").insert(masteryRows);
    if (mErr) {
      console.error("mastery insert failed:", mErr);
    } else {
      console.log(`  + ${masteryRows.length} mastery rows`);
    }
  }

  console.log(
    `\n✓ Demo student ready: ${email}`,
    `\n  ${sessionsPlan.length} sessions, ${totalResponses} responses, ${masteryRows.length} subtopics`
  );
}

main();
