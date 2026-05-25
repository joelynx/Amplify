/**
 * The Generate page — spec §8.1.
 *
 * Composition strategy: keep state in the Zustand store (`useGenerateStore`),
 * derive `Filters` via `draftToFilters`, and fan it out to:
 *   - live count (`count_matching_questions`, debounced 150ms)
 *   - dynamic tag / source / type dropdowns (spec §7.3 — re-query on every change)
 *
 * Generate / Export / Save Template are no-ops in this step; the action row
 * shows a validation tooltip when the form isn't ready to generate.
 */

import { useEffect, useMemo, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";


import { Card } from "../components/ui/Card";
import { Button } from "../components/ui/Button";
import { Modal } from "../components/ui/Modal";
import { CheckableTree } from "../components/generate/CheckableTree";
import { TagTray } from "../components/generate/TagTray";
import { ChipTray } from "../components/generate/ChipTray";
import { SubjectPicker } from "../components/generate/SubjectPicker";
import { TemplatePicker } from "../components/generate/TemplatePicker";
import { OutputSettings } from "../components/generate/OutputSettings";
import { ActionRow } from "../components/generate/ActionRow";
import { StatusBar } from "../components/generate/StatusBar";
import { NameDialog } from "../components/generate/NameDialog";
import { TemplateManager } from "../components/generate/TemplateManager";
import { useDebounced } from "../lib/debounce";
import {
  ipc,
  type ConceptTree,
  type ExportResult,
  type GenerateResult,
  type TemplatePayload,
} from "../lib/ipc";
import {
  draftEqualsTemplate,
  draftToFilters,
  draftToOutputSettings,
  draftToTemplate,
  templateSubtopicsToLeaves,
  useGenerateStore,
} from "../state/generate";

export default function GeneratePage() {
  const draft = useGenerateStore();

  // --- async lookups -------------------------------------------------
  const [subjects, setSubjects] = useState<string[]>([]);
  const [templates, setTemplates] = useState<string[]>([]);
  const [tree, setTree] = useState<ConceptTree>({});
  const [tags, setTags] = useState<string[]>([]);
  const [sources, setSources] = useState<string[]>([]);
  const [types, setTypes] = useState<string[]>([]);
  const [count, setCount] = useState<number | null>(null);
  const [countLoading, setCountLoading] = useState(false);
  const [countError, setCountError] = useState<string | null>(null);

  // Bootstrap: subjects, templates, default config, plus the initial tree.
  useEffect(() => {
    let cancelled = false;
    (async () => {
      const [subs, tmpls, defaultN, savedDir, activeSubject] = await Promise.all([
        ipc.list_subjects(),
        ipc.list_templates(),
        ipc.get_config("DEFAULT_NO_QUESTIONS"),
        ipc.get_config("FILE_SAVE_LOCATION"),
        ipc.get_active_subject(),
      ]);
      if (cancelled) return;
      setSubjects(subs);
      setTemplates(tmpls);
      if (typeof defaultN === "number") draft.setNQuestions(defaultN);
      if (typeof savedDir === "string") draft.setSaveDirectory(savedDir);
      // Spec §8.1: Subject combobox "defaults to active subject". Only default
      // when the form looks untouched — otherwise we'd clobber a template /
      // generate-similar selection that already populated the draft.
      if (
        activeSubject &&
        draft.subject === null &&
        draft.selectedLeaves.size === 0 &&
        draft.templateName === null
      ) {
        draft.setSubject(activeSubject);
      }
    })();
    return () => {
      cancelled = true;
    };
    // bootstrap is intentionally a one-shot
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Concept tree depends on the subject (which scopes the curricular boundary).
  useEffect(() => {
    let cancelled = false;
    (async () => {
      const t = await ipc.get_concept_tree(draft.subject, draft.inSyllabusOnly);
      if (!cancelled) setTree(t);
    })();
    return () => {
      cancelled = true;
    };
  }, [draft.subject, draft.inSyllabusOnly]);

  // Spec §7.3: tag / source / type dropdowns re-query on every relevant change.
  // Debounce the heavy ones so rapid edits don't thrash IPC.
  const filters = useMemo(() => draftToFilters(draft), [draft]);
  const debouncedFilters = useDebounced(filters, 150);

  // Live count.
  useEffect(() => {
    let cancelled = false;
    setCountLoading(true);
    setCountError(null);
    ipc
      .count_matching_questions(debouncedFilters)
      .then((n) => {
        if (!cancelled) setCount(n);
      })
      .catch((e: unknown) => {
        if (!cancelled) setCountError(e instanceof Error ? e.message : String(e));
      })
      .finally(() => {
        if (!cancelled) setCountLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [debouncedFilters]);

  // Dynamic tag / source / type lists — every dropdown re-queries with the
  // current filters (spec §7.3). Backend strips the self-key from filters so
  // the offerings are "what would still match if you added this option".
  useEffect(() => {
    let cancelled = false;
    Promise.all([
      ipc.get_all_tags(debouncedFilters),
      ipc.get_sources(debouncedFilters),
      ipc.get_types(debouncedFilters),
    ]).then(([t, s, ty]) => {
      if (cancelled) return;
      setTags(t);
      setSources(s);
      setTypes(ty);
    });
    return () => {
      cancelled = true;
    };
  }, [debouncedFilters]);

  // --- generation state --------------------------------------------
  const [busy, setBusy] = useState<"idle" | "generating" | "exporting">("idle");
  const [generateResult, setGenerateResult] = useState<GenerateResult | null>(null);
  const [exportResult, setExportResult] = useState<ExportResult | null>(null);

  // --- template state ----------------------------------------------
  const [loadedTemplate, setLoadedTemplate] = useState<TemplatePayload | null>(null);
  const [saveDialogOpen, setSaveDialogOpen] = useState(false);
  const [managerOpen, setManagerOpen] = useState(false);

  const refreshTemplates = async () => {
    const list = await ipc.list_templates();
    setTemplates(list);
  };

  const applyPayload = (payload: TemplatePayload) => {
    // Order matters: setSubject() clears leaves+tags, so call it before
    // populating them.
    draft.setSubject(payload.subject);
    const leaves = templateSubtopicsToLeaves(payload.subtopic_list, tree);
    draft.clearLeaves();
    draft.setLeavesBulk(Array.from(leaves), true);
    draft.clearTags();
    for (const t of payload.tag_list.compulsory) draft.addTag(t, "compulsory");
    for (const t of payload.tag_list.optional) draft.addTag(t, "optional");
    for (const t of payload.tag_list.excluded) draft.addTag(t, "excluded");
    draft.setSources(payload.source_list);
    draft.setTypes(payload.type_list);
    draft.setNQuestions(payload.n_questions);
    draft.setReuseQuestions(payload.reuse_questions);
    draft.setIncludeSources(payload.include_sources);
    draft.setInSyllabusOnly(payload.in_syllabus_only);
    if (payload.min_difficulty != null) draft.setMinDifficulty(payload.min_difficulty);
    if (payload.save_directory) draft.setSaveDirectory(payload.save_directory);
    if (payload.solutions) {
      draft.setSolutions(payload.solutions as Parameters<typeof draft.setSolutions>[0]);
    }
  };

  const handleSelectTemplate = async (name: string | null) => {
    draft.setTemplate(name);
    if (!name) {
      setLoadedTemplate(null);
      return;
    }
    const payload = await ipc.load_template(name);
    if (!payload) return;
    setLoadedTemplate(payload);
    applyPayload(payload);
  };

  // Generate similar: another page navigated here with a TemplatePayload in
  // location state. Apply it once, then clear the state so subsequent
  // navigations don't re-apply.
  const location = useLocation();
  const navigate = useNavigate();
  const navState = location.state as
    | { template?: TemplatePayload; questionIds?: number[] }
    | null;
  const pendingTemplate = navState?.template;
  const pendingQuestionIds = navState?.questionIds;

  useEffect(() => {
    if (!pendingTemplate) return;
    if (Object.keys(tree).length === 0) return;
    applyPayload(pendingTemplate);
    draft.setTemplate(null);
    setLoadedTemplate(null);
    navigate("/generate", { replace: true, state: null });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pendingTemplate, tree]);

  useEffect(() => {
    if (!pendingQuestionIds || pendingQuestionIds.length === 0) return;
    draft.setSpecificQuestionIds(pendingQuestionIds);
    draft.setNQuestions(pendingQuestionIds.length);
    navigate("/generate", { replace: true, state: null });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pendingQuestionIds]);

  const handleSaveTemplate = () => setSaveDialogOpen(true);

  const handleSaveDialogConfirm = async (name: string) => {
    const payload = draftToTemplate(draft, name);
    await ipc.save_template(name, payload);
    setSaveDialogOpen(false);
    setLoadedTemplate(payload);
    draft.setTemplate(name);
    await refreshTemplates();
  };

  // Save Template button greys when the form draft *exactly* matches the
  // currently-loaded template (spec §8.1). Also greys when there's no
  // selection at all — saving an empty template isn't useful.
  const saveTemplateDisabled =
    draft.selectedLeaves.size === 0 ||
    (loadedTemplate !== null && draftEqualsTemplate(draft, loadedTemplate));

  // --- validation ---------------------------------------------------
  const inSelectionMode = draft.specificQuestionIds.length > 0;
  const generateDisabledReason = useMemo<string | null>(() => {
    if (busy !== "idle") return "Working…";
    if (inSelectionMode) {
      if (draft.nQuestions < 1) return "Set the question count to at least 1";
      if (!draft.saveDirectory) return "Choose a save directory";
      return null;
    }
    if (draft.selectedLeaves.size === 0) return "Pick at least one subtopic from the tree";
    if (draft.nQuestions < 1) return "Set the question count to at least 1";
    if (!draft.saveDirectory) return "Choose a save directory";
    return null;
  }, [busy, inSelectionMode, draft.selectedLeaves, draft.nQuestions, draft.saveDirectory]);

  const handleGenerate = async () => {
    setBusy("generating");
    try {
      const result = await ipc.generate_pdf(draftToFilters(draft), draftToOutputSettings(draft));
      setGenerateResult(result);
    } catch (e) {
      setGenerateResult({ success: false, errors: e instanceof Error ? e.message : String(e) });
    } finally {
      setBusy("idle");
    }
  };

  const handleExport = async () => {
    setBusy("exporting");
    try {
      const result = await ipc.export_tex(draftToFilters(draft), draftToOutputSettings(draft));
      setExportResult(result);
    } catch (e) {
      setExportResult({ success: false, errors: e instanceof Error ? e.message : String(e) });
    } finally {
      setBusy("idle");
    }
  };

  return (
    <div className="flex h-full flex-col">
      <main className="flex-1 overflow-y-auto">
        <div className="mx-auto flex max-w-5xl flex-col gap-4 px-6 py-6">
          <header>
            <h1 className="text-2xl font-semibold">Generate</h1>
            <p className="text-sm text-muted">
              Compose filters, watch the live count, then generate a PDF.
            </p>
          </header>

          {inSelectionMode && (
            <div className="flex items-center justify-between gap-3 rounded-md border border-primary/40 bg-primary/5 px-4 py-2 text-sm">
              <span>
                Using <strong>{draft.specificQuestionIds.length}</strong> specific question
                {draft.specificQuestionIds.length === 1 ? "" : "s"} from Browser. Tree / tag /
                filter controls are bypassed.
              </span>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => draft.setSpecificQuestionIds([])}
              >
                Clear selection
              </Button>
            </div>
          )}

          <Card title="Required">
            <div className="grid gap-3 sm:grid-cols-2">
              <label className="flex flex-col gap-1 text-sm">
                <span className="text-muted">Template</span>
                <TemplatePicker
                  templates={templates}
                  value={draft.templateName}
                  onChange={handleSelectTemplate}
                  onOpenManager={() => setManagerOpen(true)}
                />
              </label>
              <label className="flex flex-col gap-1 text-sm">
                <span className="text-muted">Subject</span>
                <SubjectPicker
                  subjects={subjects}
                  value={draft.subject}
                  onChange={draft.setSubject}
                />
              </label>
            </div>
          </Card>

          <Card title="Topics / Branches / Subtopics">
            <CheckableTree tree={tree} />
          </Card>

          <Card title="Tags">
            <TagTray available={tags} />
          </Card>

          <div className="grid gap-4 lg:grid-cols-2">
            <Card title="Sources">
              <ChipTray
                available={sources}
                selected={draft.sources}
                onChange={draft.setSources}
                placeholder="Add a source…"
                searchPlaceholder="Search sources"
                emptyMessage={sources.length === 0 ? "No sources available" : "All sources added"}
              />
            </Card>
            <Card title="Types">
              <ChipTray
                available={types}
                selected={draft.types}
                onChange={draft.setTypes}
                placeholder="Add a question type…"
                searchPlaceholder="Search types"
                emptyMessage={types.length === 0 ? "No types available" : "All types added"}
              />
            </Card>
          </div>

          <Card title="Output settings">
            <OutputSettings />
          </Card>

          <Card title="Actions">
            <ActionRow
              saveTemplateDisabled={saveTemplateDisabled}
              generateDisabledReason={generateDisabledReason}
              onSaveTemplate={handleSaveTemplate}
              onExportLatex={handleExport}
              onGenerate={handleGenerate}
            />
          </Card>
        </div>
      </main>
      <StatusBar count={count} loading={countLoading} error={countError} />
      <GenerateResultModal result={generateResult} onClose={() => setGenerateResult(null)} />
      <ExportResultModal result={exportResult} onClose={() => setExportResult(null)} />
      <NameDialog
        open={saveDialogOpen}
        title="Save template"
        initialValue={loadedTemplate?.name ?? ""}
        takenNames={templates.filter((n) => n !== loadedTemplate?.name)}
        confirmLabel="Save"
        onCancel={() => setSaveDialogOpen(false)}
        onConfirm={handleSaveDialogConfirm}
      />
      <TemplateManager
        open={managerOpen}
        onClose={() => setManagerOpen(false)}
        templates={templates}
        onChange={refreshTemplates}
        loadedName={loadedTemplate?.name ?? null}
        onLoadedRenamed={(newName) => {
          setLoadedTemplate((t) => (t ? { ...t, name: newName } : t));
          draft.setTemplate(newName);
        }}
        onLoadedDeleted={() => {
          setLoadedTemplate(null);
          draft.setTemplate(null);
        }}
      />
    </div>
  );
}

function GenerateResultModal({
  result,
  onClose,
}: {
  result: GenerateResult | null;
  onClose: () => void;
}) {
  if (!result) return null;
  const open = result.path != null && result.success;
  const fellBack = !result.success && result.fallback != null;

  if (result.success) {
    return (
      <Modal
        open
        onClose={onClose}
        title="PDF generated"
        tone="success"
        footer={
          <>
            {result.path && (
              <Button variant="outline" onClick={() => ipc.open_file(result.path!)}>
                Open PDF
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
        {result.shortfall != null && result.shortfall > 0 && (
          <p className="mt-2 text-warning">
            Note: the filter matched fewer questions than requested ({result.shortfall} short).
          </p>
        )}
        {void open}
      </Modal>
    );
  }

  return (
    <Modal
      open
      onClose={onClose}
      title={fellBack ? "Compile failed — .tex fallback saved" : "Generate failed"}
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
      {fellBack && result.fallback && (
        <p className="mb-2">
          Fallback saved to <code className="font-mono break-all">{result.fallback}</code>
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

function ExportResultModal({
  result,
  onClose,
}: {
  result: ExportResult | null;
  onClose: () => void;
}) {
  if (!result) return null;
  if (result.success) {
    return (
      <Modal
        open
        onClose={onClose}
        title="LaTeX exported"
        tone="success"
        footer={
          <>
            {result.path && (
              <Button variant="outline" onClick={() => ipc.open_file(result.path!)}>
                Open .tex
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
      title="Export failed"
      tone="error"
      footer={
        <Button variant="primary" onClick={onClose}>
          OK
        </Button>
      }
    >
      <p>{result.errors}</p>
    </Modal>
  );
}
