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

import { Card } from "../components/ui/Card";
import { CheckableTree } from "../components/generate/CheckableTree";
import { TagTray } from "../components/generate/TagTray";
import { ChipTray } from "../components/generate/ChipTray";
import { SubjectPicker } from "../components/generate/SubjectPicker";
import { TemplatePicker } from "../components/generate/TemplatePicker";
import { OutputSettings } from "../components/generate/OutputSettings";
import { ActionRow } from "../components/generate/ActionRow";
import { StatusBar } from "../components/generate/StatusBar";
import { useDebounced } from "../lib/debounce";
import { ipc, type ConceptTree } from "../lib/ipc";
import { draftToFilters, useGenerateStore } from "../state/generate";

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
      const [subs, tmpls, defaultN, savedDir] = await Promise.all([
        ipc.list_subjects(),
        ipc.list_templates(),
        ipc.get_config("DEFAULT_NO_QUESTIONS"),
        ipc.get_config("FILE_SAVE_LOCATION"),
      ]);
      if (cancelled) return;
      setSubjects(subs);
      setTemplates(tmpls);
      if (typeof defaultN === "number") draft.setNQuestions(defaultN);
      if (typeof savedDir === "string") draft.setSaveDirectory(savedDir);
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

  // Dynamic tag / source / type lists.
  useEffect(() => {
    let cancelled = false;
    Promise.all([
      ipc.get_all_tags(debouncedFilters),
      ipc.get_sources(),
      ipc.get_types(),
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

  // --- validation ---------------------------------------------------
  const generateDisabledReason = useMemo<string | null>(() => {
    if (draft.selectedLeaves.size === 0) return "Pick at least one subtopic from the tree";
    if (draft.nQuestions < 1) return "Set the question count to at least 1";
    if (!draft.saveDirectory) return "Choose a save directory";
    return null;
  }, [draft.selectedLeaves, draft.nQuestions, draft.saveDirectory]);

  // Save Template stays grey-only-when-equal once template payloads are wired
  // (Step 6). For now we disable it whenever there's no edits at all.
  const saveTemplateDisabled = useMemo(() => draft.selectedLeaves.size === 0, [draft.selectedLeaves]);

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

          <Card title="Required">
            <div className="grid gap-3 sm:grid-cols-2">
              <label className="flex flex-col gap-1 text-sm">
                <span className="text-muted">Template</span>
                <TemplatePicker
                  templates={templates}
                  value={draft.templateName}
                  onChange={draft.setTemplate}
                  onOpenManager={() => {
                    /* Step 6 wires the Template Manager dialog */
                  }}
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
              onSaveTemplate={() => {
                /* Step 6 wires save */
              }}
              onExportLatex={() => {
                /* Step 5 wires .tex export */
              }}
              onGenerate={() => {
                /* Step 5 wires PDF generation */
              }}
            />
          </Card>
        </div>
      </main>
      <StatusBar count={count} loading={countLoading} error={countError} />
    </div>
  );
}
