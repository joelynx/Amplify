import { redirect } from "next/navigation";
import Link from "next/link";
import { getServerSupabase } from "@/lib/supabase/server";
import { AuthorForm } from "./form";

export default async function AuthorPage() {
  const supabase = await getServerSupabase();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) redirect("/auth/login?next=/author");

  const { data: profile } = await supabase
    .from("user_profiles")
    .select("role, institution_id, institution:institutions(*)")
    .eq("user_id", user.id)
    .maybeSingle();

  const role = (profile as { role?: string } | null)?.role;
  if (role !== "faculty" && role !== "admin" && role !== "moderator") {
    return (
      <main className="mx-auto max-w-2xl px-6 py-16">
        <h1 className="display text-3xl font-semibold">
          Authoring is faculty-gated
        </h1>
        <p className="mt-3 text-ink-700">
          Every question in the bank has a peer-reviewed author. That trust
          model is what makes the commons valuable — so authoring is open to
          faculty, moderators, and admins.
        </p>
        <p className="mt-3 text-ink-500">
          You&apos;re signed in as <strong>{user.email}</strong>. To request
          faculty access at your institution, email{" "}
          <a
            href="mailto:24a1cseb0015@iitdabudhabi.ac.ae?subject=Faculty%20access%20request"
            className="underline"
          >
            us
          </a>{" "}
          from your institution&apos;s email address.
        </p>
        <div className="mt-8 flex gap-3">
          <Link
            href="/practice"
            className="rounded-md bg-ink-900 px-4 py-2 text-sm font-medium text-white hover:bg-ink-700"
          >
            Practice instead
          </Link>
          <Link
            href="/"
            className="rounded-md border border-ink-200 px-4 py-2 text-sm font-medium hover:bg-ink-50"
          >
            Home
          </Link>
        </div>
      </main>
    );
  }

  // Load courses for the institution scope dropdown.
  const institutionId = (
    profile as { institution_id?: number | null } | null
  )?.institution_id;
  const { data: courses } = await supabase
    .from("courses")
    .select("id, code, name, slug")
    .eq("institution_id", institutionId ?? -1)
    .order("code");

  return (
    <main className="hero-bg">
      <section className="mx-auto max-w-5xl px-6 py-12">
        <div className="mb-8 flex items-baseline justify-between">
          <div>
            <div className="text-sm font-mono uppercase tracking-wider text-brand-600">
              author a question
            </div>
            <h1 className="display mt-1 text-3xl font-semibold">
              Add to the commons
            </h1>
            <p className="mt-2 text-sm text-ink-500">
              Submitted as a draft. Moderators review before it goes live, with
              full attribution to you.
            </p>
          </div>
        </div>

        <AuthorForm
          courses={(courses ?? []).map((c) => ({
            id: c.id as number,
            code: c.code as string,
            name: c.name as string,
            slug: c.slug as string,
          }))}
        />
      </section>
    </main>
  );
}
