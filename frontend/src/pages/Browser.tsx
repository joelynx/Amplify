/**
 * Question Browser — spec §8.6. Read-only with respect to question content.
 *
 * A list of questions, each shown by its rendered opening lines with the
 * taxonomy underneath; clicking a row opens it in the side panel. Filters,
 * sort, multi-select. Mass actions update tags / in_syllabus / progress for
 * the selection. "Create paper from selection" navigates to /generate with
 * the IDs in location state.
 *
 * No New / Edit / Delete buttons. No Author mode. Question content is
 * immutable from the runtime app per spec §16.
 */

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
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
import { LatexContent } from "../components/browser/LatexContent";
import { QuestionSidePanel } from "../components/browser/QuestionSidePanel";
import { cn } from "../lib/cn";
import { useDebounced } from "../lib/debounce";
import { emit } from "../appearance/events";
import { searchEgg } from "../appearance/eggs/search";
import { useSubjectStore } from "../state/subject";
import {
  ipc,
  type Filters,
  type Question,
  type SearchResult,
} from "../lib/ipc";

const PAGE_SIZE = 50;
const ALL_SUBJECT = "(All subjects)";
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

const SORT_LABELS: Record<SortColumn, string> = {
  question_id: "Question number",
  topic: "Topic",
  branch: "Branch",
  subtopic: "Subtopic",
  type: "Type",
  source: "Source",
  in_syllabus: "In syllabus",
  times_used: "Times used",
  difficulty_rating: "Difficulty",
};
const SORT_COLUMNS = Object.keys(SORT_LABELS) as SortColumn[];

export default function BrowserPage() {
  const navigate = useNavigate();

  // --- filter / sort / page state ----------------------------------
  // Scope: the active subject, unless another (or all) is picked here.
  const activeSubject = useSubjectStore((s) => s.active);
  const [subject, setSubject] = useState<string | null>(activeSubject);
  useEffect(() => setSubject(activeSubject), [activeSubject]);
  const [subjects, setSubjects] = useState<string[]>([]);
  const [topic, setTopic] = useState<string | null>(null);
  const [type, setType] = useState<string | null>(null);
  const [source, setSource] = useState<string | null>(null);
  const [inSyllabusOnly, setInSyllabusOnly] = useState(false);
  const [bookmarkedOnly, setBookmarkedOnly] = useState(false);
  const [textQuery, setTextQuery] = useState("");
  const [sortBy, setSortBy] = useState<SortColumn>("question_id");
  const [sortDir, setSortDir] = useState<SortDir>("asc");
  const [page, setPage] = useState(0);

  // --- data --------------------------------------------------------
  const [rows, setRows] = useState<Question[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [openError, setOpenError] = useState<string | null>(null);
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
  }, [subject, topic, type, source, inSyllabusOnly, bookmarkedOnly, textQuery, sortBy, sortDir]);

  const filters = useMemo<Filters>(
    () => ({
      subject,
      topics: topic ? [topic] : [],
      types: type ? [type] : [],
      sources: source ? [source] : [],
      in_syllabus_only: inSyllabusOnly,
      reuse_questions: true,
      bookmarked_only: bookmarkedOnly,
    }),
    [subject, topic, type, source, inSyllabusOnly, bookmarkedOnly],
  );

  // Only the latest search may write its rows: an earlier, slower one is dropped.
  const searchSeq = useRef(0);
  const refresh = useCallback(async () => {
    const seq = ++searchSeq.current;
    setLoading(true);
    try {
      const r: SearchResult = await ipc.search_questions(
        filters,
        `${sortBy}_${sortDir}`,
        page,
        PAGE_SIZE,
        textQuery || null,
      );
      if (seq !== searchSeq.current) return;
      setRows(r.rows);
      setTotal(r.total);
      setLoadError(r.error ?? null);
    } catch (e) {
      if (seq !== searchSeq.current) return;
      setRows([]);
      setTotal(0);
      setLoadError(e instanceof Error ? e.message : String(e));
    } finally {
      if (seq === searchSeq.current) setLoading(false);
    }
  }, [filters, sortBy, sortDir, page, textQuery]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  // Easter-egg cards for a few famous queries; the real search still runs.
  const debouncedQuery = useDebounced(textQuery, 500);
  const searchCard = useMemo(() => searchEgg(debouncedQuery), [debouncedQuery]);
  useEffect(() => {
    if (debouncedQuery.trim()) emit({ type: "search", query: debouncedQuery.trim() });
  }, [debouncedQuery]);

  useEffect(() => {
    ipc.list_subjects().then(setSubjects);
    ipc.get_types().then(setTypes);
    ipc.get_sources().then(setSources);
  }, []);

  // The topic list follows the subject; a topic outside it is dropped.
  useEffect(() => {
    let cancelled = false;
    ipc.get_topics(subject, false).then((t) => {
      if (cancelled) return;
      setTopics(t);
      setTopic((cur) => (cur && !t.includes(cur) ? null : cur));
    });
    return () => {
      cancelled = true;
    };
  }, [subject]);

  const filtersSet = Boolean(topic || type || source || inSyllabusOnly || bookmarkedOnly || textQuery);
  const clearFilters = () => {
    setTopic(null);
    setType(null);
    setSource(null);
    setInSyllabusOnly(false);
    setBookmarkedOnly(false);
    setTextQuery("");
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
    try {
      const n = await ipc.mass_action(selectedIds, action, payload);
      setActionFeedback(`${summary}: ${n} question${n === 1 ? "" : "s"} updated`);
      await refresh();
      if (opened && selected.has(opened.question_id)) {
        const q = await ipc.get_question(opened.question_id);
        setOpened(q);
      }
    } catch (e) {
      setActionFeedback(`Nothing was changed: ${e instanceof Error ? e.message : String(e)}`);
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
      value === 1 ? "Marked in syllabus" : "Marked off syllabus",
    );
  const onResetProgress = async () => {
    await handleMass("reset_progress", null, "Cleared usage");
    setConfirmReset(false);
  };
  const onGenerateFromSelection = () => {
    navigate("/generate", {
      state: { questionIds: selectedIds },
    });
  };

  // As with the search: the last question asked for is the one shown.
  const openSeq = useRef(0);
  const openRow = useCallback(async (qid: number) => {
    const seq = ++openSeq.current;
    try {
      const q = await ipc.get_question(qid);
      if (seq !== openSeq.current) return;
      setOpened(q);
      setOpenError(q ? null : `Question ${qid} is no longer in the question bank.`);
    } catch {
      if (seq === openSeq.current) setOpenError(`Question ${qid} could not be opened. Try again.`);
    }
  }, []);
  const closeOpened = useCallback(() => {
    openSeq.current += 1;
    setOpened(null);
  }, []);

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  return (
    <div className="relative flex h-full overflow-hidden">
      <main className="flex flex-1 flex-col overflow-hidden">
        {/* Filter bar */}
        <Card className="m-3 mb-0 rounded-lg">
          <div className="flex flex-wrap items-end gap-3">
            <FilterCol label="Subject">
              <Combobox
                options={subjects}
                value={subject}
                onSelect={setSubject}
                placeholder={ALL_SUBJECT}
                sentinel={ALL_SUBJECT}
                searchPlaceholder="Search subjects"
                emptyMessage="No subjects yet"
                className="min-w-[11rem]"
              />
            </FilterCol>
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
                  placeholder="Text, topic, tag or abbreviation"
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
            <FilterCol label="">
              <label className="inline-flex items-center gap-2 text-sm">
                <Checkbox
                  state={bookmarkedOnly ? "checked" : "unchecked"}
                  onChange={() => setBookmarkedOnly((v) => !v)}
                />
                <span>Bookmarked only</span>
              </label>
            </FilterCol>
            <FilterCol label="Sort by">
              <div className="flex items-center gap-1">
                <Combobox
                  options={SORT_COLUMNS.map((c) => SORT_LABELS[c])}
                  value={SORT_LABELS[sortBy]}
                  onSelect={(label) => {
                    const col = SORT_COLUMNS.find((c) => SORT_LABELS[c] === label);
                    if (col) setSortBy(col);
                  }}
                  searchPlaceholder="Sort by"
                  emptyMessage="—"
                  className="min-w-[10rem]"
                />
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setSortDir((d) => (d === "asc" ? "desc" : "asc"))}
                  aria-label={sortDir === "asc" ? "Ascending; switch to descending" : "Descending; switch to ascending"}
                >
                  <ArrowDownUp className="h-4 w-4" />
                  {sortDir === "asc" ? "Asc" : "Desc"}
                </Button>
              </div>
            </FilterCol>
            <div className="ml-auto text-sm text-muted" aria-live="polite">
              {loading && rows.length === 0
                ? "Loading…"
                : `${total.toLocaleString()} match${total === 1 ? "" : "es"}`}
            </div>
          </div>
        </Card>

        {searchCard && (
          <div className="m-3 mb-0 rounded-lg border border-dashed border-primary/60 bg-primary/5 px-4 py-3 text-sm">
            <span className="font-semibold">{searchCard.title}</span> <span className="text-muted">{searchCard.body}</span>
          </div>
        )}

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
                Mark in syllabus
              </Button>
              <Button variant="outline" size="sm" onClick={() => onSetInSyllabus(0)}>
                <ToggleLeft className="h-4 w-4" />
                Mark off syllabus
              </Button>
              <Button variant="outline" size="sm" onClick={() => setConfirmReset(true)}>
                <Eraser className="h-4 w-4" />
                Clear usage
              </Button>
              <Button variant="primary" size="sm" onClick={onGenerateFromSelection}>
                <Wand2 className="h-4 w-4" />
                Create paper from selection
              </Button>
              <Button variant="ghost" size="sm" onClick={clearSelection}>
                Clear
              </Button>
            </div>
            {actionFeedback && <p className="mt-2 text-xs text-muted">{actionFeedback}</p>}
          </Card>
        )}

        {/* Questions */}
        <div className="flex-1 overflow-auto p-3" aria-busy={loading}>
          {openError && (
            <p role="alert" className="mb-2 rounded-md border border-error/40 bg-error/5 px-3 py-2 text-sm">
              {openError}
            </p>
          )}
          {loadError ? (
            <div role="alert" className="px-3 py-8 text-center text-sm">
              <p className="font-medium">The questions could not be loaded.</p>
              <p className="mt-1 text-muted">{loadError}</p>
              <Button variant="outline" size="sm" className="mt-3" onClick={refresh}>
                Try again
              </Button>
            </div>
          ) : rows.length === 0 ? (
            <div className="px-3 py-8 text-center text-sm text-muted">
              {loading ? (
                "Loading questions…"
              ) : (
                <>
                  <p>No questions match these filters.</p>
                  {filtersSet && (
                    <Button variant="outline" size="sm" className="mt-3" onClick={clearFilters}>
                      Clear filters
                    </Button>
                  )}
                </>
              )}
            </div>
          ) : (
            <table
              className={cn(
                "w-full table-fixed border-separate border-spacing-0 text-sm transition-opacity",
                loading && "opacity-60",
              )}
            >
              <thead className="sticky top-0 z-10 bg-surface">
                <tr>
                  <th className="w-10 border-b border-border bg-surface px-3 py-2 text-left">
                    <Checkbox state={pageState} onChange={() => togglePage(!pageAllSelected)} />
                  </th>
                  <th className="border-b border-border bg-surface px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide text-muted">
                    Question · click one to open it
                  </th>
                </tr>
              </thead>
              <tbody>
                {rows.map((q) => (
                  <tr
                    key={q.question_id}
                    data-ui="question-row"
                    onClick={() => openRow(q.question_id)}
                    className={cn(
                      "cursor-pointer hover:bg-surface/60",
                      selected.has(q.question_id) && "bg-primary/5",
                      opened?.question_id === q.question_id && "bg-surface",
                    )}
                  >
                    <td
                      className="w-10 border-b border-border px-3 py-2 align-top"
                      onClick={(e) => e.stopPropagation()}
                    >
                      <Checkbox
                        state={selected.has(q.question_id) ? "checked" : "unchecked"}
                        onChange={() => toggleRow(q.question_id, !selected.has(q.question_id))}
                      />
                    </td>
                    <td className="border-b border-border px-3 py-2 align-top">
                      {/* The opening lines only; the panel shows the whole question. */}
                      <div data-ui="question-excerpt" className="max-h-[4.75rem] overflow-hidden">
                        <LatexContent source={q.latexcode} />
                      </div>
                      <div className="mt-1.5 flex flex-wrap items-center gap-x-2 gap-y-0.5 text-xs text-muted">
                        <button
                          type="button"
                          className="font-mono text-primary hover:underline"
                          aria-label={`Open question ${q.question_id}`}
                          onClick={(e) => {
                            e.stopPropagation();
                            openRow(q.question_id);
                          }}
                        >
                          Q{q.question_id}
                        </button>
                        <span>
                          {q.topic} / {q.branch} / {q.subtopic}
                        </span>
                        {q.type && <span>· {q.type}</span>}
                        {q.source && <span>· {q.source}</span>}
                        {!q.in_syllabus && <span>· off syllabus</span>}
                        {q.times_used > 0 && <span>· used ×{q.times_used}</span>}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
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
        filters={filters}
        textQuery={textQuery}
        onClose={closeOpened}
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
        title="Clear usage for the selection?"
        tone="error"
        footer={
          <>
            <Button variant="ghost" onClick={() => setConfirmReset(false)}>
              Cancel
            </Button>
            <Button variant="primary" onClick={onResetProgress}>
              Clear usage
            </Button>
          </>
        }
      >
        <p>
          Forgets how often the {selected.size} selected question
          {selected.size === 1 ? " has" : "s have"} appeared in papers and quizzes, and when{" "}
          {selected.size === 1 ? "it was" : "they were"} last seen. The questions themselves are untouched.
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
