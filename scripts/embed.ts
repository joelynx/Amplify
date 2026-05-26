// scripts/embed.ts
// Generate Gemini gemini-embedding-001 vectors for every question without one,
// and write them to the question_embeddings table.
// Idempotent — only embeds questions missing a gemini-embedding-001 row.
//
// Usage:  npx tsx scripts/embed.ts
//
// Requires in .env.local:
//   GOOGLE_API_KEY
//   NEXT_PUBLIC_SUPABASE_URL
//   SUPABASE_SERVICE_ROLE_KEY

import { GoogleGenerativeAI } from "@google/generative-ai";
import { createClient } from "@supabase/supabase-js";
import { config } from "dotenv";

config({ path: ".env.local" });

const BATCH_SIZE = 10;                    // concurrent API calls per batch (tuned for free-tier rate limit)
const BATCH_DELAY_MS = 6500;              // ~100 req/min, safely under Gemini free quota
const MODEL = "gemini-embedding-001";     // 768-dim Matryoshka truncation

async function main() {
  const apiKey = process.env.GOOGLE_API_KEY;
  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const supabaseServiceKey = process.env.SUPABASE_SERVICE_ROLE_KEY;

  if (!apiKey || !supabaseUrl || !supabaseServiceKey) {
    console.error("Missing env vars. Expect GOOGLE_API_KEY, NEXT_PUBLIC_SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY in .env.local");
    process.exit(1);
  }

  const supabase = createClient(supabaseUrl, supabaseServiceKey);
  const genAI = new GoogleGenerativeAI(apiKey);
  const embedModel = genAI.getGenerativeModel({ model: MODEL });

  // Pull all question_ids that already have an embedding for this model.
  const { data: existing, error: existingErr } = await supabase
    .from("question_embeddings")
    .select("question_id")
    .eq("model", MODEL);
  if (existingErr) {
    console.error("Failed to fetch existing embeddings:", existingErr);
    process.exit(1);
  }
  const existingIds = new Set((existing ?? []).map((r) => r.question_id as number));

  // Pull all questions.
  const { data: all, error: allErr } = await supabase
    .from("questions")
    .select("id, latexcode");
  if (allErr) {
    console.error("Failed to fetch questions:", allErr);
    process.exit(1);
  }

  const toEmbed = (all ?? []).filter((q) => !existingIds.has(q.id as number));
  if (toEmbed.length === 0) {
    console.log("Nothing to embed — all questions already have embeddings.");
    return;
  }

  console.log(`Embedding ${toEmbed.length} questions (batch=${BATCH_SIZE}, model=${MODEL})...`);
  const t0 = Date.now();
  let processed = 0;
  let failed = 0;

  for (let i = 0; i < toEmbed.length; i += BATCH_SIZE) {
    const batch = toEmbed.slice(i, i + BATCH_SIZE);

    const embedResults = await Promise.allSettled(
      batch.map(async (row) => {
        const res = await embedModel.embedContent({
          content: { role: "user", parts: [{ text: row.latexcode as string }] },
          taskType: "SEMANTIC_SIMILARITY" as never,
          outputDimensionality: 768,
        } as never);
        return { id: row.id as number, values: res.embedding.values as number[] };
      })
    );

    const rowsToInsert = embedResults
      .filter(
        (r): r is PromiseFulfilledResult<{ id: number; values: number[] }> =>
          r.status === "fulfilled"
      )
      .map((r) => ({
        question_id: r.value.id,
        model: MODEL,
        // pgvector accepts the textual literal '[v1,v2,...]'
        embedding: `[${r.value.values.join(",")}]`,
      }));

    const embedFailures = embedResults.filter((r) => r.status === "rejected").length;
    failed += embedFailures;

    if (rowsToInsert.length > 0) {
      const { error: insertErr } = await supabase
        .from("question_embeddings")
        .insert(rowsToInsert);
      if (insertErr) {
        console.error(`Insert failed for batch starting at ${i}:`, insertErr);
        failed += rowsToInsert.length;
      }
    }

    processed += batch.length;
    const elapsed = ((Date.now() - t0) / 1000).toFixed(1);
    const firstErr = embedResults.find((r) => r.status === "rejected") as PromiseRejectedResult | undefined;
    const errHint = firstErr ? ` — last err: ${String((firstErr.reason as Error)?.message ?? firstErr.reason).slice(0, 80)}` : "";
    console.log(`  ${processed}/${toEmbed.length}   ${elapsed}s   ${failed} failures${errHint}`);
    if (i + BATCH_SIZE < toEmbed.length) {
      await new Promise((r) => setTimeout(r, BATCH_DELAY_MS));
    }
  }

  const total = ((Date.now() - t0) / 1000).toFixed(1);
  console.log(`\nDone in ${total}s.  Wrote ${processed - failed} embeddings.`);
  if (failed > 0) {
    console.log(`${failed} rows failed. Re-run the script to retry — it's idempotent.`);
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
