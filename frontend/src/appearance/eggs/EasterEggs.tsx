/**
 * Global easter eggs (Makeover.md §6): Konami code, logo ×7, the idle
 * screensaver, clock eggs on answers, Fermat's margin, the Q.E.D. stamp,
 * "quack", the late-night nudge and the Vaporwave unlock. Renders the
 * egg overlays and toast stack. Everything is off when settings.eggs is.
 */

import { useCallback, useEffect, useState } from "react";

import { emit, on } from "../events";
import { effectsLevel, useAppearance } from "../store";
import { VAPORWAVE_ID, shouldUnlockVaporwave } from "./catalogue";
import {
  createBurstCounter,
  createKonamiDetector,
  createWordDetector,
  endsWithQed,
  fillsMargin,
  isLateNight,
  timeEgg,
} from "./detectors";
import { eggFound, findEgg, whenReady } from "./found";
import { CrtOverlay, EGG_CSS, QedStamp, ToastStack } from "./overlays";
import { Screensaver } from "./Screensaver";
import { showToast } from "./toast";

export { barrelRoll } from "./barrelRoll";

const IDLE_MS = 5 * 60 * 1000;
const LOGO_CLICKS = 7;
const LOGO_WINDOW_MS = 3000;
const FERMAT =
  "I have discovered a truly marvelous proof of this, which this margin is too narrow to contain.";

/** Session-wide: one late-night nudge per app run, CRT survives remounts. */
let lateNightShown = false;
let crtSession = false;

function isEditable(t: EventTarget | null): boolean {
  if (!(t instanceof HTMLElement)) return false;
  return t.isContentEditable || t.tagName === "INPUT" || t.tagName === "TEXTAREA" || t.tagName === "SELECT";
}

export function EasterEggs() {
  const eggs = useAppearance((s) => s.settings.eggs);
  const focus = useAppearance((s) => s.settings.focus || (s.settings.focusInTimed && s.timedActive));
  const [crt, setCrt] = useState(crtSession);
  const [stamp, setStamp] = useState(0);
  const [saver, setSaver] = useState(false);

  useEffect(() => {
    if (!eggs) return;
    const offs: (() => void)[] = [];
    const listen = <K extends keyof WindowEventMap>(type: K, fn: (e: WindowEventMap[K]) => void) => {
      const opts = { capture: true, passive: true };
      window.addEventListener(type, fn, opts);
      offs.push(() => window.removeEventListener(type, fn, opts));
    };

    /* Idle → screensaver */
    let lastActive = Date.now();
    let idle = false;
    let timer: ReturnType<typeof setTimeout> | undefined;
    const arm = (ms: number) => {
      clearTimeout(timer);
      timer = setTimeout(check, ms);
    };
    const check = () => {
      const since = Date.now() - lastActive;
      if (since < IDLE_MS) {
        arm(IDLE_MS - since);
        return;
      }
      idle = true;
      emit({ type: "idle", idle: true });
      if (effectsLevel() > 0) setSaver(true);
    };
    const active = () => {
      lastActive = Date.now();
      if (!idle) return;
      idle = false;
      setSaver(false);
      emit({ type: "idle", idle: false });
      arm(IDLE_MS);
    };
    arm(IDLE_MS);
    offs.push(() => clearTimeout(timer));
    for (const type of ["pointermove", "pointerdown", "wheel", "touchstart"] as const) listen(type, active);

    /* Keyboard: Konami (outside fields), quack (anywhere) */
    const konami = createKonamiDetector();
    const quack = createWordDetector("quack");
    listen("keydown", (e) => {
      active();
      if (e.isComposing) return;
      if (quack(e.key)) {
        showToast("Quack. (Rubber duck debugging since 1999.)", { icon: "duck", key: "quack" });
        findEgg("quack");
      }
      if (!isEditable(e.target) && konami(e.key)) {
        crtSession = !crtSession;
        setCrt(crtSession);
        if (crtSession) {
          showToast("Cheat code accepted. Enter it again to switch the scanlines off.", { icon: "↑↑↓↓", key: "konami" });
        }
        findEgg("konami");
      }
    });

    /* Logo ×7 */
    const logo = createBurstCounter(LOGO_CLICKS, LOGO_WINDOW_MS);
    offs.push(
      on("logo_click", () => {
        if (logo.hit(Date.now())) {
          const already = eggFound("developer");
          showToast(already ? "No need, you are already a developer." : "You are now a developer!", { icon: "{ }", key: "dev" });
          findEgg("developer");
          return;
        }
        const left = LOGO_CLICKS - logo.count();
        if (left <= 3 && !eggFound("developer")) {
          showToast(`You are now ${left} step${left === 1 ? "" : "s"} away from being a developer.`, { key: "dev" });
        }
      }),
    );

    /* Clock eggs */
    let lastClock = "";
    offs.push(
      on("answer", () => {
        const now = new Date();
        const egg = timeEgg(now);
        if (!egg) return;
        const stampKey = `${now.toDateString()} ${now.getHours()}:${now.getMinutes()}`;
        if (stampKey === lastClock) return;
        lastClock = stampKey;
        showToast(egg === "pi-time" ? "π o'clock." : "1337.", { icon: egg === "pi-time" ? "π" : "#" });
        findEgg(egg);
      }),
    );

    /* Notes: Fermat's margin and the Q.E.D. stamp */
    let lastFermat = "";
    let lastQed = "";
    offs.push(
      on("note_saved", ({ text, limit }) => {
        if (fillsMargin(text, limit) && text !== lastFermat) {
          lastFermat = text;
          showToast(FERMAT, { icon: "✎", key: "fermat" });
          findEgg("fermat");
        }
        if (endsWithQed(text) && text !== lastQed) {
          lastQed = text;
          if (effectsLevel() > 0) setStamp((n) => n + 1);
          else showToast("Q.E.D.", { icon: "∎", key: "qed" });
          findEgg("qed");
        }
      }),
    );

    /* Late night: one gentle nudge per session */
    const nightTimer = setInterval(() => {
      if (lateNightShown || !isLateNight(new Date())) return;
      lateNightShown = true;
      showToast("It's past 2 am. Sleep is when today's practice sticks; the questions will keep until morning.", {
        icon: "☾",
      });
    }, 60_000);
    offs.push(() => clearInterval(nightTimer));

    /* Vaporwave: ten secrets unlock the hidden preset */
    const checkVaporwave = () => {
      const s = useAppearance.getState();
      if (!s.ready || !s.settings.eggs || !shouldUnlockVaporwave(s.secrets)) return;
      s.addSecret(VAPORWAVE_ID);
      emit({ type: "egg", id: VAPORWAVE_ID });
      emit({ type: "unlock", what: `preset:${VAPORWAVE_ID}` });
      showToast("A E S T H E T I C unlocked in Themes.", { icon: "◢◤", key: "vaporwave" });
    };
    whenReady(checkVaporwave);
    offs.push(useAppearance.subscribe((s, prev) => {
      if (s.secrets !== prev.secrets || s.settings.eggs !== prev.settings.eggs) checkVaporwave();
    }));

    return () => {
      offs.forEach((off) => off());
      if (idle) emit({ type: "idle", idle: false });
      setSaver(false);
    };
  }, [eggs]);

  const onCorner = useCallback(() => {
    showToast("Right in the corner. Exactly.", { icon: "◰", key: "corner" });
    findEgg("corner");
  }, []);
  const endStamp = useCallback(() => setStamp(0), []);

  return (
    <>
      <style>{EGG_CSS}</style>
      {eggs && crt && !focus && <CrtOverlay />}
      {eggs && saver && <Screensaver onCorner={onCorner} />}
      {eggs && stamp > 0 && <QedStamp key={stamp} onDone={endStamp} />}
      <ToastStack paused={focus} />
    </>
  );
}
