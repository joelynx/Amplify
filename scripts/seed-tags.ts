// scripts/seed-tags.ts
// Synthesise question_tags rows from existing question metadata so the Tag
// tray on /practice has something to filter on. Each question gets:
//   - one slugified tag per slash-separated chunk in its subtopic
//   - one tag for its type
//   - one tag for its source (if present)
// Idempotent — ON CONFLICT DO NOTHING.
//
// Usage:  npx tsx scripts/seed-tags.ts

import { createClient } from "@supabase/supabase-js";
import { config } from "dotenv";
config({ path: ".env.local" });

function slugify(s: string): string {
  return s
    .toLowerCase()
    .replace(/['']/g, "")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 40);
}

async function main() {
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const key = process.env.SUPABASE_SERVICE_ROLE_KEY;
  if (!url || !key) {
    console.error("Missing env vars");
    process.exit(1);
  }
  const s = createClient(url, key);

  const { data: questions, error } = await s
    .from("questions")
    .select("id, subtopic, type, source");
  if (error) {
    console.error(error);
    process.exit(1);
  }

  const rows: { question_id: number; tag: string }[] = [];
  for (const q of questions ?? []) {
    const row = q as {
      id: number;
      subtopic: string;
      type: string;
      source: string | null;
    };
    const tags = new Set<string>();
    for (const chunk of (row.subtopic ?? "").split("/")) {
      const slug = slugify(chunk.trim());
      if (slug) tags.add(slug);
    }
    if (row.type) tags.add(slugify(row.type));
    if (row.source) tags.add(slugify(row.source));
    for (const tag of tags) rows.push({ question_id: row.id, tag });
  }

  console.log(`Inserting ${rows.length} tag rows from ${questions?.length} questions...`);

  // Bulk insert in chunks of 500.
  const CHUNK = 500;
  let inserted = 0;
  for (let i = 0; i < rows.length; i += CHUNK) {
    const slice = rows.slice(i, i + CHUNK);
    const { error: insErr } = await s
      .from("question_tags")
      .upsert(slice, { onConflict: "question_id,tag", ignoreDuplicates: true });
    if (insErr) {
      console.error("Insert failed:", insErr);
      process.exit(1);
    }
    inserted += slice.length;
    process.stdout.write(`  ${inserted}/${rows.length}\r`);
  }
  console.log("");

  const { count: finalCount } = await s
    .from("question_tags")
    .select("*", { count: "exact", head: true });
  console.log(`Done. question_tags now has ${finalCount} rows.`);
}

main();
