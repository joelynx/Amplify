/**
 * results.newspaper: a front page whose headline is built from the numbers
 * ("STUDENT SOLVES SEVEN UNAIDED"), with the full tally in a "By the
 * numbers" box. With full whimsy the page spins in, once.
 */

import type { SessionSummary } from "../../events";
import {
  HEADING, type StyleProps, DoneButton, Enter, cap, clock, longTime, modeLabel, plural, stats, useGreetingName, words,
} from "../shared";

/** Front-page headline from the session numbers; never mocking. */
export function headline(s: SessionSummary, name = ""): string {
  const who = (name || "Student").toUpperCase();
  const w = (n: number) => words(n).toUpperCase();
  if (s.answered <= 0) return "QUIET DAY AT THE DESK";
  if (s.unaided >= s.answered) return s.answered === 1 ? `${who} SOLVES IT UNAIDED` : `${who} SOLVES ALL ${w(s.answered)} UNAIDED`;
  if (s.unaided > 0) return `${who} SOLVES ${w(s.unaided)} UNAIDED`;
  if (s.assisted > 0) return `${who} CRACKS ${w(s.assisted)} WITH HELP`;
  if (s.partial > 0) return `${who} MAKES HEADWAY ON ${w(s.partial)}`;
  return `${who} TAKES ON ${w(s.answered)} TOUGH ${plural(s.answered, "QUESTION", "QUESTIONS")}`;
}

function deck(s: SessionSummary): string {
  if (s.answered > 2 && s.unaided >= s.answered) return "A clean sweep; city rejoices";
  if (s.toReview > 0) return `${cap(words(s.toReview))} ${plural(s.toReview, "question")} filed for a rematch in the review queue`;
  return "Nothing left over for review";
}

function story(s: SessionSummary, name: string): string {
  const who = name || "the student";
  return (
    `In a session lasting ${longTime(s.elapsedMs)}, ${who} answered ${words(s.answered)} ${plural(s.answered, "question")}: ` +
    `${words(s.unaided)} solved unaided, ${words(s.assisted)} with help, ${words(s.partial)} in part and ${words(s.missed)} missed. ` +
    (s.toReview > 0
      ? `${cap(words(s.toReview))} ${plural(s.toReview, "goes", "go")} into the review queue for another try.`
      : "None of them go into the review queue.")
  );
}

export function Newspaper({ s, level, onClose }: StyleProps) {
  const name = useGreetingName();
  const today = new Intl.DateTimeFormat(undefined, { weekday: "long", day: "numeric", month: "long", year: "numeric" }).format(new Date());
  const rule = "color-mix(in srgb, var(--text) 75%, transparent)";

  return (
    <Enter
      animate={level > 0}
      from={level > 1 ? "rotate(-720deg) scale(0.1)" : "scale(0.96)"}
      duration={level > 1 ? 900 : 300}
      easing="cubic-bezier(.2,.7,.25,1)"
      className="border border-border bg-surface p-5 text-text shadow-md sm:p-6"
    >
      <header className="text-center">
        <p className="text-[0.65rem] uppercase tracking-[0.25em] text-muted">Late edition · Price: one good question</p>
        <h2 className="mt-1 text-3xl font-black tracking-tight sm:text-4xl" style={HEADING}>The Amplify Times</h2>
        <div className="mt-2 flex justify-between border-y-[3px] border-double py-1 text-[0.7rem] uppercase tracking-wider" style={{ borderColor: rule }}>
          <span>{today}</span>
          <span>{modeLabel(s.mode)} edition</span>
        </div>
      </header>

      <h3 className="mt-4 text-center text-2xl font-black uppercase leading-tight sm:text-3xl" style={HEADING}>
        {headline(s, name)}
      </h3>
      <p className="mt-1 text-center text-sm italic text-muted">{deck(s)}</p>

      <div className="mt-4 grid gap-4 sm:grid-cols-[1fr_11rem]">
        <p className="text-sm leading-relaxed [hyphens:auto] first-letter:float-left first-letter:mr-1.5 first-letter:text-4xl first-letter:font-black first-letter:leading-none">
          {story(s, name)}
        </p>
        <aside className="border-2 p-3 text-sm" style={{ borderColor: rule }}>
          <h4 className="border-b pb-1 text-xs font-black uppercase tracking-widest" style={{ ...HEADING, borderColor: rule }}>
            By the numbers
          </h4>
          <dl className="mt-1.5 space-y-0.5">
            {stats(s).map((st) => (
              <div key={st.key} className="flex justify-between gap-2">
                <dt>{st.label}</dt>
                <dd className="font-bold tabular-nums">{st.value}</dd>
              </div>
            ))}
            <div className="flex justify-between gap-2">
              <dt>Time</dt>
              <dd className="font-bold tabular-nums">{clock(s.elapsedMs)}</dd>
            </div>
          </dl>
        </aside>
      </div>

      <footer className="mt-4 flex items-center justify-between gap-3 border-t pt-3" style={{ borderColor: rule }}>
        <p className="text-xs text-muted">
          Forecast: {s.toReview} {plural(s.toReview, "review")} expected
        </p>
        <DoneButton onClose={onClose} label="Fold the paper" />
      </footer>
    </Enter>
  );
}
