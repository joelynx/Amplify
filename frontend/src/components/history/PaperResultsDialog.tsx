/**
 * "Record paper results" for a printed PSet (History). Per question: solved /
 * partial / missed, and whether a hint or the solution was used. Recorded
 * results join the practice history, so missed and assisted questions come
 * back in the review queue. Re-recording replaces a question's earlier result
 * for this PSet; clearing it removes the result.
 */

import { useEffect, useState } from "react";
import { createPortal } from "react-dom";
import { X } from "lucide-react";

import { Button } from "../ui/Button";
import { cn } from "../../lib/cn";
import { ipc, type PaperOutcome, type PaperQuestion } from "../../lib/ipc";

interface Props {
  psetId: string | null;
  onClose: () => void;
}

const OUTCOMES: { id: PaperOutcome; label: string; tone: string }[] = [
  { id: "solved", label: "Solved", tone: "border-success text-success" },
  { id: "partial", label: "Partial", tone: "border-warning text-warning" },
  { id: "missed", label: "Missed", tone: "border-error text-error" },
];

export function PaperResultsDialog({ psetId, onClose }: Props) {
  const [rows, setRows] = useState<PaperQuestion[] | null>(null);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    if (!psetId) return;
    setRows(null);
    setMessage(null);
    ipc.get_paper_results(psetId).then((r) => setRows(r.questions));
  }, [psetId]);

  if (!psetId) return null;

  const update = (qid: number, patch: Partial<PaperQuestion>) =>
    setRows((prev) => (prev ?? []).map((r) => (r.question_id === qid ? { ...r, ...patch } : r)));

  const save = async () => {
    if (!rows) return;
    setSaving(true);
    try {
      const res = await ipc.record_paper_results(
        psetId,
        rows.map((r) => ({ question_id: r.question_id, outcome: r.outcome, assisted: r.assisted })),
      );
      setMessage(`Recorded ${res.recorded} result${res.recorded === 1 ? "" : "s"}. Missed and assisted ones join your review queue.`);
    } catch (e) {
      setMessage(e instanceof Error ? e.message : String(e));
    } finally {
      setSaving(false);
    }
  };

  return createPortal(
    <div className="fixed inset-0 z-50 flex items-center justify-center" role="dialog" aria-modal="true">
      <div className="absolute inset-0 bg-black/40" onClick={onClose} />
      <div className="relative z-10 mx-4 flex max-h-[85vh] w-full max-w-3xl flex-col rounded-lg border border-border border-l-4 border-l-primary bg-background shadow-xl">
        <header className="flex items-center justify-between gap-2 border-b border-border p-4">
          <div>
            <h2 className="text-lg font-semibold">Record paper results</h2>
            <p className="font-mono text-xs text-muted">{psetId}</p>
          </div>
          <button type="button" onClick={onClose} className="rounded-md p-1 text-muted hover:bg-surface hover:text-text" aria-label="Close">
            <X className="h-4 w-4" />
          </button>
        </header>
        <div className="flex-1 overflow-y-auto p-4">
          {!rows ? (
            <p className="text-sm text-muted">Loading…</p>
          ) : rows.length === 0 ? (
            <p className="text-sm text-muted">This paper has no questions on record.</p>
          ) : (
            <ol className="space-y-2">
              {rows.map((r, i) => (
                <li key={r.question_id} className="flex flex-wrap items-center gap-3 rounded-md border border-border p-2 text-sm">
                  <span className="w-6 text-right font-mono text-muted">{i + 1}</span>
                  <span className="min-w-0 flex-1">
                    <span className="block truncate font-medium">
                      {r.topic} › {r.subtopic} <span className="font-mono text-xs text-muted">#{r.question_id}</span>
                    </span>
                    <span className="block truncate text-xs text-muted">{r.preview}</span>
                  </span>
                  <span className="flex gap-1">
                    {OUTCOMES.map((o) => (
                      <button
                        key={o.id}
                        type="button"
                        onClick={() => update(r.question_id, { outcome: r.outcome === o.id ? null : o.id })}
                        aria-pressed={r.outcome === o.id}
                        className={cn(
                          "rounded-md border px-2 py-1 text-xs font-medium",
                          r.outcome === o.id ? cn(o.tone, "bg-surface") : "border-border text-muted hover:text-text",
                        )}
                      >
                        {o.label}
                      </button>
                    ))}
                  </span>
                  <label className="flex items-center gap-1 text-xs text-muted" title="You used a hint or looked at the solution">
                    <input
                      type="checkbox"
                      checked={r.assisted}
                      onChange={(e) => update(r.question_id, { assisted: e.target.checked })}
                      className="h-3.5 w-3.5 rounded border-border"
                    />
                    with help
                  </label>
                </li>
              ))}
            </ol>
          )}
        </div>
        <footer className="flex items-center justify-end gap-3 border-t border-border p-4">
          {message && <span className="flex-1 text-xs text-muted">{message}</span>}
          <Button variant="ghost" onClick={onClose}>
            Close
          </Button>
          <Button variant="primary" onClick={() => void save()} disabled={saving || !rows || rows.length === 0}>
            Save results
          </Button>
        </footer>
      </div>
    </div>,
    document.body,
  );
}
