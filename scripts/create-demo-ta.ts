import { createClient } from "@supabase/supabase-js";
import { config } from "dotenv";
config({ path: ".env.local" });

const email = "demo.ta@iitdabudhabi.ac.ae";
const password = "amplify-demo-2026";

(async () => {
  const s = createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.SUPABASE_SERVICE_ROLE_KEY!,
    { auth: { autoRefreshToken: false, persistSession: false } }
  );
  const list = await s.auth.admin.listUsers();
  let user = list.data.users.find((u) => u.email === email);
  if (user) {
    await s.auth.admin.updateUserById(user.id, { password });
    console.log("TA exists, password reset:", email);
  } else {
    const c = await s.auth.admin.createUser({ email, password, email_confirm: true });
    user = c.data.user!;
    console.log("Created TA:", email, user.id);
  }
  // Force role=faculty bypassing the 5-min set-role gate.
  await s.from("user_profiles").upsert(
    { user_id: user.id, role: "faculty" },
    { onConflict: "user_id" }
  );
  console.log("  role: faculty");
  console.log("\n✓ Demo TA ready:", email, "/", password);
})();
