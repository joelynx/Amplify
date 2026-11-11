/**
 * "This hint / solution is unusable" (content_flags, migration 011).
 *
 * `Flaggable` wraps a hint or solution: it adds a "Report a problem" control
 * under the text, and once flagged shows a notice instead of the text (the
 * student can still open it, or take the flag back). Settings lists the flags.
 */

import { useCallback, useEffect, useState, type ReactNode } from "react";
import { Flag } from "lucide-react";

import { ipc, type FlagPart } from "../../lib/ipc";

const PART_LABEL: Record<FlagPart, string> = { hint: "hint", solution: "solution" };

/** Load and change one question's flags. */
export function useContentFlags(questionId: number) {
  const [flags, setFlags] = useState<FlagPart[]>([]);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    let cancelled = false;
    setFlags([]);
    setFailed(false);
    ipc
      .get_content_flags([questionId])
      .then((all) => {
        if (!cancelled) setFlags(all[String(questionId)] ?? []);
      })
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, [questionId]);

  const setFlag = useCallback(
    async (part: FlagPart, on: boolean) => {
      setFailed(false);
      setFlags((f) => (on ? [...f.filter((p) => p !== part), part] : f.filter((p) => p !== part)));
      try {
        await ipc.set_content_flag(questionId, part, on);
      } catch {
        setFlags((f) => (on ? f.filter((p) => p !== part) : [...f, part]));
        setFailed(true);
      }
    },
    [questionId],
  );

  return { flags, failed, setFlag };
}

interface FlaggableProps {
  questionId: number;
  part: FlagPart;
  children: ReactNode;
}

export function Flaggable({ questionId, part, children }: FlaggableProps) {
  const { flags, failed, setFlag } = useContentFlags(questionId);
  const [showAnyway, setShowAnyway] = useState(false);
  const flagged = flags.includes(part);
  const label = PART_LABEL[part];

  useEffect(() => setShowAnyway(false), [questionId]);

  const link = "underline underline-offset-2 hover:text-text";

  return (
    <div data-ui={`flaggable-${part}`} className="space-y-2">
      {flagged && (
        <p role="status" className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-muted">
          <span className="inline-flex items-center gap-1.5 font-medium text-text">
            <Flag className="h-3.5 w-3.5" />
            You flagged this {label} as unusable.
          </span>
          <button type="button" className={link} onClick={() => setShowAnyway((v) => !v)}>
            {showAnyway ? "Hide it" : "Show it anyway"}
          </button>
          <button type="button" className={link} onClick={() => void setFlag(part, false)}>
            Remove flag
          </button>
        </p>
      )}
      {(!flagged || showAnyway) && children}
      {!flagged && (
        <div className="flex justify-end">
          <button
            type="button"
            title={`Hide this ${label} and list it in Settings for repair`}
            className="inline-flex items-center gap-1.5 text-xs text-muted hover:text-text"
            onClick={() => void setFlag(part, true)}
          >
            <Flag className="h-3.5 w-3.5" />
            Report a problem with this {label}
          </button>
        </div>
      )}
      {failed && (
        <p role="alert" className="text-xs text-error">
          The flag could not be saved. Try again.
        </p>
      )}
    </div>
  );
}
