/**
 * The Wardrobe: every slot with the items that fill it. Clicking an item
 * equips it at once (the app itself is the preview); slots that can be shown
 * in isolation also get a thumbnail or a play button.
 */

import { useState } from "react";
import { Check, Lock, Play } from "lucide-react";

import { Logo, type LogoVariant } from "../../appearance/brand/Logo";
import { MatrixLoader, Spinner, type LoopKind } from "../../appearance/brand/Loader";
import { itemsFor } from "../../appearance/registry";
import { ResultsPreview } from "../../appearance/results/ResultsScreen";
import { RoomPreview } from "../../appearance/room/StudyRoom";
import { previewSfx } from "../../appearance/sound/engine";
import { useAppearance } from "../../appearance/store";
import type { Item, SlotId } from "../../appearance/types";
import { WallpaperPreview } from "../../appearance/wallpaper/WallpaperLayer";
import { cn } from "../../lib/cn";

const GROUPS: { title: string; slots: { slot: SlotId; label: string; hint: string }[] }[] = [
  {
    title: "Look",
    slots: [
      { slot: "palette", label: "Palette", hint: "The colours." },
      { slot: "typography", label: "Fonts", hint: "UI, heading and mono fonts. Missing fonts fall back to system ones." },
      { slot: "chrome", label: "Chrome", hint: "How cards, buttons, dialogs and the nav are drawn." },
      { slot: "motion", label: "Motion", hint: "Page transitions and animation personality." },
      { slot: "surface", label: "Surface", hint: "A pattern behind the app." },
      { slot: "wallpaper", label: "Wallpaper", hint: "A still scene behind the app." },
      { slot: "paper", label: "Question paper", hint: "The paper questions are printed on, and the maths ink." },
      { slot: "icons", label: "Icons", hint: "Icon style." },
      { slot: "cursor", label: "Cursor", hint: "The mouse pointer." },
      { slot: "logo", label: "Logo", hint: "How the ampliφ and Coding Club logos are drawn." },
      { slot: "loader", label: "Loader", hint: "The loading animations." },
      { slot: "charts", label: "Charts", hint: "How Stats charts are drawn." },
    ],
  },
  {
    title: "Sound",
    slots: [
      { slot: "sfx", label: "Sound effects", hint: "Clicks, answers, session ends. Volumes are under Settings." },
    ],
  },
  {
    title: "Places",
    slots: [
      { slot: "results", label: "Results screen", hint: "The end-of-session card." },
      { slot: "room", label: "Study room", hint: "The Home page room." },
      { slot: "arena", label: "Quiz arena", hint: "The quiz board and answer box style." },
    ],
  },
];

function Preview({ item }: { item: Item }) {
  const d = item.data ?? {};
  switch (item.slot) {
    case "palette":
      return (
        <div data-theme={String(d.theme)} className="flex h-10 overflow-hidden rounded border" style={{ borderColor: "var(--border)" }}>
          {["--background", "--surface", "--primary", "--secondary", "--accent"].map((v) => (
            <span key={v} className="flex-1" style={{ background: `var(${v})` }} />
          ))}
          <span className="flex items-center px-2 text-sm font-semibold" style={{ background: "var(--background)", color: "var(--text)" }}>
            Aa
          </span>
        </div>
      );
    case "typography":
      return (
        <div className="space-y-0.5">
          <div className="truncate text-base" style={{ fontFamily: String(d.heading ?? d.body) }}>Eigenvalues</div>
          <div className="truncate text-xs" style={{ fontFamily: String(d.body) }}>The quick brown fox · 0123</div>
          <div className="truncate text-xs" style={{ fontFamily: String(d.mono) }}>x = 3.14159</div>
        </div>
      );
    case "logo":
      return item.id === "logo.auto" ? (
        <Logo name="inline" style={{ width: 110 }} />
      ) : (
        <Logo name="inline" variant={item.id.slice(5) as LogoVariant} style={{ width: 110 }} />
      );
    case "loader":
      return (
        <div className="flex items-center gap-3">
          <MatrixLoader kind={d.big as LoopKind} className="w-20" />
          <Spinner className="h-5 w-5" />
        </div>
      );
    case "wallpaper":
      return <WallpaperPreview itemId={item.id} className="h-16 w-full overflow-hidden rounded" />;
    case "room":
      return <RoomPreview itemId={item.id} className="h-20 w-full" />;
    case "results":
      return (
        <div className="relative h-24 overflow-hidden rounded">
          <div className="pointer-events-none absolute left-0 top-0 w-[200%] origin-top-left scale-50">
            <ResultsPreview itemId={item.id} />
          </div>
        </div>
      );
    case "sfx":
      return (
        <button type="button" className="inline-flex items-center gap-1 text-xs text-primary hover:underline" onClick={(e) => { e.stopPropagation(); previewSfx(item.id); }}>
          <Play className="h-3.5 w-3.5" /> Preview
        </button>
      );
    default:
      return null;
  }
}

function isLocked(item: Item, locked: Set<string>, secrets: Set<string>): boolean {
  if (!item.unlock || item.unlock === "starter") return false;
  if (item.unlock.startsWith("secret:")) return !secrets.has(item.unlock.slice(7));
  if (item.slot === "palette") return locked.has(String(item.data?.theme));
  return false;
}

export function SlotBrowser() {
  const st = useAppearance();
  const [slot, setSlot] = useState<SlotId>("palette");
  const info = GROUPS.flatMap((g) => g.slots).find((s) => s.slot === slot)!;
  const items = itemsFor(slot).filter((it) => !(it.unlock?.startsWith("secret:") && !st.secrets.has(it.unlock.slice(7))));

  return (
    <div className="grid gap-4 md:grid-cols-[13rem_1fr]">
      <nav className="space-y-4" aria-label="Slots">
        {GROUPS.map((g) => (
          <div key={g.title}>
            <div className="mb-1 text-xs font-semibold uppercase tracking-wide text-muted">{g.title}</div>
            <ul className="space-y-0.5">
              {g.slots.map((s) => (
                <li key={s.slot}>
                  <button
                    type="button"
                    onClick={() => setSlot(s.slot)}
                    className={cn(
                      "w-full rounded-md px-2 py-1 text-left text-sm hover:bg-surface",
                      slot === s.slot && "bg-surface font-medium text-primary",
                    )}
                  >
                    {s.label}
                  </button>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </nav>

      <section>
        <p className="mb-3 text-sm text-muted">{info.hint}</p>
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
          {items.map((it) => {
            const equipped = st.loadout[slot] === it.id;
            const lockedNow = isLocked(it, st.locked, st.secrets);
            return (
              <div
                key={it.id}
                role="button"
                tabIndex={0}
                aria-pressed={equipped}
                aria-disabled={lockedNow}
                onClick={() => !lockedNow && st.setSlot(slot, it.id)}
                onKeyDown={(e) => {
                  if ((e.key === "Enter" || e.key === " ") && !lockedNow) {
                    e.preventDefault();
                    st.setSlot(slot, it.id);
                  }
                }}
                className={cn(
                  "flex cursor-pointer flex-col gap-2 rounded-lg border bg-surface p-3 text-sm transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-primary",
                  equipped ? "border-primary ring-1 ring-primary/40" : "border-border hover:border-primary/50",
                  lockedNow && "cursor-not-allowed opacity-60",
                )}
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="min-w-0">
                    <div className="flex items-center gap-1.5 font-medium">
                      {it.name}
                      {it.tags?.includes("pack") && <span className="rounded bg-primary/10 px-1 text-[10px] text-primary">pack</span>}
                    </div>
                    <div className="text-xs text-muted">{it.description}</div>
                  </div>
                  {equipped ? (
                    <Check className="h-4 w-4 shrink-0 text-primary" />
                  ) : lockedNow ? (
                    <Lock className="h-4 w-4 shrink-0 text-muted" />
                  ) : null}
                </div>
                <Preview item={it} />
              </div>
            );
          })}
        </div>
      </section>
    </div>
  );
}
