/**
 * Mounts the appearance system inside the router: applies the loadout to
 * <html>, installs the sound engine, turns navigation and clicks into app
 * events, and renders the global layers (wallpaper, easter eggs, seasonal
 * decorations).
 */

import { useEffect } from "react";
import { useLocation } from "react-router-dom";

import { ipc } from "../lib/ipc";
import { useSubjectStore } from "../state/subject";
import { applyToDocument } from "./apply";
import { BrandDefs } from "./brand/Logo";
import { EasterEggs } from "./eggs/EasterEggs";
import { emit } from "./events";
import { registerFonts } from "./fonts";
import { SeasonalLayer } from "./seasonal/SeasonalLayer";
import { installSound } from "./sound/engine";
import { focusActive, useAppearance } from "./store";
import { WallpaperLayer } from "./wallpaper/WallpaperLayer";

export function AppearanceRoot() {
  const { pathname } = useLocation();

  useEffect(() => {
    registerFonts();
    const apply = () => applyToDocument(useAppearance.getState(), focusActive());
    apply();
    const unsub = useAppearance.subscribe(apply);
    const mq = window.matchMedia?.("(prefers-reduced-motion: reduce)");
    mq?.addEventListener?.("change", apply);
    return () => {
      unsub();
      mq?.removeEventListener?.("change", apply);
    };
  }, []);

  useEffect(() => installSound(), []);

  // Day/night loadout switch, checked every minute.
  useEffect(() => {
    const tick = () => useAppearance.getState().syncDayNight();
    tick();
    const id = window.setInterval(tick, 60_000);
    const unsub = useAppearance.subscribe((st, prev) => {
      if (st.settings.dayNight !== prev.settings.dayNight || st.saved !== prev.saved) tick();
    });
    return () => {
      window.clearInterval(id);
      unsub();
    };
  }, []);

  // One "reviews due" nudge per app start (sound).
  useEffect(() => {
    const t = window.setTimeout(() => {
      ipc
        .get_review_summary(useSubjectStore.getState().active)
        .then((r) => {
          if (r.counts.due > 0) emit({ type: "review_due", count: r.counts.due });
        })
        .catch(() => undefined);
    }, 2500);
    return () => window.clearTimeout(t);
  }, []);

  useEffect(() => {
    emit({ type: "nav", path: pathname });
  }, [pathname]);

  useEffect(() => {
    const onClick = (e: MouseEvent) => {
      const el = (e.target as HTMLElement | null)?.closest?.("button, a, [role='button'], [role='switch']");
      if (!el || (el as HTMLButtonElement).disabled) return;
      if (el.getAttribute("role") === "switch") emit({ type: "toggle", on: el.getAttribute("aria-checked") !== "true" });
      else emit({ type: "click" });
    };
    document.addEventListener("click", onClick, true);
    return () => document.removeEventListener("click", onClick, true);
  }, []);

  return (
    <>
      <BrandDefs />
      <WallpaperLayer />
      <EasterEggs />
      <SeasonalLayer />
    </>
  );
}
