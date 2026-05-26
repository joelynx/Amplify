"use client";

import { useState } from "react";
import { getBrowserSupabase } from "@/lib/supabase/browser";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [status, setStatus] = useState<"idle" | "sending" | "sent" | "error">(
    "idle"
  );
  const [errorMsg, setErrorMsg] = useState<string>("");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setStatus("sending");
    setErrorMsg("");

    const supabase = getBrowserSupabase();
    const { error } = await supabase.auth.signInWithOtp({
      email,
      options: {
        emailRedirectTo: `${window.location.origin}/auth/callback`,
      },
    });

    if (error) {
      setStatus("error");
      setErrorMsg(error.message);
      return;
    }
    setStatus("sent");
  }

  return (
    <main className="mx-auto flex min-h-screen max-w-md flex-col justify-center gap-6 px-6 py-16">
      <h1 className="text-3xl font-semibold tracking-tight">Sign in</h1>
      <p className="text-sm text-ink-500">
        We&apos;ll email you a magic link. No password required.
      </p>

      {status === "sent" ? (
        <div className="rounded-md border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-900">
          Check your inbox at <strong>{email}</strong>. Click the link to sign
          in.
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="flex flex-col gap-3">
          <input
            type="email"
            required
            autoComplete="email"
            placeholder="you@iitdabudhabi.ac.ae"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="rounded-md border border-ink-200 px-3 py-2 text-sm focus:border-ink-500 focus:outline-none"
          />
          <button
            type="submit"
            disabled={status === "sending"}
            className="rounded-md bg-ink-900 px-4 py-2 text-sm font-medium text-white hover:bg-ink-700 disabled:opacity-50"
          >
            {status === "sending" ? "Sending..." : "Send magic link"}
          </button>
          {status === "error" && (
            <p className="text-sm text-red-600">{errorMsg}</p>
          )}
        </form>
      )}
    </main>
  );
}
