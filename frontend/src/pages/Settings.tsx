/**
 * Settings page — spec §8.7. Four cards:
 *   1. Reset DB Data (Reset Subject + Factory Reset)
 *   2. General (font size, default # questions, default save dir, active theme,
 *      Restart App, Global mute)
 *   3. PDF Output (Left/Right header, Title, Instructions — each validated
 *      through the appropriate sanitizer; image-mode for headers; Save/Cancel/
 *      Reset to Defaults)
 *   4. Data (Re-run Seed Ingest, Augment from CSV, diagnostics)
 */

import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Brain, FolderOpen, ImagePlus, RotateCw, Tag, Trash2, Upload } from "lucide-react";

import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { Input } from "../components/ui/Input";
import { Modal } from "../components/ui/Modal";
import { NumberInput } from "../components/ui/NumberInput";
import { Switch } from "../components/ui/Switch";
import {
  ipc,
  type AugmentResult,
  type DifficultyState,
  type IngestResult,
  type RecomputeDifficultyResult,
  type ResetSubjectResult,
  type SeedDiagnostics,
  type SeedTagsResult,
} from "../lib/ipc";

interface PdfHeaders {
  left: string;
  right: string;
  title: string;
  instructions: string;
}

interface HeaderErrors {
  left: string | null;
  right: string | null;
  title: string | null;
  instructions: string | null;
}

const DEFAULT_PDF: PdfHeaders = {
  left: "<S>",
  right: "<d>",
  title: "<T>",
  instructions: "",
};

const IMAGE_PREFIX = "\\includegraphics[width=1cm]{";

function isImageHeader(value: string): boolean {
  return value.startsWith(IMAGE_PREFIX);
}

export default function SettingsPage() {
  // General
  const [defaultN, setDefaultN] = useState<number>(10);
  const [saveDir, setSaveDir] = useState<string>("");
  const [activeTheme, setActiveTheme] = useState<string>("");
  const [globalMute, setGlobalMute] = useState<boolean>(false);

  // PDF Output
  const [pdf, setPdf] = useState<PdfHeaders>(DEFAULT_PDF);
  const [pdfSaved, setPdfSaved] = useState<PdfHeaders>(DEFAULT_PDF);
  const [pdfErrors, setPdfErrors] = useState<HeaderErrors>({
    left: null,
    right: null,
    title: null,
    instructions: null,
  });

  // Data card
  const [diag, setDiag] = useState<SeedDiagnostics | null>(null);
  const [ingestResult, setIngestResult] = useState<IngestResult | null>(null);
  const [augmentResult, setAugmentResult] = useState<AugmentResult | null>(null);
  const [seedTagsResult, setSeedTagsResult] = useState<SeedTagsResult | null>(null);
  const [diff, setDiff] = useState<DifficultyState | null>(null);
  const [recomputeResult, setRecomputeResult] = useState<RecomputeDifficultyResult | null>(null);
  const navigate = useNavigate();
  const [subjectReset, setSubjectReset] = useState<ResetSubjectResult | null>(null);
  const [factoryConfirm, setFactoryConfirm] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    const [n, sd, theme, mute, l, r, t, ins, d] = await Promise.all([
      ipc.get_config("DEFAULT_NO_QUESTIONS"),
      ipc.get_config("FILE_SAVE_LOCATION"),
      ipc.get_config("THEME_SELECTED"),
      ipc.get_config("GLOBAL_MUTE"),
      ipc.get_config("PDF_LEFT_HEADER"),
      ipc.get_config("PDF_RIGHT_HEADER"),
      ipc.get_config("PDF_TITLE_LINE"),
      ipc.get_config("PDF_INSTRUCTIONS"),
      ipc.get_seed_diagnostics(),
    ]);
    if (typeof n === "number") setDefaultN(n);
    if (typeof sd === "string") setSaveDir(sd);
    if (typeof theme === "string") setActiveTheme(theme);
    if (typeof mute === "boolean") setGlobalMute(mute);
    const headers = {
      left: typeof l === "string" ? l : "",
      right: typeof r === "string" ? r : "",
      title: typeof t === "string" ? t : "",
      instructions: typeof ins === "string" ? ins : "",
    };
    setPdf(headers);
    setPdfSaved(headers);
    setDiag(d);
    const ds = await ipc.get_difficulty_state();
    setDiff(ds);
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  // Header validation (debounced via React's update cycle; for now we validate
  // on every keystroke via async IPC — cheap and gives instant feedback).
  useEffect(() => {
    let cancelled = false;
    (async () => {
      const [le, re, te, ie] = await Promise.all([
        ipc.validate_header_text(pdf.left, "basic"),
        ipc.validate_header_text(pdf.right, "basic"),
        ipc.validate_header_text(pdf.title, "extended"),
        ipc.validate_header_text(pdf.instructions, "extended"),
      ]);
      if (!cancelled) setPdfErrors({ left: le, right: re, title: te, instructions: ie });
    })();
    return () => {
      cancelled = true;
    };
  }, [pdf]);

  const anyHeaderError =
    pdfErrors.left || pdfErrors.right || pdfErrors.title || pdfErrors.instructions;

  // --- General -----------------------------------------------------

  const onDefaultNChange = async (v: number) => {
    setDefaultN(v);
    await ipc.set_config("DEFAULT_NO_QUESTIONS", v);
  };

  const onPickSaveDir = async () => {
    const path = await ipc.pick_save_directory();
    if (path) {
      setSaveDir(path);
      await ipc.set_config("FILE_SAVE_LOCATION", path);
    }
  };

  const onMuteChange = async (v: boolean) => {
    setGlobalMute(v);
    await ipc.set_config("GLOBAL_MUTE", v);
  };

  const onRestart = async () => {
    try {
      await ipc.restart_app();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  };

  // --- PDF headers -------------------------------------------------

  const onPickImage = async (field: keyof PdfHeaders) => {
    const path = await ipc.pick_image_file();
    if (!path) return;
    setPdf((p) => ({ ...p, [field]: `${IMAGE_PREFIX}${path}}` }));
  };

  const clearImage = (field: keyof PdfHeaders) => setPdf((p) => ({ ...p, [field]: "" }));

  const onSavePdf = async () => {
    if (anyHeaderError) {
      setError("Fix validation errors before saving.");
      return;
    }
    await Promise.all([
      ipc.set_config("PDF_LEFT_HEADER", pdf.left),
      ipc.set_config("PDF_RIGHT_HEADER", pdf.right),
      ipc.set_config("PDF_TITLE_LINE", pdf.title),
      ipc.set_config("PDF_INSTRUCTIONS", pdf.instructions),
    ]);
    setPdfSaved(pdf);
  };

  const pdfDirty =
    pdf.left !== pdfSaved.left ||
    pdf.right !== pdfSaved.right ||
    pdf.title !== pdfSaved.title ||
    pdf.instructions !== pdfSaved.instructions;

  // --- Reset DB Data -----------------------------------------------

  const onResetSubject = async () => {
    setError(null);
    setBusy("reset-subject");
    try {
      const r = await ipc.reset_active_subject();
      setSubjectReset(r);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(null);
    }
  };

  const onFactoryReset = async () => {
    setError(null);
    setBusy("factory");
    try {
      await ipc.factory_reset();
      setFactoryConfirm(false);
      // Spec says factory_reset restarts; trigger that here.
      await ipc.restart_app();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(null);
    }
  };

  // --- Data card ---------------------------------------------------

  const onReingest = async () => {
    setBusy("ingest");
    try {
      const r = await ipc.run_seed_ingest();
      setIngestResult(r);
      await refresh();
    } finally {
      setBusy(null);
    }
  };

  const onAugment = async () => {
    const path = await ipc.pick_csv_file();
    if (!path) return;
    setBusy("augment");
    try {
      const r = await ipc.augment_seed_from_csv(path);
      setAugmentResult(r);
      await refresh();
    } finally {
      setBusy(null);
    }
  };

  const onSeedTags = async () => {
    setBusy("seed-tags");
    try {
      const r = await ipc.seed_tags_from_metadata();
      setSeedTagsResult(r);
      await refresh();
    } finally {
      setBusy(null);
    }
  };

  const onSmartDifficultyToggle = async (on: boolean) => {
    await ipc.set_smart_difficulty_enabled(on);
    setDiff((prev) => (prev ? { ...prev, enabled: on } : prev));
  };

  const onRecomputeDifficulty = async () => {
    setBusy("difficulty");
    try {
      const r = await ipc.recompute_difficulty();
      setRecomputeResult(r);
    } finally {
      setBusy(null);
    }
  };

  return (
    <main className="h-full overflow-y-auto">
      <div className="mx-auto max-w-3xl space-y-4 px-6 py-6">
        <header>
          <h1 className="text-2xl font-semibold">Settings</h1>
          {error && <p className="text-sm text-error">{error}</p>}
        </header>

        {/* Reset DB Data */}
        <Card title="Reset DB Data">
          <div className="flex flex-wrap gap-2">
            <Button variant="outline" onClick={onResetSubject} disabled={busy !== null}>
              <RotateCw className="h-4 w-4" />
              Reset active subject usage
            </Button>
            <Button
              variant="outline"
              onClick={() => setFactoryConfirm(true)}
              disabled={busy !== null}
            >
              <Trash2 className="h-4 w-4 text-error" />
              Factory reset…
            </Button>
          </div>
          <p className="mt-2 text-xs text-muted">
            Reset subject zeroes <code>times_used</code> for questions in the active subject's
            scope. Factory reset wipes psets, templates, quizzes, subjects, and configs — question
            content (bodies, solutions, embeddings, outlines) is preserved.
          </p>
        </Card>

        {/* General */}
        <Card title="General">
          <div className="space-y-3">
            <Row label="Default number of questions">
              <NumberInput value={defaultN} onChange={onDefaultNChange} min={1} max={200} />
            </Row>
            <Row label="Default save location">
              <div className="flex flex-1 items-center gap-2">
                <div className="flex-1 truncate rounded-md border border-border bg-background px-3 py-1.5 text-sm">
                  {saveDir || <span className="text-muted">Not set</span>}
                </div>
                <Button variant="outline" size="sm" onClick={onPickSaveDir}>
                  <FolderOpen className="h-4 w-4" />
                  Browse…
                </Button>
              </div>
            </Row>
            <Row label="Active theme">
              <span className="text-sm">{activeTheme || "default-light"}</span>
            </Row>
            <Row label="Global mute (sound effects)">
              <Switch checked={globalMute} onCheckedChange={onMuteChange} />
            </Row>
            <Row label="">
              <Button variant="outline" onClick={onRestart}>
                <RotateCw className="h-4 w-4" />
                Restart App
              </Button>
            </Row>
          </div>
        </Card>

        {/* PDF Output */}
        <Card title="PDF Output">
          <div className="space-y-3">
            <HeaderField
              label="Left header"
              value={pdf.left}
              error={pdfErrors.left}
              level="basic"
              onChange={(v) => setPdf((p) => ({ ...p, left: v }))}
              onPickImage={() => onPickImage("left")}
              onClearImage={() => clearImage("left")}
            />
            <HeaderField
              label="Right header"
              value={pdf.right}
              error={pdfErrors.right}
              level="basic"
              onChange={(v) => setPdf((p) => ({ ...p, right: v }))}
              onPickImage={() => onPickImage("right")}
              onClearImage={() => clearImage("right")}
            />
            <HeaderField
              label="Title line"
              value={pdf.title}
              error={pdfErrors.title}
              level="extended"
              multiline
              onChange={(v) => setPdf((p) => ({ ...p, title: v }))}
            />
            <HeaderField
              label="Instructions"
              value={pdf.instructions}
              error={pdfErrors.instructions}
              level="extended"
              multiline
              onChange={(v) => setPdf((p) => ({ ...p, instructions: v }))}
            />
            <div className="flex flex-wrap gap-2 pt-1">
              <Button variant="primary" onClick={onSavePdf} disabled={!pdfDirty || !!anyHeaderError}>
                Save
              </Button>
              <Button variant="ghost" onClick={() => setPdf(pdfSaved)} disabled={!pdfDirty}>
                Cancel
              </Button>
              <Button variant="ghost" onClick={() => setPdf(DEFAULT_PDF)}>
                Reset to defaults
              </Button>
            </div>
            <p className="text-xs text-muted">
              Tokens: <code>&lt;S&gt;</code> subject · <code>&lt;T&gt;</code> topics ·{" "}
              <code>&lt;N&gt;</code> count · <code>&lt;K&gt;</code> sources · <code>&lt;Q&gt;</code>{" "}
              types · <code>&lt;P&gt;</code> pset id · <code>&lt;d&gt;</code> /{" "}
              <code>&lt;D&gt;</code> dates
            </p>
          </div>
        </Card>

        {/* Smart difficulty (Step 19) */}
        <Card title="Smart difficulty">
          <div className="space-y-3">
            <Row label="Enable smart difficulty (Phase 2)">
              <Switch
                checked={diff?.enabled ?? false}
                onCheckedChange={onSmartDifficultyToggle}
                ariaLabel="Enable smart difficulty"
              />
            </Row>
            <div className="flex flex-wrap gap-2">
              <Button variant="outline" onClick={onRecomputeDifficulty} disabled={busy !== null}>
                <RotateCw className={"h-4 w-4 " + (busy === "difficulty" ? "animate-spin" : "")} />
                Recompute smart difficulty
              </Button>
              <Button variant="outline" onClick={() => navigate("/difficulty/train")}>
                <Brain className="h-4 w-4" />
                Train pairwise…
              </Button>
            </div>
            {diff && (
              <p className="text-xs text-muted">
                {diff.topics_with_depth.length === 0 ? (
                  <>
                    <strong>TOPIC_DEPTH_MAP is empty</strong> — depth sub-score contributes 0; the
                    combiner auto-renormalizes over length + novelty.
                  </>
                ) : (
                  <>Depth values available for {diff.topics_with_depth.length} topic(s).</>
                )}
                {Object.keys(diff.weights_by_topic).length > 0 && (
                  <> Trained weights on {Object.keys(diff.weights_by_topic).length} topic(s).</>
                )}
              </p>
            )}
          </div>
        </Card>

        {/* Data */}
        <Card title="Data">
          <div className="space-y-3">
            <div className="flex flex-wrap gap-2">
              <Button variant="outline" onClick={onReingest} disabled={busy !== null}>
                <RotateCw className="h-4 w-4" />
                Re-run seed ingest
              </Button>
              <Button variant="outline" onClick={onAugment} disabled={busy !== null}>
                <Upload className="h-4 w-4" />
                Augment seed from CSV…
              </Button>
              <Button variant="outline" onClick={onSeedTags} disabled={busy !== null}>
                <Tag className="h-4 w-4" />
                Seed tags from metadata
              </Button>
            </div>
            {diag && (
              <div className="rounded-md border border-border bg-background p-3 text-sm">
                <div className="grid grid-cols-1 gap-1 sm:grid-cols-2">
                  <span className="text-muted">Embedding model</span>
                  <span className="font-mono">{diag.embed_model_version}</span>
                  <span className="text-muted">Questions total</span>
                  <span>{diag.questions_total}</span>
                  <span className="text-muted">With embeddings</span>
                  <span>
                    {diag.questions_with_embeddings} / {diag.questions_total}
                  </span>
                  <span className="text-muted">With outlines</span>
                  <span>
                    {diag.questions_with_outlines} / {diag.questions_total}
                  </span>
                </div>
              </div>
            )}
          </div>
        </Card>
      </div>

      {/* --- Modals --- */}
      <Modal
        open={factoryConfirm}
        onClose={() => setFactoryConfirm(false)}
        title="Factory reset?"
        tone="error"
        footer={
          <>
            <Button variant="ghost" onClick={() => setFactoryConfirm(false)}>
              Cancel
            </Button>
            <Button variant="primary" onClick={onFactoryReset}>
              Reset and restart
            </Button>
          </>
        }
      >
        <p>
          Wipes psets, templates, quizzes, subjects, and configs. The question bank
          (bodies, solutions, tags, embeddings, outlines) stays intact. The app restarts
          when the reset finishes.
        </p>
      </Modal>

      <Modal
        open={subjectReset !== null}
        onClose={() => setSubjectReset(null)}
        title="Subject usage reset"
        tone="success"
        footer={
          <Button variant="primary" onClick={() => setSubjectReset(null)}>
            OK
          </Button>
        }
      >
        {subjectReset && (
          <p>
            Reset usage counters on <strong>{subjectReset.rows_reset.toLocaleString()}</strong>{" "}
            question{subjectReset.rows_reset === 1 ? "" : "s"} in{" "}
            <code className="font-mono">{subjectReset.subject}</code>.
          </p>
        )}
      </Modal>

      <Modal
        open={ingestResult !== null}
        onClose={() => setIngestResult(null)}
        title="Seed ingest complete"
        tone={ingestResult?.warnings?.length ? "default" : "success"}
        footer={
          <Button variant="primary" onClick={() => setIngestResult(null)}>
            OK
          </Button>
        }
      >
        {ingestResult && (
          <div className="space-y-2 text-sm">
            <p>
              Imported: <strong>{ingestResult.imported.toLocaleString()}</strong> · Skipped:{" "}
              <strong>{ingestResult.skipped.toLocaleString()}</strong> · Embeddings:{" "}
              <strong>{ingestResult.embeddings_loaded.toLocaleString()}</strong> · Outlines:{" "}
              <strong>{ingestResult.outlines_loaded.toLocaleString()}</strong>
            </p>
            {ingestResult.warnings?.length > 0 && (
              <div className="space-y-1 rounded-md border border-warning/30 bg-warning/5 p-2">
                <p className="text-xs font-semibold text-warning">Warnings</p>
                {ingestResult.warnings.map((w, i) => (
                  <p key={i} className="text-xs text-warning">
                    ⚠ {w}
                  </p>
                ))}
              </div>
            )}
          </div>
        )}
      </Modal>

      <Modal
        open={augmentResult !== null}
        onClose={() => setAugmentResult(null)}
        title="Augment from CSV"
        tone={augmentResult?.errors.length ? "error" : "success"}
        footer={
          <Button variant="primary" onClick={() => setAugmentResult(null)}>
            OK
          </Button>
        }
      >
        {augmentResult && (
          <div className="space-y-2 text-sm">
            <p>
              Added: <strong>{augmentResult.added}</strong> · Skipped:{" "}
              <strong>{augmentResult.skipped}</strong>
            </p>
            {augmentResult.errors.length > 0 && (
              <pre className="max-h-40 overflow-y-auto rounded-md bg-surface p-2 text-xs whitespace-pre-wrap">
                {augmentResult.errors.join("\n")}
              </pre>
            )}
            {augmentResult.warnings?.length > 0 && (
              <div className="space-y-1 rounded-md border border-warning/30 bg-warning/5 p-2">
                <p className="text-xs font-semibold text-warning">Warnings</p>
                {augmentResult.warnings.map((w, i) => (
                  <p key={i} className="text-xs text-warning">
                    ⚠ {w}
                  </p>
                ))}
              </div>
            )}
          </div>
        )}
      </Modal>

      <Modal
        open={recomputeResult !== null}
        onClose={() => setRecomputeResult(null)}
        title="Difficulty recomputed"
        tone="success"
        footer={
          <Button variant="primary" onClick={() => setRecomputeResult(null)}>
            OK
          </Button>
        }
      >
        {recomputeResult && (
          <p className="text-sm">
            Wrote ratings for <strong>{recomputeResult.updated.toLocaleString()}</strong> questions
            across <strong>{recomputeResult.topics_covered}</strong> topic(s).
            {recomputeResult.skipped > 0 && (
              <> Skipped <strong>{recomputeResult.skipped}</strong> (all sub-scores were 0).</>
            )}
            {recomputeResult.avg_rating != null && (
              <> Mean rating: <strong>{recomputeResult.avg_rating.toFixed(2)}</strong>.</>
            )}
          </p>
        )}
      </Modal>

      <Modal
        open={seedTagsResult !== null}
        onClose={() => setSeedTagsResult(null)}
        title="Tags seeded"
        tone="success"
        footer={
          <Button variant="primary" onClick={() => setSeedTagsResult(null)}>
            OK
          </Button>
        }
      >
        {seedTagsResult && (
          <p className="text-sm">
            Scanned <strong>{seedTagsResult.questions_scanned.toLocaleString()}</strong>{" "}
            questions; inserted <strong>{seedTagsResult.rows_inserted.toLocaleString()}</strong>{" "}
            new tag rows. Re-running only adds tags for new questions or new metadata.
          </p>
        )}
      </Modal>
    </main>
  );
}

function Row({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="flex flex-wrap items-center justify-between gap-3">
      {label ? <span className="min-w-[14rem] text-sm">{label}</span> : <span />}
      {children}
    </label>
  );
}

function HeaderField({
  label,
  value,
  error,
  level: _level,
  multiline,
  onChange,
  onPickImage,
  onClearImage,
}: {
  label: string;
  value: string;
  error: string | null;
  level: "basic" | "extended";
  multiline?: boolean;
  onChange: (v: string) => void;
  onPickImage?: () => void;
  onClearImage?: () => void;
}) {
  const isImage = isImageHeader(value);
  return (
    <div>
      <div className="flex items-center justify-between gap-2">
        <span className="text-sm text-muted">{label}</span>
        {onPickImage && (
          <div className="flex gap-1">
            {isImage ? (
              <Button variant="ghost" size="sm" onClick={onClearImage} aria-label="Clear image">
                <Trash2 className="h-4 w-4" />
              </Button>
            ) : (
              <Button variant="ghost" size="sm" onClick={onPickImage} aria-label="Pick image">
                <ImagePlus className="h-4 w-4" />
              </Button>
            )}
          </div>
        )}
      </div>
      {multiline ? (
        <textarea
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className="min-h-[3rem] w-full rounded-md border border-border bg-background px-3 py-2 text-sm outline-none focus-visible:ring-2 focus-visible:ring-primary"
          disabled={isImage}
        />
      ) : (
        <Input value={value} onChange={(e) => onChange(e.target.value)} disabled={isImage} />
      )}
      {error && <p className="mt-1 text-xs text-error">{error}</p>}
    </div>
  );
}
