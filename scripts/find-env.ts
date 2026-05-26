import { createClient } from "@supabase/supabase-js";
import { config } from "dotenv";
config({ path: ".env.local" });

async function main() {
  const s = createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.SUPABASE_SERVICE_ROLE_KEY!
  );
  const { data } = await s
    .from("questions")
    .select("id, latexcode, solution")
    .limit(2000);

  const counts: Record<string, number[]> = {};
  for (const r of data ?? []) {
    const blob = ((r.latexcode as string) ?? "") + "\n" + ((r.solution as string) ?? "");
    const matches = blob.match(/\\begin\{([a-z*]+)\}/g) ?? [];
    for (const m of matches) {
      const env = m.replace(/\\begin\{|\}/g, "");
      counts[env] ??= [];
      if (counts[env].length < 3) counts[env].push(r.id as number);
    }
  }

  for (const env of Object.keys(counts).sort()) {
    console.log(`\\begin{${env}} — examples: ${counts[env].slice(0, 3).join(", ")}`);
  }
}
main();
