/**
 * Seasonal layer (Makeover.md §5.17): a slim, dismissible banner at the top
 * of the window for the day's events, and <html data-season-event="ids">
 * (space-separated, so CSS can match with [data-season-event~="pi-day"])
 * while any event runs. Club events come from configs.CLUB_EVENTS. Off when
 * settings.seasonal is; the banner hides in focus mode.
 */

import { useEffect, useMemo, useState } from "react";

import { ipc } from "../../lib/ipc";
import { Logo } from "../brand/Logo";
import { getPref, setPref } from "../prefs";
import { useAppearance } from "../store";
import { activeEvents, parseClubEvents, type ClubEvent, type SeasonEvent } from "./calendar";

const DISMISS_KEY = "seasonal.dismissed";
const ROW_PX = 30;

const CSS = `
.amp-season { position: fixed; top: 0; left: 0; right: 0; z-index: 9980; font-family: var(--font-family); }
.amp-season-row { position: relative; height: ${ROW_PX}px; display: flex; align-items: center; justify-content: center;
  gap: 8px; padding: 0 40px 0 12px; white-space: nowrap; overflow: hidden; font-size: 13px;
  background: color-mix(in srgb, var(--primary) 14%, var(--surface)); color: var(--text);
  border-bottom: 1px solid color-mix(in srgb, var(--primary) 30%, var(--border));
  animation: amp-season-in 0.25s ease-out; }
.amp-season-row .glyph { flex: none; color: var(--primary); font-weight: 700; font-family: var(--font-heading, var(--font-family)); }
.amp-season-row .glyph .amp-logo { width: 62px; }
.amp-season-row .name { flex: none; font-weight: 600; }
.amp-season-row .msg { min-width: 0; overflow: hidden; text-overflow: ellipsis; opacity: 0.85; }
.amp-season-row .est { flex: none; font-size: 11px; color: var(--muted); }
.amp-season-row button { position: absolute; right: 6px; top: 50%; transform: translateY(-50%); width: 22px; height: 22px;
  display: grid; place-items: center; border: 0; border-radius: 6px; background: transparent; color: var(--muted);
  cursor: pointer; font-size: 15px; line-height: 1; }
.amp-season-row button:hover { background: color-mix(in srgb, var(--text) 10%, transparent); color: var(--text); }
.amp-season-row button:focus-visible { outline: 2px solid var(--primary); outline-offset: 1px; }
@keyframes amp-season-in { from { transform: translateY(-100%); } to { transform: none; } }
:root[data-reduced-motion="on"] .amp-season-row { animation: none; }
`;

function loadDismissed(): Set<string> {
  const v = getPref<unknown>(DISMISS_KEY, []);
  return new Set(Array.isArray(v) ? v.filter((x): x is string => typeof x === "string") : []);
}

function saveDismissed(set: Set<string>, year: number): void {
  // Keep only this year's and last year's entries.
  const keep = [...set].filter((k) => Number(k.slice(k.lastIndexOf(":") + 1)) >= year - 1);
  setPref(DISMISS_KEY, keep);
}

/** Local calendar day as "YYYY-M-D"; changes at midnight. */
function dayKey(d: Date): string {
  return `${d.getFullYear()}-${d.getMonth() + 1}-${d.getDate()}`;
}

function fromDayKey(k: string): Date {
  const [y, m, d] = k.split("-").map(Number);
  return new Date(y, m - 1, d, 12);
}

function Row({ ev, onDismiss }: { ev: SeasonEvent; onDismiss: () => void }) {
  return (
    <div className="amp-season-row" role="note" aria-label={ev.name}>
      <span className="glyph" aria-hidden="true">
        {ev.kind === "club" ? <Logo name="inline" /> : ev.glyph}
      </span>
      <span className="name">{ev.name}</span>
      {ev.message && <span className="msg">· {ev.message}</span>}
      {ev.approximate && (
        <span className="est" title="Estimated date: it depends on the moon sighting.">
          (est.)
        </span>
      )}
      <button type="button" onClick={onDismiss} aria-label={`Dismiss ${ev.name}`} title="Dismiss until next year">
        ×
      </button>
    </div>
  );
}

export function SeasonalLayer() {
  const enabled = useAppearance((s) => s.settings.seasonal);
  const focus = useAppearance((s) => s.settings.focus || (s.settings.focusInTimed && s.timedActive));
  const [club, setClub] = useState<ClubEvent[]>([]);
  const [today, setToday] = useState(() => dayKey(new Date()));
  const [dismissed, setDismissed] = useState(loadDismissed);

  useEffect(() => {
    if (!enabled) return;
    let alive = true;
    ipc
      .get_config("CLUB_EVENTS")
      .then((raw) => alive && setClub(parseClubEvents(raw)))
      .catch(() => {});
    return () => {
      alive = false;
    };
  }, [enabled]);

  // Roll over at midnight, and re-check when the window comes back.
  useEffect(() => {
    if (!enabled) return;
    let timer: ReturnType<typeof setTimeout>;
    const schedule = () => {
      const now = new Date();
      const next = new Date(now.getFullYear(), now.getMonth(), now.getDate() + 1, 0, 0, 5);
      timer = setTimeout(() => {
        setToday(dayKey(new Date()));
        schedule();
      }, next.getTime() - now.getTime());
    };
    const onVis = () => {
      if (!document.hidden) setToday(dayKey(new Date()));
    };
    schedule();
    document.addEventListener("visibilitychange", onVis);
    return () => {
      clearTimeout(timer);
      document.removeEventListener("visibilitychange", onVis);
    };
  }, [enabled]);

  const events = useMemo(() => (enabled ? activeEvents(fromDayKey(today), club) : []), [enabled, today, club]);
  const ids = events.map((e) => e.id).join(" ");

  useEffect(() => {
    const root = document.documentElement;
    if (ids) root.setAttribute("data-season-event", ids);
    else root.removeAttribute("data-season-event");
    return () => root.removeAttribute("data-season-event");
  }, [ids]);

  const year = fromDayKey(today).getFullYear();
  const shown = focus ? [] : events.filter((e) => !dismissed.has(`${e.id}:${year}`));
  if (!shown.length) return null;

  const dismiss = (id: string) => {
    const next = new Set(dismissed).add(`${id}:${year}`);
    setDismissed(next);
    saveDismissed(next, year);
  };

  return (
    <div className="amp-season">
      <style>{`${CSS}\n#root { padding-top: ${shown.length * ROW_PX}px; }`}</style>
      {shown.map((ev) => (
        <Row key={ev.id} ev={ev} onDismiss={() => dismiss(ev.id)} />
      ))}
    </div>
  );
}
