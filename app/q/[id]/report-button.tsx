"use client";

import { useState } from "react";
import { Flag } from "lucide-react";

export function ReportButton({ questionId }: { questionId: number }) {
  const [open, setOpen] = useState(false);
  const [reason, setReason] = useState("");
  const [state, setState] = useState<
    "idle" | "submitting" | "done" | "auth" | "error"
  >("idle");

  async function submit() {
    setState("submitting");
    const res = await fetch(`/api/questions/${questionId}/report`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ reason }),
    });
    if (res.status === 401) {
      setState("auth");
      return;
    }
    if (!res.ok) {
      setState("error");
      return;
    }
    setState("done");
  }

  if (state === "done") {
    return (
      <span className="rounded-full border border-emerald-200 bg-emerald-50 px-2 py-1 text-xs text-emerald-700">
        flagged — thank you
      </span>
    );
  }

  return (
    <span className="relative">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="inline-flex items-center gap-1 rounded-full border border-ink-200 px-2 py-1 text-xs text-ink-500 hover:border-red-300 hover:text-red-700"
        title="Report this question"
      >
        <Flag className="h-3 w-3" />
        report
      </button>
      {open && (
        <div className="absolute right-0 top-full z-20 mt-1 w-64 rounded-md border border-ink-200 bg-white p-3 shadow-lg">
          <div className="mb-2 text-xs font-medium text-ink-700">
            What&apos;s wrong?
          </div>
          <textarea
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            rows={3}
            placeholder="Wrong answer, typo, ambiguous wording…"
            className="w-full rounded border border-ink-200 bg-white px-2 py-1 text-xs text-ink-900 placeholder:text-ink-400 focus:border-ink-500 focus:outline-none"
          />
          <div className="mt-2 flex justify-end gap-2">
            <button
              type="button"
              onClick={() => setOpen(false)}
              className="rounded px-2 py-1 text-xs text-ink-500 hover:text-ink-900"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={submit}
              disabled={state === "submitting"}
              className="rounded-md bg-ink-900 px-3 py-1 text-xs font-medium text-white hover:bg-ink-700 disabled:opacity-50"
            >
              {state === "submitting" ? "Sending…" : "Send"}
            </button>
          </div>
          {state === "auth" && (
            <p className="mt-2 text-xs text-red-600">
              Sign in to report.
            </p>
          )}
          {state === "error" && (
            <p className="mt-2 text-xs text-red-600">Couldn&apos;t send.</p>
          )}
        </div>
      )}
    </span>
  );
}
