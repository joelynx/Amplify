/**
 * Question Browser — spec §8.6. Read-only with respect to question content.
 *
 * Power-user table: filters, sort, multi-select. Mass actions update
 * tags / in_syllabus / progress for the selection. "Generate PSet from
 * selection" navigates to /generate with the IDs in location state.
 *
 * No New / Edit / Delete buttons. No Author mode. Question content is
 * immutable from the runtime app per spec §16.
 */

import { useCallback, useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  ArrowDownUp,
  ChevronLeft,
  ChevronRight,
  Eraser,
  Minus,
  Plus,
  Search,
  ToggleLeft,
  ToggleRight,
  Wand2,
} from "lucide-react";

import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { Checkbox } from "../components/ui/Checkbox";
import { Combobox } from "../components/ui/Combobox";
import { Input } from "../components/ui/Input";
import { Modal } from "../components/ui/Modal";
import { QuestionSidePanel } from "../components/browser/QuestionSidePanel";
import { cn } from "../lib/cn";
import {
  ipc,
  type Filters,
  type Question,
  type SearchResult,
} from "../lib/ipc";

const PAGE_SIZE = 50;
const ALL_TOPIC = "(All topics)";
const ALL_TYPE = "(All types)";
const ALL_SOURCE = "(All sources)";

type SortDir = "asc" | "desc";
type SortColumn =
  | "question_id"
  | "topic"
  | "branch"
  | "subtopic"
  | "type"
  | "source"
  | "in_syllabus"
  | "times_used"
  | "difficulty_rating";

export default function BrowserPage() {
  const navigate = useNavigate();

  // --- filter / sort / page state ----------------------------------
  const [topic, setTopic] = useState<string | null>(null);
  const [type, setType] = useState<string | null>(null);
  const [source, setSource] = useState<string | null>(null);
  const [inSyllabusOnly, setInSyllabusOnly] = useState(false);
  const [textQuery, setTextQuery] = useState("");
  const [sortBy, setSortBy] = useState<SortColumn>("question_id");
  const [sortDir, setSortDir] = useState<SortDir>("asc");
  const [page, setPage] = useState(0);

  // --- data --------------------------------------------------------
  const [rows, setRows] = useState<Question[]>([]);
  const [total, setTotal] = useState(0);
  const [topics, setTopics] = useState<string[]>([]);
  const [types, setTypes] = useState<string[]>([]);
  const [sources, setSources] = useState<string[]>([]);

  // --- selection ---------------------------------------------------
  const [selected, setSelected] = useState<Set<number>>(new Set());
  const [opened, setOpened] = useState<Question | null>(null);

  // --- mass-action UI ---------------------------------------------
  const [tagDialog, setTagDialog] = useState<{ mode: "add" | "remove"; value: string } | null>(null);
  const [confirmReset, setConfirmReset] = useState(false);
  const [actionFeedback, setActionFeedback] = useState<string | null>(null);

  // Reset page when filters change.
  useEffect(() => {
    setPage(0);
  }, [topic, type, source, inSyllabusOnly, textQuery, sortBy, sortDir]);

  const filters = useMemo<Filters>(
    () => ({
      topics: topic ? [topic] : [],
      types: type ? [type] : [],
      sources: source ? [source] : [],
      in_syllabus_only: inSyllabusOnly,
      reuse_questions: true,
    }),
    [topic, type, source, inSyllabusOnly],
  );

  const refresh = useCallback(async () => {
    const r: SearchResult = await ipc.search_questions(
      filters,
      `${sortBy}_${sortDir}`,
      page,
      PAGE_SIZE,
      textQuery || null,
    );
    setRows(r.rows);
    setTotal(r.total);
  }, [filters, sortBy, sortDir, page, textQuery]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  useEffect(() => {
    ipc.get_topics(null, false).then(setTopics);
    ipc.get_types().then(setTypes);
    ipc.get_sources().then(setSources);
  }, []);

  // --- column sort -------------------------------------------------
  const onSort = (col: SortColumn) => {
    if (col === sortBy) setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    else {
      setSortBy(col);
      setSortDir("asc");
    }
  };

  // --- selection helpers ------------------------------------------
  const toggleRow = (qid: number, checked: boolean) =>
    setSelected((s) => {
      const next = new Set(s);
      if (checked) next.add(qid);
      else next.delete(qid);
      return next;
    });
  const togglePage = (checked: boolean) =>
    setSelected((s) => {
      const next = new Set(s);
      if (checked) rows.forEach((r) => next.add(r.question_id));
      else rows.forEach((r) => next.delete(r.question_id));
      return next;
    });
  const clearSelection = () => setSelected(new Set());

  const pageAllSelected = rows.length > 0 && rows.every((r) => selected.has(r.question_id));
  const pageAnySelected = rows.some((r) => selected.has(r.question_id));
  const pageState: "checked" | "unchecked" | "partial" = pageAllSelected
    ? "checked"
    : pageAnySelected
      ? "partial"
      : "unchecked";

  // --- mass actions ------------------------------------------------
  const selectedIds = useMemo(() => Array.from(selected), [selected]);

  const handleMass = async (
    action: string,
    payload: Record<string, unknown> | null,
    summary: string,
  ) => {
    const n = await ipc.mass_action(selectedIds, action, payload);
    setActionFeedback(`${summary}: ${n} row${n === 1 ? "" : "s"} updated`);
    await refresh();
    if (opened && selected.has(opened.question_id)) {
      const q = await ipc.get_question(opened.question_id);
      setOpened(q);
    }
  };

  const onAddTag = async (tag: string) => {
    await handleMass("add_tag", { tag }, `Added tag '${tag}'`);
    setTagDialog(null);
  };
  const onRemoveTag = async (tag: string) => {
    await handleMass("remove_tag", { tag }, `Removed tag '${tag}'`);
    setTagDialog(null);
  };
  const onSetInSyllabus = (value: 0 | 1) =>
    handleMass(
      "set_in_syllabus",
      { value },
      value === 1 ? "Set in_syllabus = 1" : "Set in_syllabus = 0",
    );
  const onResetProgress = async () => {
    await handleMass("reset_progress", null, "Reset question data");
    setConfirmReset(false);
  };
  const onGenerateFromSelection = () => {
    navigate("/generate", {
      state: { questionIds: selectedIds },
    });
  };

  const openRow = async (qid: number) => {
    const q = await ipc.get_question(qid);
    setOpened(q);
  };

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  return (
    <div className="flex h-full overflow-hidden">
      <main className="flex flex-1 flex-col overflow-hidden">
        {/* Filter bar */}
        <Card className="m-3 mb-0 rounded-lg">
          <div className="flex flex-wrap items-end gap-3">
            <FilterCol label="Topic">
              <Combobox
                options={topics}
                value={topic}
                onSelect={setTopic}
                placeholder={ALL_TOPIC}
                sentinel={ALL_TOPIC}
                searchPlaceholder="Search topics"
                emptyMessage="—"
                clearable
                className="min-w-[12rem]"
              />
            </FilterCol>
            <FilterCol label="Type">
              <Combobox
                options={types}
                value={type}
                onSelect={setType}
                placeholder={ALL_TYPE}
                sentinel={ALL_TYPE}
                searchPlaceholder="Search types"
                emptyMessage="—"
                clearable
                className="min-w-[10rem]"
              />
            </FilterCol>
            <FilterCol label="Source">
              <Combobox
                options={sources}
                value={source}
                onSelect={setSource}
                placeholder={ALL_SOURCE}
                sentinel={ALL_SOURCE}
                searchPlaceholder="Search sources"
                emptyMessage="—"
                clearable
                className="min-w-[10rem]"
              />
            </FilterCol>
            <FilterCol label="Search">
              <div className="flex h-9 items-center gap-2 rounded-md border border-border bg-background px-3">
                <Search className="h-4 w-4 text-muted" />
                <input
                  value={textQuery}
                  onChange={(e) => setTextQuery(e.target.value)}
                  className="w-56 bg-transparent text-sm outline-none"
                  placeholder="Substring in latexcode"
                />
              </div>
            </FilterCol>
            <FilterCol label="">
              <label className="inline-flex items-center gap-2 text-sm">
                <Checkbox
                  state={inSyllabusOnly ? "checked" : "unchecked"}
                  onChange={() => setInSyllabusOnly((v) => !v)}
                />
                <span>In-syllabus only</span>
              </label>
            </FilterCol>
            <div className="ml-auto text-sm text-muted">
              {total.toLocaleString()} match{total === 1 ? "" : "es"}
            </div>
          </div>
        </Card>

        {/* Mass actions */}
        {selected.size > 0 && (
          <Card className="m-3 mb-0 rounded-lg border-primary/50 bg-primary/5">
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-sm font-medium">
                {selected.size} selected
              </span>
              <Button variant="outline" size="sm" onClick={() => setTagDialog({ mode: "add", value: "" })}>
                <Plus className="h-4 w-4" />
                Add tag
              </Button>
              <Button variant="outline" size="sm" onClick={() => setTagDialog({ mode: "remove", value: "" })}>
                <Minus className="h-4 w-4" />
                Remove tag
              </Button>
              <Button variant="outline" size="sm" onClick={() => onSetInSyllabus(1)}>
                <ToggleRight className="h-4 w-4" />
                In-syllabus = 1
              </Button>
              <Button variant="outline" size="sm" onClick={() => onSetInSyllabus(0)}>
                <ToggleLeft className="h-4 w-4" />
                In-syllabus = 0
              </Button>
              <Button variant="outline" size="sm" onClick={() => setConfirmReset(true)}>
                <Eraser className="h-4 w-4" />
                Reset progress
              </Button>
              <Button variant="primary" size="sm" onClick={onGenerateFromSelection}>
                <Wand2 className="h-4 w-4" />
                Generate PSet from selection
              </Button>
              <Button variant="ghost" size="sm" onClick={clearSelection}>
                Clear
              </Button>
            </div>
            {actionFeedback && <p className="mt-2 text-xs text-muted">{actionFeedback}</p>}
          </Card>
        )}

        {/* Table */}
        <div className="flex-1 overflow-auto p-3">
          <table className="min-w-full table-fixed border-separate border-spacing-0 text-sm">
            <thead className="sticky top-0 z-10 bg-surface">
              <tr>
                <Th className="w-10">
                  <Checkbox state={pageState} onChange={() => togglePage(!pageAllSelected)} />
                </Th>
                <Th className="w-16" sortable col="question_id" {...{ sortBy, sortDir, onSort }}>
                  ID
                </Th>
                <Th sortable col="topic" {...{ sortBy, sortDir, onSort }}>
                  Topic
                </Th>
                <Th sortable col="branch" {...{ sortBy, sortDir, onSort }}>
                  Branch
                </Th>
                <Th sortable col="subtopic" {...{ sortBy, sortDir, onSort }}>
                  Subtopic
                </Th>
                <Th className="w-24" sortable col="type" {...{ sortBy, sortDir, onSort }}>
                  Type
                </Th>
                <Th className="w-24" sortable col="source" {...{ sortBy, sortDir, onSort }}>
                  Source
                </Th>
                <Th className="w-16" sortable col="in_syllabus" {...{ sortBy, sortDir, onSort }}>
                  In syll.
                </Th>
                <Th className="w-16" sortable col="times_used" {...{ sortBy, sortDir, onSort }}>
                  Used
                </Th>
              </tr>
            </thead>
            <tbody>
              {rows.length === 0 && (
                <tr>
                  <td colSpan={9} className="px-3 py-8 text-center text-muted">
                    No questions match these filters.
                  </td>
                </tr>
              )}
              {rows.map((q) => (
                <tr
                  key={q.question_id}
                  className={cn(
                    "border-b border-border hover:bg-surface/60",
                    selected.has(q.question_id) && "bg-primary/5",
                    opened?.question_id === q.question_id && "bg-surface",
                  )}
                >
                  <Td className="w-10">
                    <Checkbox
                      state={selected.has(q.question_id) ? "checked" : "unchecked"}
                      onChange={() => toggleRow(q.question_id, !selected.has(q.question_id))}
                    />
                  </Td>
                  <Td>
                    <button
                      type="button"
                      className="font-mono text-primary hover:underline"
                      onClick={() => openRow(q.question_id)}
                    >
                      {q.question_id}
                    </button>
                  </Td>
                  <Td>{q.topic}</Td>
                  <Td>{q.branch}</Td>
                  <Td>{q.subtopic}</Td>
                  <Td>{q.type ?? "—"}</Td>
                  <Td>{q.source ?? "—"}</Td>
                  <Td>{q.in_syllabus ? "✓" : "—"}</Td>
                  <Td>{q.times_used}</Td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        <footer className="flex items-center justify-between border-t border-border bg-surface px-4 py-2 text-sm">
          <span className="text-muted">
            Page {page + 1} of {totalPages}
          </span>
          <div className="flex items-center gap-1">
            <Button
              variant="ghost"
              size="sm"
              disabled={page === 0}
              onClick={() => setPage((p) => Math.max(0, p - 1))}
            >
              <ChevronLeft className="h-4 w-4" />
              Prev
            </Button>
            <Button
              variant="ghost"
              size="sm"
              disabled={page + 1 >= totalPages}
              onClick={() => setPage((p) => p + 1)}
            >
              Next
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        </footer>
      </main>

      <QuestionSidePanel
        question={opened}
        onClose={() => setOpened(null)}
        onPickSimilar={openRow}
      />

      <TagDialog
        dialog={tagDialog}
        onCancel={() => setTagDialog(null)}
        onAdd={onAddTag}
        onRemove={onRemoveTag}
      />

      <Modal
        open={confirmReset}
        onClose={() => setConfirmReset(false)}
        title="Reset question data?"
        tone="error"
        footer={
          <>
            <Button variant="ghost" onClick={() => setConfirmReset(false)}>
              Cancel
            </Button>
            <Button variant="primary" onClick={onResetProgress}>
              Reset
            </Button>
          </>
        }
      >
        <p>
          Zeroes <code>times_used</code>, <code>interactive_times_used</code>, and{" "}
          <code>date_last_accessed</code> for the {selected.size} selected question
          {selected.size === 1 ? "" : "s"}. Question content is untouched.
        </p>
      </Modal>
    </div>
  );
}

function FilterCol({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="flex flex-col gap-1 text-sm">
      {label && <span className="text-xs uppercase tracking-wide text-muted">{label}</span>}
      {children}
    </label>
  );
}

function Th({
  children,
  className,
  sortable,
  col,
  sortBy,
  sortDir,
  onSort,
}: {
  children: React.ReactNode;
  className?: string;
  sortable?: boolean;
  col?: SortColumn;
  sortBy?: SortColumn;
  sortDir?: SortDir;
  onSort?: (c: SortColumn) => void;
}) {
  const active = sortable && col === sortBy;
  return (
    <th
      className={cn(
        "border-b border-border bg-surface px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide text-muted",
        sortable && "cursor-pointer hover:text-text",
        className,
      )}
      onClick={() => sortable && col && onSort?.(col)}
    >
      <span className="inline-flex items-center gap-1">
        {children}
        {sortable && (
          <ArrowDownUp
            className={cn(
              "h-3 w-3 transition-opacity",
              active ? "opacity-100 text-primary" : "opacity-40",
              active && sortDir === "desc" && "rotate-180",
            )}
          />
        )}
      </span>
    </th>
  );
}

function Td({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <td className={cn("border-b border-border px-3 py-1.5 align-top", className)}>{children}</td>
  );
}

function TagDialog({
  dialog,
  onCancel,
  onAdd,
  onRemove,
}: {
  dialog: { mode: "add" | "remove"; value: string } | null;
  onCancel: () => void;
  onAdd: (tag: string) => void;
  onRemove: (tag: string) => void;
}) {
  const [value, setValue] = useState("");
  useEffect(() => {
    if (dialog) setValue(dialog.value);
  }, [dialog]);
  if (!dialog) return null;
  return (
    <Modal
      open
      onClose={onCancel}
      title={dialog.mode === "add" ? "Add tag" : "Remove tag"}
      footer={
        <>
          <Button variant="ghost" onClick={onCancel}>
            Cancel
          </Button>
          <Button
            variant="primary"
            onClick={() => (dialog.mode === "add" ? onAdd(value.trim()) : onRemove(value.trim()))}
            disabled={!value.trim()}
          >
            {dialog.mode === "add" ? "Add" : "Remove"}
          </Button>
        </>
      }
    >
      <Input
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter" && value.trim()) {
            (dialog.mode === "add" ? onAdd : onRemove)(value.trim());
          }
        }}
        placeholder="Tag name"
        autoFocus
      />
    </Modal>
  );
}
