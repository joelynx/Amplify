"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

export function ResolveButton({ reportId }: { reportId: string | number }) {
  const router = useRouter();
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string>("");

  async function onClick() {
    setBusy(true);
    setErr("");
    const res = await fetch(`/api/reports/${reportId}/resolve`, {
      method: "POST",
    });
    if (!res.ok) {
      const j = await res.json().catch(() => ({}));
      setErr(j.error || `HTTP ${res.status}`);
      setBusy(false);
      return;
    }
    router.refresh();
  }

  return (
    <div className="flex flex-col items-end gap-1">
      <button
        type="button"
        onClick={onClick}
        disabled={busy}
        className="rounded-md border border-emerald-300 bg-emerald-50 px-3 py-1 text-xs text-emerald-800 hover:bg-emerald-100 disabled:opacity-50"
      >
        {busy ? "Resolving…" : "Resolve"}
      </button>
      {err && <span className="text-xs text-red-600">{err}</span>}
    </div>
  );
}
