import { LatexContent } from "../../components/browser/LatexContent";

const PREVIEW_QUESTION = String.raw`Find the eigenvalues of $A = \begin{pmatrix} 2 & 1 \\ 1 & 2 \end{pmatrix}$.`;

/** A question as the quiz shows it: statement with an equation, an answer box,
 * and both feedback states. Reads the surrounding palette's tokens, so a
 * palette can be judged by how comfortable it is to study in. */
export function StudyPreview() {
  return (
    <div className="space-y-2 text-sm" style={{ color: "var(--text)" }}>
      <LatexContent source={PREVIEW_QUESTION} />
      <div className="flex items-center gap-2">
        <span
          className="flex-1 rounded-md border px-2 py-1 text-xs"
          style={{ borderColor: "var(--border)", background: "var(--surface)", color: "var(--text)" }}
        >
          1, 3
        </span>
        <span className="rounded-md px-2 py-1 text-xs font-medium" style={{ background: "var(--primary)", color: "var(--on-primary, #fff)" }}>
          Submit
        </span>
      </div>
      <div className="flex flex-wrap gap-2 text-xs">
        <span className="rounded-md border px-2 py-0.5" style={{ borderColor: "var(--success)", color: "var(--success)" }}>
          ✓ Correct · full credit
        </span>
        <span className="rounded-md border px-2 py-0.5" style={{ borderColor: "var(--error)", color: "var(--error)" }}>
          ✗ Expected 1, 3
        </span>
      </div>
      <p className="text-xs" style={{ color: "var(--muted)" }}>
        muted helper text
      </p>
    </div>
  );
}
