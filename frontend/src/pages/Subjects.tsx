/**
 * The Subjects page — spec §8.2.
 *
 * Subjects are user-defined curricular bundles (alias Courses). The DB starts
 * empty; first one is user-created here (or imported as JSON). Activation is
 * "at most one active row" enforced by a partial-unique index (migration 001).
 *
 * Layout: left list (with active dot + action buttons), right editor (Name,
 * Description, topic picker, one InclusionTree per topic, Save/Activate/Deactivate).
 */

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  Copy,
  Download,
  Plus,
  Trash2,
  Upload,
} from "lucide-react";

import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { Combobox } from "../components/ui/Combobox";
import { Input } from "../components/ui/Input";
import { Modal } from "../components/ui/Modal";
import { InclusionTree } from "../components/subjects/InclusionTree";
import { ipc, type ConceptTree, type SubjectPayload } from "../lib/ipc";

interface EditorState {
  /** Name in the DB this editor row came from. Null when this is a new (unsaved) subject. */
  originalName: string | null;
  name: string;
  description: string;
  topics: string[];
  excludedBranches: Record<string, string[]>;
  excludedSubtopics: Record<string, Record<string, string[]>>;
}

const EMPTY_EDITOR: EditorState = {
  originalName: null,
  name: "",
  description: "",
  topics: [],
  excludedBranches: {},
  excludedSubtopics: {},
};

function payloadToEditor(p: SubjectPayload): EditorState {
  return {
    originalName: p.name,
    name: p.name,
    description: p.description ?? "",
    topics: p.topics ?? [],
    excludedBranches: p.excluded_branches ?? {},
    excludedSubtopics: p.excluded_subtopics ?? {},
  };
}

function editorToPayload(e: EditorState): SubjectPayload {
  return {
    name: e.name.trim(),
    description: e.description,
    topics: e.topics,
    excluded_branches: e.excludedBranches,
    excluded_subtopics: e.excludedSubtopics,
    schema_version: 1,
  };
}

export default function SubjectsPage() {
  const [names, setNames] = useState<string[]>([]);
  const [activeName, setActiveName] = useState<string | null>(null);
  const [editor, setEditor] = useState<EditorState>(EMPTY_EDITOR);
  const [tree, setTree] = useState<ConceptTree>({});
  const [importConflict, setImportConflict] = useState<SubjectPayload | null>(null);
  const [confirmingDelete, setConfirmingDelete] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    const [list, active, fullTree] = await Promise.all([
      ipc.list_subjects(),
      ipc.get_active_subject(),
      // Universe of topics/branches/subtopics; the editor uses this to render
      // the InclusionTree for any topic the subject points to.
      ipc.get_concept_tree(null, false),
    ]);
    setNames(list);
    setActiveName(active);
    setTree(fullTree);
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const selectExisting = async (name: string) => {
    const p = await ipc.load_subject(name);
    if (p) setEditor(payloadToEditor(p));
  };

  const startNew = () => {
    setEditor(EMPTY_EDITOR);
  };

  const duplicate = async () => {
    if (!editor.originalName) return;
    setEditor((e) => ({ ...e, originalName: null, name: `${e.name} copy` }));
  };

  const allTopics = useMemo(() => Object.keys(tree).sort(), [tree]);
  const availableTopics = useMemo(
    () => allTopics.filter((t) => !editor.topics.includes(t)),
    [allTopics, editor.topics],
  );

  const addTopic = (topic: string | null) => {
    if (!topic) return;
    if (editor.topics.includes(topic)) return;
    setEditor((e) => ({ ...e, topics: [...e.topics, topic] }));
  };

  const removeTopic = (topic: string) => {
    setEditor((e) => {
      const eb = { ...e.excludedBranches };
      const es = { ...e.excludedSubtopics };
      delete eb[topic];
      delete es[topic];
      return {
        ...e,
        topics: e.topics.filter((t) => t !== topic),
        excludedBranches: eb,
        excludedSubtopics: es,
      };
    });
  };

  const onTopicTreeChange = (
    topic: string,
    next: { excludedBranches: string[]; excludedSubtopics: Record<string, string[]> },
  ) => {
    setEditor((e) => {
      const eb = { ...e.excludedBranches };
      if (next.excludedBranches.length > 0) eb[topic] = next.excludedBranches;
      else delete eb[topic];
      const es = { ...e.excludedSubtopics };
      if (Object.keys(next.excludedSubtopics).length > 0) es[topic] = next.excludedSubtopics;
      else delete es[topic];
      return { ...e, excludedBranches: eb, excludedSubtopics: es };
    });
  };

  const handleSave = async () => {
    setError(null);
    const target = editor.name.trim();
    if (!target) {
      setError("Name cannot be empty");
      return;
    }
    try {
      if (editor.originalName && editor.originalName !== target) {
        // Rename: enforce uniqueness, then update.
        await ipc.rename_subject(editor.originalName, target);
      } else if (!editor.originalName) {
        // New: enforce uniqueness.
        const ok = await ipc.subject_name_available(target);
        if (!ok) {
          setError("Name already in use");
          return;
        }
      }
      await ipc.save_subject(target, editorToPayload(editor));
      setEditor((e) => ({ ...e, originalName: target, name: target }));
      await refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  };

  const handleDelete = async () => {
    if (!confirmingDelete) return;
    try {
      await ipc.delete_subject(confirmingDelete);
      if (editor.originalName === confirmingDelete) setEditor(EMPTY_EDITOR);
    } finally {
      setConfirmingDelete(null);
      await refresh();
    }
  };

  const handleActivate = async () => {
    if (!editor.originalName) return;
    await ipc.activate_subject(editor.originalName);
    await refresh();
  };

  const handleDeactivate = async () => {
    await ipc.activate_subject(null);
    await refresh();
  };

  const handleExport = async () => {
    if (!editor.originalName) return;
    await ipc.export_subject_to_file(editor.originalName);
  };

  const handleImport = async () => {
    const payload = await ipc.import_subject_from_file();
    if (!payload) return;
    const exists = names.includes(payload.name);
    if (exists) {
      setImportConflict(payload);
    } else {
      await ipc.save_subject(payload.name, payload);
      await refresh();
      setEditor(payloadToEditor(payload));
    }
  };

  const handleImportReplace = async () => {
    if (!importConflict) return;
    await ipc.save_subject(importConflict.name, importConflict);
    setImportConflict(null);
    await refresh();
    setEditor(payloadToEditor(importConflict));
  };

  const handleImportRename = async (newName: string) => {
    if (!importConflict) return;
    if (names.includes(newName)) {
      setError(`Name ${newName} already in use`);
      return;
    }
    await ipc.save_subject(newName, { ...importConflict, name: newName });
    setImportConflict(null);
    await refresh();
  };

  return (
    <div className="flex h-full overflow-hidden">
      {/* Left column */}
      <aside className="flex w-72 flex-col border-r border-border bg-surface">
        <div className="border-b border-border p-3">
          <div className="mb-2 flex items-center gap-1">
            <Button variant="primary" size="sm" onClick={startNew} className="flex-1">
              <Plus className="h-4 w-4" />
              New
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={duplicate}
              disabled={!editor.originalName}
              aria-label="Duplicate"
            >
              <Copy className="h-4 w-4" />
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() =>
                editor.originalName && setConfirmingDelete(editor.originalName)
              }
              disabled={!editor.originalName}
              aria-label="Delete"
            >
              <Trash2 className="h-4 w-4 text-error" />
            </Button>
          </div>
          <div className="flex items-center gap-1">
            <Button variant="ghost" size="sm" onClick={handleImport} className="flex-1">
              <Upload className="h-4 w-4" />
              Import
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={handleExport}
              disabled={!editor.originalName}
              className="flex-1"
            >
              <Download className="h-4 w-4" />
              Export
            </Button>
          </div>
        </div>
        <ul className="flex-1 overflow-y-auto py-1">
          {names.length === 0 && (
            <li className="px-4 py-3 text-sm text-muted">No subjects yet. Click New to create one.</li>
          )}
          {names.map((n) => (
            <li
              key={n}
              className={
                "mx-1 my-0.5 flex cursor-pointer items-center gap-2 rounded-md px-3 py-2 text-sm hover:bg-background " +
                (editor.originalName === n ? "bg-background font-medium" : "")
              }
              onClick={() => selectExisting(n)}
            >
              {activeName === n && (
                <span
                  className="h-2 w-2 flex-none rounded-full bg-success"
                  aria-label="active"
                />
              )}
              <span className="flex-1 truncate">{n}</span>
            </li>
          ))}
        </ul>
      </aside>

      {/* Right column */}
      <main className="flex-1 overflow-y-auto">
        <div className="mx-auto max-w-3xl space-y-4 px-6 py-6">
          <Card title={editor.originalName ? "Edit subject" : "New subject"}>
            <div className="space-y-3">
              <label className="flex flex-col gap-1 text-sm">
                <span className="text-muted">Name</span>
                <Input
                  value={editor.name}
                  onChange={(e) => setEditor((s) => ({ ...s, name: e.target.value }))}
                  placeholder="e.g. Math I"
                />
              </label>
              <label className="flex flex-col gap-1 text-sm">
                <span className="text-muted">Description</span>
                <textarea
                  value={editor.description}
                  onChange={(e) => setEditor((s) => ({ ...s, description: e.target.value }))}
                  className="min-h-[5rem] rounded-md border border-border bg-background px-3 py-2 text-sm outline-none focus-visible:ring-2 focus-visible:ring-primary"
                  placeholder="Freeform notes (optional)"
                />
              </label>
              {error && <p className="text-sm text-error">{error}</p>}
              <div className="flex flex-wrap gap-2">
                <Button variant="primary" onClick={handleSave}>
                  Save changes
                </Button>
                {editor.originalName && activeName !== editor.originalName && (
                  <Button variant="outline" onClick={handleActivate}>
                    Activate this subject
                  </Button>
                )}
                {editor.originalName && activeName === editor.originalName && (
                  <Button variant="outline" onClick={handleDeactivate}>
                    Deactivate
                  </Button>
                )}
              </div>
            </div>
          </Card>

          <Card title="Topics">
            <div className="space-y-3">
              <Combobox
                options={availableTopics}
                onSelect={addTopic}
                placeholder="Add a topic…"
                searchPlaceholder="Search topics"
                emptyMessage={
                  allTopics.length === 0
                    ? "No taxonomy data — ingest the seed first"
                    : "All topics added"
                }
                className="min-w-[14rem]"
              />
              {editor.topics.length === 0 && (
                <p className="text-sm text-muted">
                  Pick at least one topic. Default everything is included; uncheck branches /
                  subtopics to exclude.
                </p>
              )}
              {editor.topics.map((t) => (
                <InclusionTree
                  key={t}
                  topic={t}
                  branches={tree[t] ?? {}}
                  excludedBranches={editor.excludedBranches[t] ?? []}
                  excludedSubtopics={editor.excludedSubtopics[t] ?? {}}
                  onChange={(next) => onTopicTreeChange(t, next)}
                  onRemoveTopic={() => removeTopic(t)}
                />
              ))}
            </div>
          </Card>
        </div>
      </main>

      <Modal
        open={confirmingDelete !== null}
        onClose={() => setConfirmingDelete(null)}
        title="Delete subject?"
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
          Delete <code className="font-mono">{confirmingDelete}</code>?
        </p>
      </Modal>

      <ImportConflictDialog
        conflict={importConflict}
        existingNames={names}
        onCancel={() => setImportConflict(null)}
        onReplace={handleImportReplace}
        onRename={handleImportRename}
      />
    </div>
  );
}

function ImportConflictDialog({
  conflict,
  existingNames,
  onCancel,
  onReplace,
  onRename,
}: {
  conflict: SubjectPayload | null;
  existingNames: readonly string[];
  onCancel: () => void;
  onReplace: () => void;
  onRename: (name: string) => void;
}) {
  const [renameValue, setRenameValue] = useState("");
  const [renameMode, setRenameMode] = useState(false);
  useEffect(() => {
    if (conflict) {
      setRenameValue(`${conflict.name} (imported)`);
      setRenameMode(false);
    }
  }, [conflict]);
  if (!conflict) return null;
  const renameDisabled =
    !renameValue.trim() ||
    existingNames.some((n) => n.toLowerCase() === renameValue.trim().toLowerCase());
  return (
    <Modal
      open
      onClose={onCancel}
      title="Subject already exists"
      footer={
        renameMode ? (
          <>
            <Button variant="ghost" onClick={() => setRenameMode(false)}>
              Back
            </Button>
            <Button
              variant="primary"
              disabled={renameDisabled}
              onClick={() => onRename(renameValue.trim())}
            >
              Import as {renameValue.trim() || "…"}
            </Button>
          </>
        ) : (
          <>
            <Button variant="ghost" onClick={onCancel}>
              Cancel
            </Button>
            <Button variant="outline" onClick={() => setRenameMode(true)}>
              Rename…
            </Button>
            <Button variant="primary" onClick={onReplace}>
              Replace
            </Button>
          </>
        )
      }
    >
      {renameMode ? (
        <>
          <p className="mb-2 text-sm">Save the imported subject under a new name:</p>
          <Input value={renameValue} onChange={(e) => setRenameValue(e.target.value)} autoFocus />
        </>
      ) : (
        <p>
          A subject named <code className="font-mono">{conflict.name}</code> already exists.
          Replace it, save under a different name, or cancel?
        </p>
      )}
    </Modal>
  );
}
