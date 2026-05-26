// scripts/compute-difficulty.ts
// Smart Difficulty (Joel's §13.1 sub-scores, web-port version):
//   novelty   = 1 − max(cosine(this, other-in-same-subtopic))   ∈ [0,1]
//   length    = log1p(solution_chars) / log1p(MAX_OBS)          ∈ [0,1]
//   combined  = 0.5 * novelty + 0.5 * length, scaled to [0, 20]
// Writes the result to questions.difficulty_rating. Idempotent — re-running
// recomputes from scratch.
//
// Usage:  npx tsx scripts/compute-difficulty.ts

import { createClient } from "@supabase/supabase-js";
import { config } from "dotenv";
config({ path: ".env.local" });

function cosine(a: number[], b: number[]): number {
  let dot = 0;
  let na = 0;
  let nb = 0;
  for (let i = 0; i < a.length; i++) {
    dot += a[i] * b[i];
    na += a[i] * a[i];
    nb += b[i] * b[i];
  }
  const d = Math.sqrt(na) * Math.sqrt(nb);
  return d === 0 ? 0 : dot / d;
}

function parseVec(raw: unknown): number[] | null {
  if (Array.isArray(raw)) return (raw as unknown[]).map(Number);
  if (typeof raw === "string") {
    const inner = raw.replace(/^\[|\]$/g, "");
    if (!inner) return null;
    return inner.split(",").map(Number);
  }
  return null;
}

async function main() {
  const s = createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.SUPABASE_SERVICE_ROLE_KEY!
  );

  const { data: qs } = await s
    .from("questions")
    .select("id, subtopic, solution");
  const { data: es } = await s
    .from("question_embeddings")
    .select("question_id, embedding")
    .eq("model", "gemini-embedding-001");

  const vecById = new Map<number, number[]>();
  for (const e of es ?? []) {
    const v = parseVec((e as { embedding: unknown }).embedding);
    if (v) vecById.set((e as { question_id: number }).question_id, v);
  }

  type Q = { id: number; subtopic: string; solution: string | null };
  const all = (qs ?? []) as Q[];

  // Group by subtopic for novelty pairings.
  const bySubtopic = new Map<string, Q[]>();
  for (const q of all) {
    if (!bySubtopic.has(q.subtopic)) bySubtopic.set(q.subtopic, []);
    bySubtopic.get(q.subtopic)!.push(q);
  }

  // Max observed solution length (for length-score normalisation).
  const maxLen = Math.max(
    1,
    ...all.map((q) => (q.solution?.length ?? 0))
  );
  const logMax = Math.log1p(maxLen);

  console.log(`Computing difficulty for ${all.length} questions...`);
  let written = 0;

  for (const q of all) {
    // Novelty
    let novelty = 0;
    const myVec = vecById.get(q.id);
    if (myVec) {
      const peers = (bySubtopic.get(q.subtopic) ?? []).filter(
        (p) => p.id !== q.id
      );
      let maxCos = 0;
      for (const p of peers) {
        const pv = vecById.get(p.id);
        if (!pv) continue;
        const c = cosine(myVec, pv);
        if (c > maxCos) maxCos = c;
      }
      novelty = 1 - maxCos;
    }

    // Length score
    const lenScore =
      q.solution && q.solution.length > 0
        ? Math.log1p(q.solution.length) / logMax
        : 0;

    const combined = 0.5 * novelty + 0.5 * lenScore; // [0,1]
    const rating = Math.max(0, Math.min(20, +(combined * 20).toFixed(2)));

    await s.from("questions").update({ difficulty_rating: rating }).eq("id", q.id);
    written++;
    if (written % 50 === 0) {
      process.stdout.write(`  ${written}/${all.length}\r`);
    }
  }
  console.log(`\nDone. Wrote ${written} difficulty ratings.`);

  // Quick distribution check
  const { data: dist } = await s
    .from("questions")
    .select("difficulty_rating")
    .order("difficulty_rating", { ascending: false })
    .limit(5);
  console.log("Top 5 difficulty:", dist?.map((d) => d.difficulty_rating));
}

main();
