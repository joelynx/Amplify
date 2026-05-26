import { createClient } from "@supabase/supabase-js";

// Service-role client — bypasses RLS. Use only in trusted server-side scripts
// (seed import, admin actions). Never expose to the browser.
export function getAdminSupabase() {
  return createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.SUPABASE_SERVICE_ROLE_KEY!,
    {
      auth: { autoRefreshToken: false, persistSession: false },
    }
  );
}
