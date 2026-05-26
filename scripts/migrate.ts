// scripts/migrate.ts
// Apply every supabase/migrations/*.sql file in lexical order against DATABASE_URL.
// All migrations are written to be idempotent — re-running is safe.
//
// Usage:  npx tsx scripts/migrate.ts
//
// Requires in .env.local:
//   DATABASE_URL

import { config } from "dotenv";
import { Client } from "pg";
import { readdirSync, readFileSync } from "fs";
import { join } from "path";

config({ path: ".env.local" });

async function main() {
  const url = process.env.DATABASE_URL;
  if (!url) {
    console.error("DATABASE_URL missing in .env.local");
    process.exit(1);
  }

  const client = new Client({ connectionString: url });
  try {
    await client.connect();
    console.log("Connected to Postgres.\n");
  } catch (err) {
    console.error("Failed to connect:", (err as Error).message);
    process.exit(1);
  }

  // Ensure the schema_migrations tracker exists; load already-applied filenames.
  await client.query(`
    create table if not exists public.schema_migrations (
      filename text primary key,
      applied_at timestamptz not null default now()
    );
  `);
  const appliedRows = await client.query(
    "select filename from public.schema_migrations"
  );
  const alreadyTracked = new Set<string>(
    appliedRows.rows.map((r: { filename: string }) => r.filename)
  );

  const migrationDir = "supabase/migrations";
  const files = readdirSync(migrationDir)
    .filter((f) => f.endsWith(".sql"))
    .sort();

  if (files.length === 0) {
    console.error(`No .sql files in ${migrationDir}`);
    await client.end();
    process.exit(1);
  }

  let applied = 0;
  let failed = 0;
  let tracked = 0;

  for (const file of files) {
    if (alreadyTracked.has(file)) {
      console.log(`  ${file} ... SKIP (tracked)`);
      tracked++;
      continue;
    }

    const sql = readFileSync(join(migrationDir, file), "utf-8");
    process.stdout.write(`  ${file} ... `);
    try {
      await client.query(sql);
      await client.query(
        "insert into public.schema_migrations (filename) values ($1) on conflict do nothing",
        [file]
      );
      console.log("OK");
      applied++;
    } catch (err) {
      const msg = (err as Error).message;
      // "Already exists" means the migration's effects are present from a
      // pre-tracker run — mark it tracked so future runs skip cleanly.
      if (/already exists|duplicate key|duplicate_object/i.test(msg)) {
        await client.query(
          "insert into public.schema_migrations (filename) values ($1) on conflict do nothing",
          [file]
        );
        console.log("SKIP (effects already present — now tracked)");
        applied++;
      } else {
        console.log("FAILED");
        console.error(`    ${msg}`);
        failed++;
      }
    }
  }

  await client.end();

  console.log(
    `\n${tracked} already tracked · ${applied} newly applied · ${failed} failed (of ${files.length} total).`
  );
  if (failed > 0) process.exit(1);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
