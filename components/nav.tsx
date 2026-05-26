import Link from "next/link";
import { getServerSupabase } from "@/lib/supabase/server";
import { ThemeToggle } from "./theme-toggle";

export async function Nav() {
  const supabase = await getServerSupabase();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  let role: string | null = null;
  if (user) {
    const { data } = await supabase
      .from("user_profiles")
      .select("role")
      .eq("user_id", user.id)
      .maybeSingle();
    role = (data as { role?: string } | null)?.role ?? "student";
  }

  const isFaculty = role === "faculty" || role === "admin" || role === "moderator";

  return (
    <header className="sticky top-0 z-20 border-b border-ink-200 bg-white/80 backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-3">
        <Link
          href="/"
          className="flex items-center gap-2 text-base font-semibold tracking-tight"
        >
          <span className="inline-block size-5 rounded-md bg-ink-900 text-center text-xs font-bold leading-5 text-white">
            A
          </span>
          Amplify
        </Link>
        <nav className="flex items-center gap-1 text-sm">
          <NavLink href="/practice">Practice</NavLink>
          <NavLink href="/pbs">PBS</NavLink>
          <NavLink href="/q">Browse</NavLink>
          <NavLink href="/stats">Stats</NavLink>
          {user && <NavLink href="/history">History</NavLink>}
          <NavLink href="/tutorial">Tutorial</NavLink>
          <NavLink href="/about">About</NavLink>
          {isFaculty && <NavLink href="/faculty">Faculty</NavLink>}
          {user ? (
            <Link
              href="/me"
              className="ml-1 rounded-md border border-ink-200 px-3 py-1.5 text-ink-700 hover:bg-ink-50"
            >
              {user.email?.split("@")[0]}
            </Link>
          ) : (
            <Link
              href="/auth/login"
              className="ml-1 rounded-md bg-ink-900 px-3 py-1.5 text-white hover:bg-ink-700"
            >
              Sign in
            </Link>
          )}
          <ThemeToggle />
        </nav>
      </div>
    </header>
  );
}

function NavLink({ href, children }: { href: string; children: React.ReactNode }) {
  return (
    <Link
      href={href}
      className="rounded-md px-3 py-1.5 text-ink-700 hover:bg-ink-50"
    >
      {children}
    </Link>
  );
}
