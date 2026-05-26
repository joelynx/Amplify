/**
 * The History page (spec §8.5).
 *
 * Lists every generated PSet newest-first. Per-row actions:
 *   - Open      → `ipc.open_pset_file(pset_id)` opens the saved PDF in the OS viewer.
 *   - Re-export → `ipc.re_export_pset_pdf(pset_id)` re-compiles the same questions
 *                 to the original `save_directory` (or current FILE_SAVE_LOCATION fallback).
 *   - Generate  → fetches `get_pset_filters` and navigates to /generate with the
 *     similar    payload in location.state. User reviews/edits before clicking
 *                 Generate; the new PSet stores the *edited* filters (no back-link).
 *   - Delete    → drops the psets row + pset_questions cascade. The on-disk PDF stays.
 */

import { useCallback, useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Download, ExternalLink, RefreshCw, Settings as Gear, Trash2, Wand2 } from "lucide-react";

import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { Modal } from "../components/ui/Modal";
import { StatsFiltersDialog } from "../components/stats/StatsFiltersDialog";
import {
  ipc,
  type DateRange,
  type GenerateResult,
  type PSetSummary,
  type QuizAttemptSummary,
} from "../lib/ipc";

function defaultRange(): DateRange {
  return { from: null, to: null };  // all-time by default; spec leaves this open for History
}

function formatRange(r: DateRange): string {
  if (!r.from && !r.to) return "all time";
  return `${r.from ?? "…"} → ${r.to ?? "…"}`;
}

function formatDate(iso: string): string {
  // psets.date_created is `YYYY-MM-DDTHH:MM:SSZ` — render local-ish without time zone fuss.
  return iso.replace("T", " ").replace("Z", " UTC");
}

export default function HistoryPage() {
  const navigate = useNavigate();
  const [subject, setSubject] = useState<string | null>(null);
  const [dateRange, setDateRange] = useState<DateRange>(defaultRange);
  const [filtersOpen, setFiltersOpen] = useState(false);

  const [subjects, setSubjects] = useState<string[]>([]);
  const [psets, setPsets] = useState<PSetSummary[]>([]);
  const [attempts, setAttempts] = useState<QuizAttemptSummary[]>([]);
  const [busy, setBusy] = useState<string | null>(null); // pset_id currently busy

  const [reExportResult, setReExportResult] = useState<GenerateResult | null>(null);
  const [openError, setOpenError] = useState<string | null>(null);
  const [confirmingDelete, setConfirmingDelete] = useState<PSetSummary | null>(null);

  useEffect(() => {
    ipc.list_subjects().then(setSubjects);
  }, []);

  const refresh = useCallback(async () => {
    const [rows, attemptRows] = await Promise.all([
      ipc.list_psets(subject, dateRange),
      ipc.list_quiz_attempts(subject, dateRange),
    ]);
    setPsets(rows);
    setAttempts(attemptRows);
  }, [subject, dateRange]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const handleOpen = async (pset: PSetSummary) => {
    setBusy(pset.pset_id);
    try {
      const r = await ipc.open_pset_file(pset.pset_id);
      if (!r.success) setOpenError(r.errors ?? "Open failed");
    } finally {
      setBusy(null);
    }
  };

  const handleReExport = async (pset: PSetSummary) => {
    setBusy(pset.pset_id);
    try {
      const r = await ipc.re_export_pset_pdf(pset.pset_id);
      setReExportResult(r);
    } finally {
      setBusy(null);
    }
  };

  const handleGenerateSimilar = async (pset: PSetSummary) => {
    setBusy(pset.pset_id);
    try {
      const payload = await ipc.get_pset_filters(pset.pset_id);
      if (!payload) return;
      navigate("/generate", { state: { template: payload } });
    } finally {
      setBusy(null);
    }
  };

  const handleDelete = async () => {
    if (!confirmingDelete) return;
    try {
      await ipc.delete_pset(confirmingDelete.pset_id);
      setConfirmingDelete(null);
      await refresh();
    } finally {
      setBusy(null);
    }
  };

  const empty = useMemo(() => psets.length === 0, [psets]);

  return (
    <div className="flex h-full flex-col overflow-hidden">
      <header className="flex items-center justify-between border-b border-border bg-surface px-6 py-3">
        <div>
          <h1 className="text-2xl font-semibold">History</h1>
          <p className="text-xs text-muted">
            {subject ?? "All subjects"} · {formatRange(dateRange)} · {psets.length} PSet
            {psets.length === 1 ? "" : "s"}
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={() => setFiltersOpen(true)}>
          <Gear className="h-4 w-4" />
          Filters
        </Button>
      </header>

      <main className="flex-1 overflow-y-auto">
        <div className="mx-auto max-w-5xl px-6 py-6">
          {empty ? (
            <Card>
              <p className="text-muted">No PSets match these filters yet.</p>
            </Card>
          ) : (
            <ul className="divide-y divide-border overflow-hidden rounded-lg border border-border bg-surface">
              {psets.map((p) => (
                <li
                  key={p.pset_id}
                  className="flex flex-col gap-2 px-4 py-3 sm:flex-row sm:items-center sm:justify-between"
                >
                  <div className="flex-1">
                    <div className="font-mono text-sm font-medium">{p.pset_id}</div>
                    <div className="mt-0.5 text-xs text-muted">
                      {formatDate(p.date_created)} ·{" "}
                      <span className="font-medium">
                        {p.subject ?? "(no subject)"}
                      </span>{" "}
                      · {p.n_questions} question{p.n_questions === 1 ? "" : "s"}
                      {p.template_name && <> · template <em>{p.template_name}</em></>}
                      {p.generation_mode && p.generation_mode !== "random" && (
                        <> · <span className="font-medium text-text">{p.generation_mode}</span>
                          {p.diversity_score != null && <> ({p.diversity_score.toFixed(2)})</>}
                        </>
                      )}
                    </div>
                  </div>
                  <div className="flex flex-wrap items-center gap-1">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleOpen(p)}
                      disabled={busy !== null}
                      aria-label={`Open ${p.pset_id}`}
                    >
                      <ExternalLink className="h-4 w-4" />
                      Open
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleReExport(p)}
                      disabled={busy !== null}
                      aria-label={`Re-export ${p.pset_id}`}
                    >
                      <RefreshCw className="h-4 w-4" />
                      Re-export
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleGenerateSimilar(p)}
                      disabled={busy !== null}
                      aria-label={`Generate similar to ${p.pset_id}`}
                    >
                      <Wand2 className="h-4 w-4" />
                      Generate similar
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => setConfirmingDelete(p)}
                      disabled={busy !== null}
                      aria-label={`Delete ${p.pset_id}`}
                    >
                      <Trash2 className="h-4 w-4 text-error" />
                      Delete
                    </Button>
                  </div>
                </li>
              ))}
            </ul>
          )}

          {attempts.length > 0 && (
            <section className="mt-8">
              <h2 className="mb-2 text-sm font-semibold uppercase tracking-wide text-muted">
                Quiz attempts ({attempts.length})
              </h2>
              <ul className="divide-y divide-border overflow-hidden rounded-lg border border-border bg-surface">
                {attempts.map((a) => (
                  <li
                    key={a.attempt_id}
                    className="flex flex-col gap-2 px-4 py-3 sm:flex-row sm:items-center sm:justify-between"
                  >
                    <div className="flex-1">
                      <div className="font-mono text-sm font-medium">{a.attempt_id}</div>
                      <div className="mt-0.5 text-xs text-muted">
                        {formatDate(a.date_started)} ·{" "}
                        <span className="font-medium">{a.subject ?? "(no subject)"}</span> ·{" "}
                        {a.n_questions} question{a.n_questions === 1 ? "" : "s"}
                        {a.template_name && <> · {a.template_name}</>}
                        {a.total_score != null && <> · score {a.total_score.toFixed(1)}</>}
                      </div>
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => navigate(`/quiz/review/${a.attempt_id}`)}
                    >
                      <Wand2 className="h-4 w-4" />
                      Review
                    </Button>
                  </li>
                ))}
              </ul>
            </section>
          )}
        </div>
      </main>

      <StatsFiltersDialog
        open={filtersOpen}
        onClose={() => setFiltersOpen(false)}
        initial={{ subject, dateRange }}
        subjects={subjects}
        onApply={(s, r) => {
          setSubject(s);
          setDateRange(r);
        }}
      />

      <Modal
        open={confirmingDelete !== null}
        onClose={() => setConfirmingDelete(null)}
        title="Delete PSet?"
        tone="error"
        footer={
          <>
            <Button variant="ghost" onClick={() => setConfirmingDelete(null)}>
              Cancel
            </Button>
            <Button variant="primary" onClick={handleDelete}>
              Delete
            </Button>
          </>
        }
      >
        <p>
          Remove <code className="font-mono">{confirmingDelete?.pset_id}</code> from history? The
          saved PDF stays on disk — only the database row is dropped.
        </p>
      </Modal>

      <ReExportResultModal
        result={reExportResult}
        onClose={() => setReExportResult(null)}
      />

      <Modal
        open={openError !== null}
        onClose={() => setOpenError(null)}
        title="Open failed"
        tone="error"
        footer={
          <Button variant="primary" onClick={() => setOpenError(null)}>
            OK
          </Button>
        }
      >
        <p>{openError}</p>
      </Modal>
    </div>
  );
}

function ReExportResultModal({
  result,
  onClose,
}: {
  result: GenerateResult | null;
  onClose: () => void;
}) {
  if (!result) return null;
  if (result.success) {
    return (
      <Modal
        open
        onClose={onClose}
        title="PDF re-exported"
        tone="success"
        footer={
          <>
            {result.path && (
              <Button variant="outline" onClick={() => ipc.open_file(result.path!)}>
                <Download className="h-4 w-4" />
                Open
              </Button>
            )}
            <Button variant="primary" onClick={onClose}>
              OK
            </Button>
          </>
        }
      >
        <p>
          Saved to <code className="font-mono break-all">{result.path}</code>
        </p>
      </Modal>
    );
  }
  return (
    <Modal
      open
      onClose={onClose}
      title="Re-export failed"
      tone="error"
      footer={
        <>
          {result.fallback && (
            <Button variant="outline" onClick={() => ipc.open_file(result.fallback!)}>
              Open .tex
            </Button>
          )}
          <Button variant="primary" onClick={onClose}>
            OK
          </Button>
        </>
      }
    >
      {result.fallback && (
        <p className="mb-2">
          Fallback at <code className="font-mono break-all">{result.fallback}</code>
        </p>
      )}
      {result.errors && (
        <pre className="max-h-40 overflow-y-auto rounded-md bg-surface p-2 text-xs whitespace-pre-wrap">
          {result.errors}
        </pre>
      )}
    </Modal>
  );
}
