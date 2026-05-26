"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { getBrowserSupabase } from "@/lib/supabase/browser";

type Mode = "signin" | "signup";
type Role = "student" | "ta";

export default function LoginPage() {
  const router = useRouter();
  const [next, setNext] = useState<string>("/me");
  useEffect(() => {
    if (typeof window === "undefined") return;
    const sp = new URLSearchParams(window.location.search);
    const target = sp.get("next");
    if (target) setNext(target);
  }, []);

  const [mode, setMode] = useState<Mode>("signin");
  const [role, setRole] = useState<Role>("student");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string>("");

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    const supabase = getBrowserSupabase();
    try {
      if (mode === "signup") {
        const { error } = await supabase.auth.signUp({ email, password });
        if (error) throw error;
        const { error: signInError } =
          await supabase.auth.signInWithPassword({ email, password });
        if (signInError) throw signInError;
        // TA role → write 'faculty' on user_profiles via service-role endpoint.
        if (role === "ta") {
          await fetch("/api/auth/set-role", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ role: "faculty" }),
          });
        }
      } else {
        const { error } = await supabase.auth.signInWithPassword({
          email,
          password,
        });
        if (error) throw error;
      }
      // TAs land on the authoring page, students go to /me (or the ?next target).
      const landing =
        mode === "signup" && role === "ta" ? "/author" : next;
      router.push(landing);
      router.refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
      setBusy(false);
    }
  }

  return (
    <main className="mx-auto flex min-h-[calc(100vh-3rem)] max-w-md flex-col justify-center gap-6 px-6 py-16">
      <h1 className="text-3xl font-semibold tracking-tight">
        {mode === "signin" ? "Sign in" : "Create an account"}
      </h1>

      <div className="inline-flex self-start overflow-hidden rounded-md border border-ink-200 text-xs">
        <button
          type="button"
          onClick={() => {
            setMode("signin");
            setError("");
          }}
          className={`px-4 py-1.5 font-medium ${
            mode === "signin"
              ? "bg-ink-900 text-white"
              : "bg-white text-ink-700 hover:bg-ink-50"
          }`}
        >
          Sign in
        </button>
        <button
          type="button"
          onClick={() => {
            setMode("signup");
            setError("");
          }}
          className={`px-4 py-1.5 font-medium ${
            mode === "signup"
              ? "bg-ink-900 text-white"
              : "bg-white text-ink-700 hover:bg-ink-50"
          }`}
        >
          Sign up
        </button>
      </div>

      {mode === "signup" && (
        <div>
          <div className="mb-2 text-xs uppercase tracking-wider text-ink-500">
            I am a…
          </div>
          <div className="inline-flex overflow-hidden rounded-md border border-ink-200">
            {(["student", "ta"] as const).map((r) => (
              <button
                key={r}
                type="button"
                onClick={() => setRole(r)}
                className={
                  "px-4 py-1.5 text-xs font-medium " +
                  (role === r
                    ? "bg-ink-900 text-white"
                    : "bg-white text-ink-700 hover:bg-ink-50")
                }
              >
                {r === "student" ? "Student" : "TA / contributor"}
              </button>
            ))}
          </div>
          <p className="mt-2 text-xs text-ink-500">
            {role === "ta"
              ? "TAs contribute questions to the bank. Each submission is auto-embedded and added to the pool."
              : "Students get mastery tracking, practice sessions, and similarity search."}
          </p>
        </div>
      )}

      <form onSubmit={onSubmit} className="flex flex-col gap-3">
        <label className="flex flex-col gap-1 text-xs text-ink-500">
          Email
          <input
            type="email"
            required
            autoComplete="email"
            placeholder="you@example.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="rounded-md border border-ink-200 px-3 py-2 text-sm text-ink-900 focus:border-ink-500 focus:outline-none"
          />
        </label>
        <label className="flex flex-col gap-1 text-xs text-ink-500">
          Password
          <input
            type="password"
            required
            minLength={6}
            autoComplete={mode === "signin" ? "current-password" : "new-password"}
            placeholder={mode === "signin" ? "your password" : "at least 6 chars"}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="rounded-md border border-ink-200 px-3 py-2 text-sm text-ink-900 focus:border-ink-500 focus:outline-none"
          />
        </label>

        <button
          type="submit"
          disabled={busy}
          className="rounded-md bg-ink-900 px-4 py-2 text-sm font-medium text-white hover:bg-ink-700 disabled:opacity-50"
        >
          {busy
            ? mode === "signin" ? "Signing in…" : "Creating account…"
            : mode === "signin" ? "Sign in" : "Create account and continue"}
        </button>

        {error && (
          <p className="text-sm text-red-600">
            {error}
          </p>
        )}
      </form>

    </main>
  );
}
