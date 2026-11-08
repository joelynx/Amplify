/**
 * A personal note and a bookmark per question (question_notes, migration 009).
 *
 * `SelfExplain` is the optional prompt shown after a solution: one short
 * question about why the method works, picked per question so it stays the
 * same on every visit; the answer is saved as the question's note.
 * `NoteEditor` is the plain note box (Browser side panel), `BookmarkButton`
 * the star.
 */

import { useCallback, useEffect, useState } from "react";
import { Bookmark, BookmarkCheck, MessageSquareText } from "lucide-react";

import { Button } from "../ui/Button";
import { cn } from "../../lib/cn";
import { ipc } from "../../lib/ipc";

/** Self-explanation prompts. Reusable on any worked solution; no live tutor. */
export const SELF_EXPLAIN_PROMPTS: readonly string[] = [
  "Why was this method the right one to use here?",
  "Which condition makes the key step valid?",
  "What would change if one of the assumptions were removed?",
  "What is the one idea you would need to solve a similar question?",
  "Where would you have got stuck, and what gets you past it?",
];

export function promptFor(questionId: number): string {
  return SELF_EXPLAIN_PROMPTS[questionId % SELF_EXPLAIN_PROMPTS.length];
}

interface NoteState {
  note: string;
  bookmarked: boolean;
  loaded: boolean;
}

/** Load and save one question's note and bookmark. */
export function useQuestionNote(questionId: number) {
  const [state, setState] = useState<NoteState>({ note: "", bookmarked: false, loaded: false });

  useEffect(() => {
    let cancelled = false;
    setState({ note: "", bookmarked: false, loaded: false });
    ipc
      .get_question_notes([questionId])
      .then((notes) => {
        if (cancelled) return;
        const n = notes[String(questionId)];
        setState({ note: n?.note ?? "", bookmarked: Boolean(n?.bookmarked), loaded: true });
      })
      .catch(() => {
        if (!cancelled) setState((s) => ({ ...s, loaded: true }));
      });
    return () => {
      cancelled = true;
    };
  }, [questionId]);

  const saveNote = useCallback(
    async (note: string) => {
      await ipc.save_question_note(questionId, note);
      setState((s) => ({ ...s, note }));
    },
    [questionId],
  );

  const toggleBookmark = useCallback(async () => {
    const next = !state.bookmarked;
    setState((s) => ({ ...s, bookmarked: next }));
    try {
      await ipc.set_question_bookmark(questionId, next);
    } catch {
      setState((s) => ({ ...s, bookmarked: !next }));
    }
  }, [questionId, state.bookmarked]);

  return { ...state, saveNote, toggleBookmark };
}

export function BookmarkButton({ questionId, className }: { questionId: number; className?: string }) {
  const { bookmarked, loaded, toggleBookmark } = useQuestionNote(questionId);
  return (
    <button
      type="button"
      disabled={!loaded}
      onClick={() => void toggleBookmark()}
      title={bookmarked ? "Remove bookmark" : "Bookmark this question"}
      aria-pressed={bookmarked}
      className={cn(
        "flex items-center gap-2 rounded-md px-3 py-1.5 text-sm font-medium transition-colors disabled:opacity-50",
        bookmarked ? "bg-primary/10 text-primary" : "bg-surface text-text/80 hover:bg-surface-hover",
        className,
      )}
    >
      {bookmarked ? <BookmarkCheck size={16} /> : <Bookmark size={16} />}
      {bookmarked ? "Bookmarked" : "Bookmark"}
    </button>
  );
}

interface EditorProps {
  questionId: number;
  /** Shown above the box; omit for a plain note. */
  prompt?: string;
  placeholder?: string;
  /** Start collapsed behind a button when there is no note yet. */
  collapsible?: boolean;
}

export function NoteEditor({ questionId, prompt, placeholder, collapsible = false }: EditorProps) {
  const { note, loaded, saveNote } = useQuestionNote(questionId);
  const [draft, setDraft] = useState("");
  const [open, setOpen] = useState(!collapsible);
  const [status, setStatus] = useState<"idle" | "saving" | "saved" | "error">("idle");

  useEffect(() => {
    setDraft(note);
    if (note) setOpen(true);
  }, [note]);

  useEffect(() => {
    setOpen(!collapsible);
    setStatus("idle");
  }, [questionId, collapsible]);

  if (!loaded) return null;

  if (!open) {
    return (
      <div className="flex flex-wrap items-center gap-3 rounded-lg border border-dashed border-border p-3">
        <MessageSquareText className="h-4 w-4 text-primary" />
        <span className="flex-1 text-sm">{prompt}</span>
        <Button size="sm" variant="outline" onClick={() => setOpen(true)}>
          Answer in a note
        </Button>
      </div>
    );
  }

  const save = async () => {
    setStatus("saving");
    try {
      await saveNote(draft.trim());
      setStatus("saved");
    } catch {
      setStatus("error");
    }
  };

  return (
    <div className="space-y-2 rounded-lg border border-border p-3">
      {prompt && (
        <div className="flex items-start gap-2 text-sm font-medium">
          <MessageSquareText className="mt-0.5 h-4 w-4 shrink-0 text-primary" />
          <span>{prompt}</span>
        </div>
      )}
      <textarea
        value={draft}
        onChange={(e) => {
          setDraft(e.target.value);
          setStatus("idle");
        }}
        rows={3}
        placeholder={placeholder ?? "A sentence or two in your own words."}
        className="w-full resize-y rounded-md border border-border bg-background px-3 py-2 text-sm outline-none focus:border-primary"
      />
      <div className="flex items-center justify-end gap-3 text-xs text-muted">
        {status === "saved" && <span>Saved to your notes.</span>}
        {status === "error" && <span className="text-error">Could not save.</span>}
        <Button size="sm" variant="primary" onClick={() => void save()} disabled={status === "saving" || draft.trim() === note.trim()}>
          Save note
        </Button>
      </div>
    </div>
  );
}

/** The optional self-explanation prompt after a worked solution. */
export function SelfExplain({ questionId }: { questionId: number }) {
  return (
    <NoteEditor
      questionId={questionId}
      prompt={promptFor(questionId)}
      placeholder="Answer in your own words, then compare with the takeaways if the solution has them."
      collapsible
    />
  );
}
