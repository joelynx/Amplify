/**
 * Answer input for one question: one row per answer-key part
 * (pipeline/answer_key_spec.md, `answer_fields`). A number box with the
 * expected unit as a suffix, option buttons labelled with both forms ("2 · b"),
 * True / False, or a free-text box.
 *
 * Submitting grades and locks in the auto-graded parts. Parts that need
 * self-assessment (`points`, and an `expression` that did not match) come back
 * with the expected answer / checklist, and only then take Got it / Partial /
 * Missed; a one-part question records on the click, several parts on Record.
 * A one-part numeric question stays: type, Enter, done.
 *
 * The parent owns the result (so it survives navigation) and the IPC calls.
 */

import { useRef, useState, type KeyboardEvent } from "react";
import { Send } from "lucide-react";

import { Button } from "../ui/Button";
import { Input } from "../ui/Input";
import { LatexContent } from "../browser/LatexContent";
import { PartResults } from "./PartResults";
import { cn } from "../../lib/cn";
import type { AnswerField, QuizAnswerResult, SelfMark } from "../../lib/ipc";
import {
  MARK_LABELS,
  awaitingIndices,
  canSubmit,
  creditLabel,
  marksPayload,
  nextTypedField,
  optionLabel,
  optionLetter,
  partLabel,
  splitLetters,
  toggleChoice,
} from "../../lib/answerKey";
import { recordAnswer } from "../../appearance/session";

interface Props {
  fields: AnswerField[];
  /** The last result for this question; null before submitting. */
  result: QuizAnswerResult | null;
  submit: (answers: string[]) => Promise<QuizAnswerResult>;
  assess: (marks: (SelfMark | null)[]) => Promise<QuizAnswerResult>;
  /** A result without `error` (errors are shown here and change nothing). */
  onResult: (result: QuizAnswerResult) => void;
  /** Shown instead of the inputs (e.g. the answer was opened before answering). */
  lockedNote?: string | null;
  disabled?: boolean;
  /** Narrow layout (PBS cards): labels above the inputs. */
  compact?: boolean;
  autoFocus?: boolean;
  /** A hint or the answer was opened first (for the session summary and sounds). */
  assisted?: boolean;
}

const MARKS: SelfMark[] = ["got_it", "partial", "missed"];

export function AnswerPanel({
  fields,
  result,
  submit,
  assess,
  onResult,
  lockedNote = null,
  disabled = false,
  compact = false,
  autoFocus = true,
  assisted = false,
}: Props) {
  const [inputs, setInputs] = useState<string[]>(() => fields.map(() => ""));
  const [marks, setMarks] = useState<Partial<Record<number, SelfMark>>>({});
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const refs = useRef<Array<HTMLInputElement | HTMLTextAreaElement | null>>([]);

  const parts = result?.parts ?? [];
  const phase = result?.pending ? "assess" : result && !result.retry ? "done" : "edit";
  const locked = busy || disabled;

  const run = async (call: () => Promise<QuizAnswerResult>, selfAssessed = false) => {
    setBusy(true);
    setError(null);
    try {
      const r = await call();
      if (r.error) {
        setError(r.error);
      } else {
        setMarks({});
        onResult(r);
        if (!r.pending && !r.retry) {
          recordAnswer({ credit: r.credit ?? (r.correct ? 1 : 0), assisted, selfAssessed });
        }
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "IPC error");
    } finally {
      setBusy(false);
    }
  };

  const send = () => {
    if (locked || !canSubmit(fields, inputs)) return;
    void run(() => submit(inputs));
  };

  const record = (picked: Partial<Record<number, SelfMark>>) => {
    const payload = marksPayload(parts, picked);
    if (payload && !busy) void run(() => assess(payload), true);
  };

  const setInput = (i: number, value: string) =>
    setInputs((prev) => prev.map((v, j) => (j === i ? value : v)));

  const onKey = (e: KeyboardEvent<HTMLInputElement | HTMLTextAreaElement>, i: number) => {
    if (e.key !== "Enter") return;
    if (e.currentTarget instanceof HTMLTextAreaElement && !(e.ctrlKey || e.metaKey)) return;
    e.preventDefault();
    const next = nextTypedField(fields, i);
    if (next >= 0) refs.current[next]?.focus();
    else send();
  };

  if (lockedNote) return <p className="text-sm text-muted">{lockedNote}</p>;
  if (fields.length === 0) return null;

  if (phase === "assess") {
    const awaiting = awaitingIndices(parts);
    const one = awaiting.length === 1;
    return (
      <div className="space-y-3">
        <p className="text-sm text-muted">
          {one
            ? "Compare your answer with the expected one, then mark it."
            : "Compare each part with the expected answer, mark it, then record."}
        </p>
        <PartResults
          parts={parts}
          action={(p, i) =>
            p.credit == null ? (
              <div className="flex flex-wrap items-center gap-1.5">
                {MARKS.map((m) => (
                  <Button
                    key={m}
                    size="sm"
                    variant={marks[i] === m ? "primary" : "outline"}
                    aria-pressed={marks[i] === m}
                    disabled={busy}
                    onClick={() => {
                      const next = { ...marks, [i]: m };
                      setMarks(next);
                      if (one) record(next);
                    }}
                  >
                    {MARK_LABELS[m]}
                  </Button>
                ))}
              </div>
            ) : null
          }
        />
        {result?.solution && <Solution source={result.solution} />}
        {!one && (
          <Button variant="primary" size="sm" onClick={() => record(marks)} disabled={busy || !marksPayload(parts, marks)}>
            Record
          </Button>
        )}
        {error && <p className="text-xs text-error">{error}</p>}
      </div>
    );
  }

  if (phase === "done" && result) {
    const credit = result.credit ?? (result.correct ? 1 : 0);
    return (
      <div className="space-y-3">
        <p className="text-sm">
          <span
            className={cn(
              "font-semibold",
              credit >= 1 && "text-success",
              credit > 0 && credit < 1 && "text-warning",
              credit <= 0 && "text-error",
            )}
          >
            {creditLabel(credit)}
          </span>
          {credit > 0 && credit < 1 && <span className="ml-2 text-muted">{Math.round(credit * 100)}% of the marks</span>}
        </p>
        {parts.length > 0 && <PartResults parts={parts} />}
        {result.solution && <Solution source={result.solution} />}
      </div>
    );
  }

  const firstTyped = nextTypedField(fields, -1);
  const textClass =
    "w-full min-w-0 bg-transparent px-3 text-sm outline-none disabled:cursor-not-allowed disabled:opacity-50";

  const field = (f: AnswerField, i: number) => {
    const name = [partLabel(f.label), f.ask].filter(Boolean).join(" ") || "answer";
    const setRef = (el: HTMLInputElement | HTMLTextAreaElement | null) => {
      refs.current[i] = el;
    };
    // Read-only rather than disabled while a call is in flight, so focus stays put for a retry.
    const bind = {
      value: inputs[i] ?? "",
      disabled,
      readOnly: busy,
      autoFocus: autoFocus && i === firstTyped,
      "aria-label": name,
    };
    if (f.kind === "number") {
      return (
        <div className="flex h-9 items-stretch overflow-hidden rounded-md border border-border bg-background focus-within:ring-2 focus-within:ring-primary">
          <input
            {...bind}
            ref={setRef}
            className={textClass}
            inputMode="decimal"
            autoComplete="off"
            placeholder="e.g. 12.5, 1/8, 1.2e5"
            onChange={(e) => setInput(i, e.target.value)}
            onKeyDown={(e) => onKey(e, i)}
          />
          {f.unit && (
            <span className="flex flex-none items-center border-l border-border bg-surface px-3 text-sm text-muted">
              {f.unit}
            </span>
          )}
        </div>
      );
    }
    if (f.kind === "choice" && f.options) {
      const picked = splitLetters(inputs[i] ?? "");
      return (
        <div className="flex flex-wrap items-center gap-1.5" role="group" aria-label={name}>
          {Array.from({ length: f.options }, (_, k) => {
            const letter = optionLetter(k);
            const on = picked.includes(letter);
            return (
              <Button
                key={letter}
                size="sm"
                variant={on ? "primary" : "outline"}
                aria-pressed={on}
                disabled={locked}
                onClick={() => setInput(i, toggleChoice(inputs[i] ?? "", letter, f.multi))}
              >
                {optionLabel(letter)}
              </Button>
            );
          })}
          {f.multi && <span className="text-xs text-muted">select every correct option</span>}
        </div>
      );
    }
    if (f.kind === "truefalse") {
      return (
        <div className="flex gap-1.5" role="group" aria-label={name}>
          {(["true", "false"] as const).map((v) => (
            <Button
              key={v}
              size="sm"
              variant={inputs[i] === v ? "primary" : "outline"}
              aria-pressed={inputs[i] === v}
              disabled={locked}
              onClick={() => setInput(i, inputs[i] === v ? "" : v)}
            >
              {v === "true" ? "True" : "False"}
            </Button>
          ))}
        </div>
      );
    }
    if (f.kind === "points") {
      return (
        <textarea
          {...bind}
          ref={setRef}
          rows={compact ? 2 : 3}
          className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm outline-none focus-visible:ring-2 focus-visible:ring-primary disabled:cursor-not-allowed disabled:opacity-50"
          placeholder="Your answer (optional): you'll compare it with the key points"
          onChange={(e) => setInput(i, e.target.value)}
          onKeyDown={(e) => onKey(e, i)}
        />
      );
    }
    // expression, or a choice whose option count is unknown
    return (
      <Input
        {...bind}
        ref={setRef}
        autoComplete="off"
        placeholder={
          f.kind === "choice" ? (f.multi ? "e.g. a, c or 1, 3" : "e.g. b or 2") : "Your answer (LaTeX is fine)"
        }
        onChange={(e) => setInput(i, e.target.value)}
        onKeyDown={(e) => onKey(e, i)}
      />
    );
  };

  return (
    <div className="space-y-3">
      {fields.map((f, i) => {
        const prior = result?.retry ? result.parts?.[i] : undefined;
        return (
          <div key={i} className={cn("flex flex-col gap-1.5", !compact && "sm:flex-row sm:items-start sm:gap-3")}>
            {(f.label || f.ask) && (
              <div className={cn("text-sm", !compact && "sm:w-44 sm:flex-none sm:pt-2")}>
                {f.label && <span className="mr-1.5 font-medium">{partLabel(f.label)}</span>}
                {f.ask && <span className="text-muted">{f.ask}</span>}
              </div>
            )}
            <div className="min-w-0 flex-1">
              {field(f, i)}
              {prior?.credit === 0 && <p className="mt-1 text-xs text-error">wrong</p>}
              {prior?.credit === 1 && <p className="mt-1 text-xs text-success">right</p>}
            </div>
          </div>
        );
      })}
      <div className="flex flex-wrap items-center gap-2">
        <Button variant="primary" size="sm" onClick={send} disabled={locked || !canSubmit(fields, inputs)}>
          <Send className="h-4 w-4" />
          Submit
        </Button>
        {result?.retry && <span className="text-xs text-error">Not quite: fix the parts marked wrong.</span>}
        {error && <span className="text-xs text-error">{error}</span>}
      </div>
    </div>
  );
}

function Solution({ source }: { source: string }) {
  return (
    <div className="overflow-hidden rounded-md border border-border">
      <div className="border-b border-border bg-surface px-3 py-1.5 text-xs font-medium uppercase tracking-wide text-muted">
        Solution
      </div>
      <div className="bg-background p-3">
        <LatexContent source={source} />
      </div>
    </div>
  );
}
