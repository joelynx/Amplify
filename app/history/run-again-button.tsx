"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { getAnonKey } from "@/lib/anon";
import type { PracticeFilters } from "@/lib/db/types";

export function RunAgainButton({
  filters,
  nTarget,
  mode,
}: {
  filters: PracticeFilters;
  nTarget: number;
  mode: "random" | "diverse";
}) {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  async function onClick() {
    setLoading(true);
    setErr(null);
    try {
      const res = await fetch("/api/sessions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          filters,
          n_target: nTarget,
          mode,
          anon_key: getAnonKey(),
        }),
      });
      const json = await res.json();
      if (!res.ok || !json.session_id) {
        throw new Error(json.error ?? `HTTP ${res.status}`);
      }
      router.push(`/practice/${json.session_id}`);
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
      setLoading(false);
    }
  }

  return (
    <div className="flex flex-col items-end gap-1">
      <button
        type="button"
        onClick={onClick}
        disabled={loading}
        className="rounded-md bg-ink-900 px-3 py-1.5 text-xs font-medium text-white hover:bg-ink-700 disabled:opacity-50"
      >
        {loading ? "starting…" : "Run again"}
      </button>
      {err && <span className="text-[10px] text-red-600">{err}</span>}
    </div>
  );
}
