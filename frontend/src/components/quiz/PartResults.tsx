/**
 * Per-part result of a graded answer (answer_key_spec.md): what the student
 * gave, the expected value with its unit (or the checklist of key points), and
 * the credit. Used after a submission (where `action` adds the self-assessment
 * buttons to parts awaiting them) and on the review page.
 */

import type { ReactNode } from "react";

import { LatexContent } from "../browser/LatexContent";
import { cn } from "../../lib/cn";
import type { PartResult } from "../../lib/ipc";
import {
  MARK_LABELS,
  creditLabel,
  expectedText,
  expressionTex,
  inputText,
  partLabel,
  readNote,
} from "../../lib/answerKey";

interface Props {
  parts: PartResult[];
  /** Rendered under each part (the Got it / Partial / Missed buttons). */
  action?: (part: PartResult, index: number) => ReactNode;
  /** A retry is allowed: say which parts were wrong, show no expected answers. */
  withheld?: boolean;
}

export function PartResults({ parts, action, withheld = false }: Props) {
  return (
    <ul className="divide-y divide-border overflow-hidden rounded-md border border-border bg-background">
      {parts.map((p, i) => {
        const note = readNote(p);
        const given = inputText(p).trim();
        return (
          <li key={i} className="space-y-2 px-3 py-2 text-sm">
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0">
                {p.label && <span className="mr-1.5 font-medium">{partLabel(p.label)}</span>}
                {p.ask && <span className="text-muted">{p.ask}</span>}
              </div>
              <CreditBadge credit={p.credit} mark={p.mark} unjudged={withheld} />
            </div>
            <dl className="grid grid-cols-[5.5rem_1fr] gap-x-3 gap-y-1">
              <dt className="text-xs font-medium uppercase tracking-wide text-muted">Yours</dt>
              <dd className="min-w-0 whitespace-pre-wrap break-words">
                {given || <em className="text-muted">no answer</em>}
                {note && <span className="ml-2 text-xs text-muted">({note})</span>}
              </dd>
              {!withheld && <Expected part={p} />}
            </dl>
            {action?.(p, i)}
          </li>
        );
      })}
    </ul>
  );
}

function Expected({ part }: { part: PartResult }) {
  const text = expectedText(part);
  let body: ReactNode = null;
  if (text != null) {
    body = <span className="font-medium">{text}</span>;
  } else if (part.kind === "expression" && part.expected != null) {
    body = <LatexContent source={expressionTex(part.expected)} />;
  } else if (part.kind === "points") {
    body = part.points.length ? (
      <ul className="list-disc space-y-1 pl-5">
        {part.points.map((pt, j) => (
          <li key={j}>
            <LatexContent source={pt} />
          </li>
        ))}
      </ul>
    ) : (
      <em className="text-muted">no checklist; compare with the solution</em>
    );
  }
  if (body == null) return null;
  return (
    <>
      <dt className="text-xs font-medium uppercase tracking-wide text-muted">
        {part.kind === "points" ? "Key points" : "Expected"}
      </dt>
      <dd className="min-w-0">{body}</dd>
    </>
  );
}

function CreditBadge({
  credit,
  mark,
  unjudged,
}: {
  credit: number | null;
  mark: PartResult["mark"];
  /** On a retry, self-assessed parts are not judged yet. */
  unjudged: boolean;
}) {
  const label = mark ? MARK_LABELS[mark] : credit == null && unjudged ? "—" : creditLabel(credit);
  return (
    <span
      className={cn(
        "flex-none rounded-full px-2 py-0.5 text-xs font-semibold",
        credit == null && "bg-muted/15 text-muted",
        credit != null && credit >= 1 && "bg-success/15 text-success",
        credit != null && credit > 0 && credit < 1 && "bg-warning/15 text-warning",
        credit != null && credit <= 0 && "bg-error/15 text-error",
      )}
    >
      {label}
    </span>
  );
}
