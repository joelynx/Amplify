/**
 * Wallpaper behind the app (Makeover.md §5.4): a fixed layer under all page
 * content that never takes pointer events. Procedural scenes paint one still
 * frame (motion in the periphery pulls attention from the work, so they never
 * animate); pack items show their own day/night image. Kept faint (0.45
 * subtle, 0.75 full) so text stays readable, and hidden in focus mode.
 */

import { useEffect, useReducer, useRef, useState, type CSSProperties } from "react";

import { getItem, resolve } from "../registry";
import { effectsLevel, focusActive, useAppearance } from "../store";
import type { Item } from "../types";
import { runScene } from "./runner";
import { SCENES, sceneKeyFor } from "./scenes";
import { imageFor } from "./time";

const FILL: CSSProperties = { position: "absolute", inset: 0 };

function useEffectsLevel(): 0 | 1 | 2 {
  const [, bump] = useReducer((n: number) => n + 1, 0);
  useEffect(() => {
    const mq = window.matchMedia?.("(prefers-reduced-motion: reduce)");
    mq?.addEventListener?.("change", bump);
    return () => mq?.removeEventListener?.("change", bump);
  }, []);
  return useAppearance(() => effectsLevel());
}

/** The current time, refreshed every minute while `active`. */
function useNow(active: boolean): Date {
  const [now, setNow] = useState(() => new Date());
  useEffect(() => {
    if (!active) return;
    setNow(new Date());
    const id = setInterval(() => setNow(new Date()), 60_000);
    return () => clearInterval(id);
  }, [active]);
  return now;
}

interface CanvasProps {
  sceneKey: string;
  animate: boolean;
  density: 1 | 2;
  data?: Record<string, unknown>;
  preview?: boolean;
}

function SceneCanvas({ sceneKey, animate, density, data, preview = false }: CanvasProps) {
  const ref = useRef<HTMLCanvasElement>(null);
  const backRef = useRef<HTMLCanvasElement>(null);
  const scene = SCENES[sceneKey];
  useEffect(() => {
    const c = ref.current;
    if (!c || !scene) return;
    return runScene(c, {
      scene,
      animate,
      density,
      data,
      back: backRef.current,
      maxFps: preview ? 15 : undefined,
      pauseOffscreen: preview,
    });
  }, [scene, animate, density, data, preview]);
  const style: CSSProperties = {
    ...FILL,
    width: "100%",
    height: "100%",
    display: "block",
    imageRendering: scene?.pixelated ? "pixelated" : "auto",
  };
  return (
    <>
      {scene?.back && <canvas ref={backRef} style={style} />}
      <canvas ref={ref} style={style} />
    </>
  );
}

function Backdrop({ item, animate, density, preview }: { item: Item | undefined; animate: boolean; density: 1 | 2; preview?: boolean }) {
  const key = sceneKeyFor(item);
  const now = useNow(key === "image" && typeof item?.data?.night === "string");
  if (key === "none") return null;
  if (key === "image") {
    const src = (imageFor(item, now) ?? "").replace(/"/g, "%22");
    return <div style={{ ...FILL, backgroundImage: `url("${src}")`, backgroundSize: "cover", backgroundPosition: "center" }} />;
  }
  return <SceneCanvas key={key} sceneKey={key} animate={animate} density={density} data={item?.data} preview={preview} />;
}

function WallpaperFrame({ item, level }: { item: Item | undefined; level: 0 | 1 | 2 }) {
  const [shown, setShown] = useState(false);
  useEffect(() => {
    const r = requestAnimationFrame(() => setShown(true));
    return () => cancelAnimationFrame(r);
  }, []);
  const opacity = level === 2 ? 0.75 : 0.45;
  return (
    <div
      aria-hidden="true"
      data-layer="wallpaper"
      style={{
        position: "fixed",
        inset: 0,
        zIndex: -1,
        pointerEvents: "none",
        overflow: "hidden",
        opacity: shown ? opacity : 0,
        transition: level === 0 ? "none" : "opacity 500ms ease",
      }}
    >
      <Backdrop item={item} animate={false} density={level === 2 ? 2 : 1} />
    </div>
  );
}

export function WallpaperLayer() {
  const id = useAppearance((s) => s.loadout.wallpaper);
  const level = useEffectsLevel();
  // Focus mode clears everything behind the work.
  const focus = useAppearance(() => focusActive());
  const item = resolve({ wallpaper: id }, "wallpaper");
  if (focus || sceneKeyFor(item) === "none") return null;
  return <WallpaperFrame key={item?.id} item={item} level={level} />;
}

/**
 * A small still preview of any wallpaper for the Wardrobe, independent of
 * the active one.
 */
export function WallpaperPreview({ itemId, className }: { itemId: string; className?: string }) {
  const found = getItem(itemId);
  const item = found?.slot === "wallpaper" ? found : undefined;
  const positioned = /(^|\s)(absolute|fixed|sticky)(\s|$)/.test(className ?? "");
  const style: CSSProperties = {
    overflow: "hidden",
    background: "var(--background)",
    ...(positioned ? {} : { position: "relative" }),
    ...(className ? {} : { width: 160, height: 100 }),
  };
  return (
    <div className={className} style={style} aria-hidden="true" data-wallpaper-preview={itemId}>
      <div style={{ ...FILL, opacity: 0.75 }}>
        <Backdrop item={item} animate={false} density={2} preview />
      </div>
    </div>
  );
}
