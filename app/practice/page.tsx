import { Suspense } from "react";
import { redirect } from "next/navigation";
import { PracticeFilterForm } from "./filter-form";
import { getPracticeTaxonomy } from "@/lib/cached";
import { getServerSupabase } from "@/lib/supabase/server";

export default async function PracticePage() {
  const supabase = await getServerSupabase();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) redirect("/auth/login?next=/practice");

  // TAs / faculty don't do practice — they contribute. Bounce them to /author.
  const { data: profile } = await supabase
    .from("user_profiles")
    .select("role")
    .eq("user_id", user.id)
    .maybeSingle();
  const role = (profile as { role?: string } | null)?.role;
  if (role === "faculty" || role === "admin" || role === "moderator") {
    redirect("/author");
  }

  const { tree, types, sources, tags } = await getPracticeTaxonomy();

  return (
    <main className="mx-auto max-w-3xl px-6 py-10">
      <h1 className="mb-8 text-3xl font-semibold tracking-tight">Practice</h1>

      <Suspense fallback={<p className="text-sm text-ink-500">Loading…</p>}>
        <PracticeFilterForm
          tree={tree}
          types={types}
          sources={sources}
          tags={tags}
        />
      </Suspense>
    </main>
  );
}
