"use client";

import { useEffect, useState } from "react";

type Theme =
  | "default-light"
  | "default-dark"
  | "pastel"
  | "frutiger-aero"
  | "pixel-art"
  | "windows-xp"
  | "comic"
  | "ascii"
  | "android-kitkat";

const THEMES: { id: Theme; label: string; glyph: string }[] = [
  { id: "default-light", label: "Default Light", glyph: "◐" },
  { id: "default-dark", label: "Default Dark", glyph: "◑" },
  { id: "pastel", label: "Pastel", glyph: "❀" },
  { id: "frutiger-aero", label: "Frutiger Aero", glyph: "✦" },
  { id: "pixel-art", label: "Pixel Art", glyph: "■" },
  { id: "windows-xp", label: "Windows XP", glyph: "▣" },
  { id: "comic", label: "Comic", glyph: "★" },
  { id: "ascii", label: "ASCII", glyph: ">" },
  { id: "android-kitkat", label: "Android KitKat", glyph: "◆" },
];

export function ThemeToggle() {
  const [theme, setTheme] = useState<Theme>("default-light");
  const [open, setOpen] = useState(false);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    const saved = localStorage.getItem("amplify-theme") as Theme | null;
    const initial: Theme =
      saved && THEMES.some((t) => t.id === saved) ? saved : "default-light";
    setTheme(initial);
    document.documentElement.setAttribute("data-theme", initial);
  }, []);

  function pick(id: Theme) {
    setTheme(id);
    document.documentElement.setAttribute("data-theme", id);
    localStorage.setItem("amplify-theme", id);
    setOpen(false);
  }

  const current = THEMES.find((t) => t.id === theme) ?? THEMES[0];

  if (!mounted) {
    return (
      <button
        type="button"
        className="ml-1 rounded-md border border-ink-200 px-2 py-1.5 text-xs text-ink-500"
        aria-label="Theme"
      >
        ◐
      </button>
    );
  }

  return (
    <div className="relative ml-1">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="rounded-md border border-ink-200 px-2 py-1.5 text-xs text-ink-700 hover:bg-ink-50"
        aria-label="Choose theme"
        title={current.label}
      >
        {current.glyph}
      </button>
      {open && (
        <div className="absolute right-0 z-30 mt-1 min-w-44 rounded-md border border-ink-200 bg-white p-1 shadow-lg">
          {THEMES.map((t) => (
            <button
              key={t.id}
              type="button"
              onClick={() => pick(t.id)}
              className={`flex w-full items-center gap-2 rounded px-2 py-1.5 text-left text-xs ${
                t.id === theme
                  ? "bg-ink-100 font-medium text-ink-900"
                  : "text-ink-700 hover:bg-ink-50"
              }`}
            >
              <span className="w-4 text-center">{t.glyph}</span>
              <span>{t.label}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
