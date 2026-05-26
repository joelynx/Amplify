import { createClient } from "@supabase/supabase-js";
import { config } from "dotenv";
config({ path: ".env.local" });

async function main() {
  const s = createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.SUPABASE_SERVICE_ROLE_KEY!
  );
  const { data } = await s.from("questions").select("id, latexcode").limit(8);
  for (const r of data ?? []) {
    console.log(`--- id ${r.id} (${(r.latexcode as string).length} chars) ---`);
    console.log((r.latexcode as string).slice(0, 400));
    console.log();
  }
}
main();
