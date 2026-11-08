/**
 * "From a lecture": paste the lecture's keywords, confirm what each one
 * matched in the taxonomy and tags, then practise. Matching is offline
 * (app/core/concepts.py: spelling variants, abbreviations from
 * keyword_aliases.json). Short terms are ambiguous, so nothing is used until
 * the student has seen the matches; weak or many-way ties start unticked.
 * Keyword sets can be saved ("Monday's lecture") and reloaded.
 */

import { useEffect, useMemo, useState } from "react";
import { BookmarkPlus, Search, Trash2 } from "lucide-react";

import { Button } from "../ui/Button";
import { cn } from "../../lib/cn";
import { ipc, type ConceptRef, type Filters, type KeywordTerm, type LectureSet } from "../../lib/ipc";

interface Props {
  filters: Filters;
  /** The confirmed concepts (deduplicated). */
  onChange: (concepts: ConceptRef[]) => void;
}

const KIND_LABEL: Record<string, string> = { subtopic: "subtopic", branch: "branch", topic: "topic", tag: "technique" };
const keyOf = (kind: string, path: string) => `${kind}:${path}`;

export function LecturePanel({ filters, onChange }: Props) {
  const [text, setText] = useState("");
  const [terms, setTerms] = useState<KeywordTerm[] | null>(null);
  const [ticked, setTicked] = useState<Set<string>>(new Set());
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sets, setSets] = useState<LectureSet[]>([]);
  const [saveName, setSaveName] = useState("");

  useEffect(() => {
    ipc.list_lecture_sets().then(setSets).catch(() => setSets([]));
  }, []);

  const find = async (input: string, preselect?: ConceptRef[]) => {
    if (!input.trim()) return;
    setBusy(true);
    setError(null);
    try {
      const found = await ipc.match_keywords(input, filters);
      setTerms(found);
      const next = new Set<string>();
      for (const t of found) {
        for (const m of t.matches) {
          const want = preselect
            ? preselect.some((c) => c.kind === m.kind && (c.path ? c.path === m.path : c.label === m.label))
            : m.selected;
          if (want) next.add(keyOf(m.kind, m.path));
        }
      }
      setTicked(next);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  };

  const confirmed = useMemo<ConceptRef[]>(() => {
    const seen = new Set<string>();
    const out: ConceptRef[] = [];
    for (const t of terms ?? []) {
      for (const m of t.matches) {
        const k = keyOf(m.kind, m.path);
        if (ticked.has(k) && !seen.has(k)) {
          seen.add(k);
          out.push({ kind: m.kind, label: m.label, path: m.path });
        }
      }
    }
    return out;
  }, [terms, ticked]);

  useEffect(() => {
    onChange(confirmed);
  }, [confirmed, onChange]);

  const toggle = (k: string) =>
    setTicked((prev) => {
      const next = new Set(prev);
      if (next.has(k)) next.delete(k);
      else next.add(k);
      return next;
    });

  const save = async () => {
    const name = saveName.trim();
    if (!name || confirmed.length === 0) return;
    setSets(await ipc.save_lecture_set(name, text, confirmed));
    setSaveName("");
  };

  const load = (set: LectureSet) => {
    setText(set.text);
    void find(set.text, set.concepts);
  };

  return (
    <div className="space-y-4">
      <div className="space-y-2">
        <label htmlFor="lectureKeywords" className="block text-sm font-medium text-text">
          Lecture keywords
        </label>
        <textarea
          id="lectureKeywords"
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) void find(text);
          }}
          rows={3}
          placeholder="eigenvalues, diagonalisation, repeated roots"
          className="w-full resize-y rounded-md border border-border bg-background px-3 py-2 text-sm outline-none focus:border-primary"
        />
        <div className="flex items-center justify-between gap-2">
          <p className="text-xs text-muted">Separate terms with commas or new lines. Abbreviations like SVD or CLT work.</p>
          <Button size="sm" variant="primary" onClick={() => void find(text)} disabled={busy || !text.trim()}>
            <Search className="h-4 w-4" />
            Find concepts
          </Button>
        </div>
        {error && <p className="text-sm text-error">{error}</p>}
      </div>

      {terms && (
        <div className="space-y-3">
          <p className="text-xs text-muted">
            Tick what your lecture covered. Questions are picked for each ticked concept separately, then mixed.
          </p>
          {terms.map((t) => (
            <div key={t.term} className="rounded-lg border border-border bg-background p-3">
              <div className="mb-2 text-sm font-semibold">“{t.term}”</div>
              {t.matches.length === 0 ? (
                <p className="text-xs text-muted">No match in this subject. Try another wording.</p>
              ) : (
                <ul className="space-y-1">
                  {t.matches.map((m) => {
                    const k = keyOf(m.kind, m.path);
                    return (
                      <li key={k}>
                        <label className="flex cursor-pointer items-start gap-2 text-sm">
                          <input
                            type="checkbox"
                            checked={ticked.has(k)}
                            onChange={() => toggle(k)}
                            className="mt-0.5 h-4 w-4 rounded border-border text-primary focus:ring-primary"
                          />
                          <span className="flex-1">
                            <span className="font-medium">{m.label}</span>{" "}
                            <span className="text-xs text-muted">
                              {KIND_LABEL[m.kind]}
                              {m.kind !== "tag" && m.kind !== "topic" ? ` · ${m.path}` : ""} · {m.count} questions
                              {m.via_alias ? ` · read as “${m.via_alias}”` : ""}
                            </span>
                          </span>
                        </label>
                      </li>
                    );
                  })}
                </ul>
              )}
            </div>
          ))}
          <div className="flex flex-wrap items-center gap-2">
            <input
              value={saveName}
              onChange={(e) => setSaveName(e.target.value)}
              placeholder="Save as… e.g. Monday's lecture"
              className="w-64 rounded-md border border-border bg-background px-3 py-1.5 text-sm outline-none focus:border-primary"
            />
            <Button size="sm" variant="outline" onClick={() => void save()} disabled={!saveName.trim() || confirmed.length === 0}>
              <BookmarkPlus className="h-4 w-4" />
              Save keyword set
            </Button>
            <span className="text-xs text-muted">{confirmed.length} concept{confirmed.length === 1 ? "" : "s"} ticked</span>
          </div>
        </div>
      )}

      {sets.length > 0 && (
        <div className="space-y-1">
          <div className="text-xs font-medium uppercase tracking-wide text-muted">Saved lectures</div>
          <ul className="flex flex-wrap gap-2">
            {sets.map((s) => (
              <li
                key={s.name}
                className={cn("flex items-center gap-1 rounded-full border border-border bg-background pl-3 text-sm")}
              >
                <button type="button" className="py-1 hover:text-primary" onClick={() => load(s)} title={s.text}>
                  {s.name}
                </button>
                <button
                  type="button"
                  className="rounded-full p-1.5 text-muted hover:text-error"
                  title="Delete this saved lecture"
                  onClick={() => void ipc.delete_lecture_set(s.name).then(setSets)}
                >
                  <Trash2 className="h-3.5 w-3.5" />
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
