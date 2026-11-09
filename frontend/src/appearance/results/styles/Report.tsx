/** results.report: the default report card. A headline number, a stacked bar and one tile per stat. */

import { HEADING, type StyleProps, DoneButton, clock, countAt, modeLabel, stats, useAnimClock } from "../shared";

const SEGMENTS = [
  { key: "unaided", label: "Unaided", color: "var(--success)" },
  { key: "assisted", label: "With help", color: "var(--primary)" },
  { key: "partial", label: "Partial", color: "var(--warning)" },
  { key: "missed", label: "Missed", color: "var(--muted)" },
] as const;

export function Report({ s, level, onClose }: StyleProps) {
  const t = useAnimClock(level > 0, 1400);
  const total = Math.max(s.answered, s.unaided + s.assisted + s.partial + s.missed, 1);
  const line = `Session complete: ${s.answered} answered, ${s.unaided} unaided, ${s.toReview} to review`;

  return (
    <section data-ui="card" className="rounded-lg border border-border bg-surface p-5 text-text shadow-sm">
      <header className="flex items-baseline justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wider text-muted">Session report · {modeLabel(s.mode)}</p>
          <h2 className="mt-1 text-2xl font-semibold" style={HEADING}>
            <span className="tabular-nums">{countAt(t, s.unaided, 0, 900)}</span> of{" "}
            <span className="tabular-nums">{s.answered}</span> solved unaided
          </h2>
        </div>
        <div className="text-right">
          <div className="text-lg font-semibold tabular-nums">{clock(s.elapsedMs)}</div>
          <div className="text-xs text-muted">elapsed</div>
        </div>
      </header>

      <div className="mt-4 flex h-3 w-full overflow-hidden rounded-full bg-background" role="img"
        aria-label={`${s.unaided} unaided, ${s.assisted} with help, ${s.partial} partial, ${s.missed} missed`}>
        {SEGMENTS.map((seg, i) => {
          const share = (s[seg.key] / total) * 100;
          const grow = countAt(t, 1000, 150 + i * 120, 600) / 1000;
          return share > 0 ? (
            <div key={seg.key} style={{ width: `${share * grow}%`, background: seg.color }} />
          ) : null;
        })}
      </div>
      <ul className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-xs text-muted">
        {SEGMENTS.map((seg) => (
          <li key={seg.key} className="flex items-center gap-1.5">
            <span className="inline-block h-2.5 w-2.5 rounded-sm" style={{ background: seg.color }} />
            {seg.label}
          </li>
        ))}
      </ul>

      <dl className="mt-4 grid grid-cols-2 gap-2 sm:grid-cols-3">
        {stats(s).map((st, i) => (
          <div key={st.key} className="rounded-md border border-border bg-background px-3 py-2">
            <dt className="text-xs text-muted">{st.label}</dt>
            <dd className="text-2xl font-semibold tabular-nums" style={HEADING}>
              {countAt(t, st.value, 100 + i * 90, 700)}
            </dd>
          </div>
        ))}
      </dl>

      <footer className="mt-4 flex flex-wrap items-center justify-between gap-3">
        <p className="text-sm text-muted">{line}</p>
        <DoneButton onClose={onClose} />
      </footer>
    </section>
  );
}
