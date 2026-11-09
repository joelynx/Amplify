/**
 * results.terminal: the session as a timestamped log that types itself out
 * line by line and ends in `exit 0`. Start time is now minus the elapsed time.
 */

import { useState } from "react";

import { MONO, type StyleProps, hms, screenColors, useAnimClock, useBlink, usePaletteDark } from "../shared";

const LINE_MS = 140;

function stamp(d: Date): string {
  const p = (n: number) => String(n).padStart(2, "0");
  return `${p(d.getHours())}:${p(d.getMinutes())}:${p(d.getSeconds())}`;
}

type Tone = "ok" | "warn" | "plain" | "prompt";
interface LogLine {
  time?: string;
  text: string;
  tone: Tone;
}

export function Terminal({ s, level, onClose }: StyleProps) {
  const dark = usePaletteDark();
  const { bg, fg } = screenColors(dark);
  const [end] = useState(() => new Date());
  const start = stamp(new Date(end.getTime() - s.elapsedMs));
  const now = stamp(end);
  const kv = (k: string, v: string | number) => `${k.padEnd(14, " ")}${v}`;

  const lines: LogLine[] = [
    { time: start, text: `session start  mode=${s.mode || "quiz"}`, tone: "plain" },
    { time: now, text: kv("answered", s.answered), tone: "plain" },
    { time: now, text: kv("  unaided", s.unaided), tone: "ok" },
    { time: now, text: kv("  with help", s.assisted), tone: "plain" },
    { time: now, text: kv("  partial", s.partial), tone: s.partial ? "warn" : "plain" },
    { time: now, text: kv("  missed", s.missed), tone: "plain" },
    { time: now, text: kv("review queue", `+${s.toReview}`), tone: "plain" },
    { time: now, text: kv("elapsed", hms(s.elapsedMs)), tone: "plain" },
    { time: now, text: "[ OK ] session closed", tone: "ok" },
    { text: "$ exit 0", tone: "prompt" },
  ];

  const t = useAnimClock(level > 0, lines.length * LINE_MS + 200);
  const shown = t === Infinity ? lines.length : Math.min(lines.length, Math.floor(t / LINE_MS));
  const caret = useBlink<HTMLSpanElement>(level > 0);
  const mix = dark ? 45 : 25; // light palettes invert the screen; keep their deep state colours faint
  const tone = (k: Tone) =>
    k === "ok" ? `color-mix(in srgb, var(--success) ${mix}%, ${fg})` : k === "warn" ? `color-mix(in srgb, var(--warning) ${mix}%, ${fg})` : fg;
  const dim = `color-mix(in srgb, ${fg} 68%, ${bg})`;

  return (
    <div className="overflow-hidden rounded-md border border-border shadow-md" style={{ ...MONO, background: bg, color: fg }}>
      <div className="flex items-center justify-between border-b px-3 py-1.5 text-xs" style={{ borderColor: dim, color: dim }}>
        <span>~/amplify/session.log</span>
        <span>tty1</span>
      </div>
      <pre className="m-0 overflow-x-auto whitespace-pre px-4 py-3 text-[0.8rem] leading-relaxed sm:text-sm" style={{ fontFamily: "inherit" }}>
        {lines.map((l, i) => (
          <div key={i} style={{ visibility: i < shown ? "visible" : "hidden" }}>
            {l.time && <span style={{ color: dim }}>[{l.time}] </span>}
            <span style={{ color: tone(l.tone), fontWeight: l.tone === "prompt" ? 700 : undefined }}>{l.text}</span>
          </div>
        ))}
        <span ref={caret} aria-hidden style={{ visibility: shown >= lines.length ? "visible" : "hidden" }}>█</span>
      </pre>
      {onClose && (
        <div className="flex justify-end border-t px-3 py-2" style={{ borderColor: dim }}>
          <button
            type="button"
            onClick={onClose}
            className="px-2 py-1 text-sm focus:outline-none focus-visible:ring-2 focus-visible:ring-primary"
            style={{ color: fg, background: "transparent", fontFamily: "inherit" }}
          >
            [ close ]
          </button>
        </div>
      )}
    </div>
  );
}
