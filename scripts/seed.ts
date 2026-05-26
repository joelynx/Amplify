/**
 * Seed import from Files/TEST.csv → Supabase questions table.
 *
 * Idempotent: dedup by SHA-256 hash of normalized latexcode (matches the
 * `latex_hash` column in the schema).
 *
 * Run: npm run seed
 * Requires: .env.local with SUPABASE_SERVICE_ROLE_KEY (bypasses RLS).
 */

import { config } from "dotenv";
config({ path: ".env.local" });
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import crypto from "node:crypto";
import Papa from "papaparse";
import { getAdminSupabase } from "../lib/supabase/admin";

type CsvRow = {
  Topic: string;
  Branch: string;
  Subtopic: string;
  latexcode: string;
  Type: string;
  "In Syllabus?": string;
  Source: string;
  SubSource: string;
  AnsCode: string;
  Answer: string;
  Solution: string;
};

function sha256(s: string) {
  return crypto.createHash("sha256").update(s, "utf8").digest("hex");
}

function normalizeLatex(s: string) {
  return s.replace(/\r\n/g, "\n").replace(/\s+$/g, "");
}

function stripBrackets(s: string) {
  if (!s) return s;
  return s.replace(/^\s*\[/, "").replace(/\]\s*$/, "").trim();
}

function coerceInSyllabus(v: string): boolean {
  if (!v) return true;
  const lower = v.trim().toLowerCase();
  return lower !== "no" && lower !== "false" && lower !== "0";
}

function normalizeType(t: string): "proof" | "numerical" | "explanation/reasoning" {
  const lower = (t || "").trim().toLowerCase();
  if (lower.includes("proof")) return "proof";
  if (lower.includes("num")) return "numerical";
  return "explanation/reasoning";
}

async function main() {
  const dryRun = process.argv.includes("--dry-run");

  const csvPath = resolve(process.cwd(), "Files/TEST.csv");
  console.log(`Reading ${csvPath} ${dryRun ? "(dry-run)" : ""}...`);
  const raw = readFileSync(csvPath, "utf8");

  const parsed = Papa.parse<CsvRow>(raw, {
    header: true,
    skipEmptyLines: true,
    transformHeader: (h) => h.trim(),
  });

  if (parsed.errors.length > 0) {
    console.warn(`CSV parse warnings: ${parsed.errors.length}`);
    for (const e of parsed.errors.slice(0, 5)) console.warn(e);
  }

  console.log(`Parsed ${parsed.data.length} rows.`);

  if (dryRun) {
    // Validate row shape, count types and topics, print first few.
    const topicCounts = new Map<string, number>();
    const typeCounts = new Map<string, number>();
    const sourceCounts = new Map<string, number>();
    let withSolution = 0;
    let withAnswer = 0;
    let badRows = 0;
    const seenHashes = new Set<string>();
    let dupCount = 0;

    for (const row of parsed.data) {
      if (!row.latexcode || !row.Topic) {
        badRows++;
        continue;
      }
      topicCounts.set(row.Topic, (topicCounts.get(row.Topic) ?? 0) + 1);
      typeCounts.set(
        normalizeType(row.Type),
        (typeCounts.get(normalizeType(row.Type)) ?? 0) + 1
      );
      if (row.Source) {
        sourceCounts.set(row.Source, (sourceCounts.get(row.Source) ?? 0) + 1);
      }
      if (row.Solution) withSolution++;
      if (row.Answer && row.Answer !== "N/A") withAnswer++;
      const h = sha256(normalizeLatex(row.latexcode));
      if (seenHashes.has(h)) dupCount++;
      else seenHashes.add(h);
    }

    console.log("\n=== Dry-run summary ===");
    console.log(`Total rows:        ${parsed.data.length}`);
    console.log(`Bad rows:          ${badRows}`);
    console.log(`Duplicate hashes:  ${dupCount}`);
    console.log(`With Solution:     ${withSolution}`);
    console.log(`With Answer:       ${withAnswer}`);
    console.log(`Unique topics:     ${topicCounts.size}`);
    console.log(`Unique sources:    ${sourceCounts.size}`);
    console.log("\nTop topics:");
    [...topicCounts.entries()]
      .sort((a, b) => b[1] - a[1])
      .slice(0, 10)
      .forEach(([t, c]) => console.log(`  ${c.toString().padStart(4)}  ${t}`));
    console.log("\nType distribution:");
    [...typeCounts.entries()]
      .sort((a, b) => b[1] - a[1])
      .forEach(([t, c]) => console.log(`  ${c.toString().padStart(4)}  ${t}`));
    console.log("\nTop sources:");
    [...sourceCounts.entries()]
      .sort((a, b) => b[1] - a[1])
      .slice(0, 10)
      .forEach(([s, c]) => console.log(`  ${c.toString().padStart(4)}  ${s}`));

    console.log("\nFirst row preview:");
    const first = parsed.data.find((r) => r.latexcode);
    if (first) {
      console.log(`  Topic:     ${first.Topic}`);
      console.log(`  Branch:    ${first.Branch}  → stripped: ${stripBrackets(first.Branch)}`);
      console.log(`  Subtopic:  ${first.Subtopic}`);
      console.log(`  Type:      ${first.Type}  → normalized: ${normalizeType(first.Type)}`);
      console.log(`  Source:    ${first.Source}`);
      console.log(`  latexcode: ${first.latexcode.slice(0, 100)}${first.latexcode.length > 100 ? "..." : ""}`);
    }
    return;
  }

  const db = getAdminSupabase();

  // Pull existing hashes for idempotent dedup.
  const existing = new Set<string>();
  let from = 0;
  const PAGE = 1000;
  while (true) {
    const { data, error } = await db
      .from("questions")
      .select("latex_hash")
      .range(from, from + PAGE - 1);
    if (error) throw error;
    if (!data || data.length === 0) break;
    for (const r of data) existing.add(r.latex_hash);
    if (data.length < PAGE) break;
    from += PAGE;
  }
  console.log(`Existing rows in DB: ${existing.size}`);

  let inserted = 0;
  let skipped = 0;
  let errored = 0;

  const BATCH = 100;
  let batch: Array<{
    topic: string;
    branch: string;
    subtopic: string;
    latexcode: string;
    type: string;
    in_syllabus: boolean;
    source: string | null;
    subsource: string | null;
    answer: string | null;
    solution: string | null;
    latex_hash: string;
  }> = [];

  const flush = async () => {
    if (batch.length === 0) return;
    const { error } = await db.from("questions").insert(batch);
    if (error) {
      console.error(`Batch insert failed:`, error.message);
      errored += batch.length;
    } else {
      inserted += batch.length;
    }
    batch = [];
  };

  for (const row of parsed.data) {
    if (!row.latexcode || !row.Topic) {
      skipped++;
      continue;
    }
    const hash = sha256(normalizeLatex(row.latexcode));
    if (existing.has(hash)) {
      skipped++;
      continue;
    }
    existing.add(hash);
    batch.push({
      topic: (row.Topic || "").trim(),
      branch: stripBrackets(row.Branch || ""),
      subtopic: (row.Subtopic || "").trim(),
      latexcode: row.latexcode,
      type: normalizeType(row.Type),
      in_syllabus: coerceInSyllabus(row["In Syllabus?"]),
      source: row.Source?.trim() || null,
      subsource: row.SubSource?.trim() || null,
      answer: row.Answer?.trim() || null,
      solution: row.Solution || null,
      latex_hash: hash,
    });
    if (batch.length >= BATCH) await flush();
  }
  await flush();

  console.log(
    `\nDone. inserted=${inserted}, skipped=${skipped}, errored=${errored}`
  );
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
