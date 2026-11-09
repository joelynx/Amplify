/**
 * Visual pieces of the easter eggs: the toast stack, the CRT scanline
 * overlay (Konami), the Q.E.D. tombstone stamp and the rubber duck icon.
 * Everything is themed with the palette variables and ignores the pointer.
 */

import { useEffect } from "react";

import { dismissToast, useEggToasts, type EggToast } from "./toast";

const TOAST_MS = 4000;
const STAMP_MS = 1500;

export const EGG_CSS = `
.amp-egg-toasts { position: fixed; left: 50%; bottom: 20px; transform: translateX(-50%); z-index: 9999;
  display: flex; flex-direction: column; align-items: center; gap: 8px; pointer-events: none;
  width: max-content; max-width: min(92vw, 480px); }
.amp-egg-toast { display: flex; align-items: center; gap: 10px; padding: 8px 14px; border-radius: 10px;
  background: var(--surface); color: var(--text); border: 1px solid var(--border);
  box-shadow: 0 6px 24px rgba(0, 0, 0, 0.18); font-family: var(--font-family); font-size: 14px; line-height: 1.35;
  animation: amp-egg-toast-in 0.22s ease-out; }
.amp-egg-toast .glyph { flex: none; min-width: 1.4em; text-align: center; color: var(--primary); font-weight: 700;
  font-family: var(--font-heading, var(--font-family)); }
.amp-egg-toast svg { flex: none; width: 26px; height: 26px; }
@keyframes amp-egg-toast-in { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: none; } }

.amp-egg-crt { position: fixed; inset: 0; z-index: 9990; pointer-events: none;
  background:
    repeating-linear-gradient(to bottom, transparent 0, transparent 2px, rgba(0, 0, 0, 0.13) 2px, rgba(0, 0, 0, 0.13) 3px),
    radial-gradient(ellipse at center, transparent 58%, rgba(0, 0, 0, 0.32) 100%); }

.amp-egg-qed { position: fixed; inset: 0; z-index: 9996; display: grid; place-items: center; pointer-events: none; }
.amp-egg-qed span { font-size: min(34vmin, 220px); line-height: 1; color: var(--primary);
  font-family: var(--font-heading, var(--font-family)); filter: drop-shadow(0 6px 14px rgba(0, 0, 0, 0.25));
  animation: amp-egg-stamp ${STAMP_MS}ms cubic-bezier(0.2, 0.9, 0.3, 1) forwards; }
@keyframes amp-egg-stamp {
  0% { opacity: 0; transform: scale(2.6) rotate(-10deg); }
  16% { opacity: 0.92; transform: scale(1) rotate(-4deg); }
  22% { transform: scale(1.05) rotate(-4deg); }
  28% { transform: scale(1) rotate(-4deg); }
  70% { opacity: 0.92; }
  100% { opacity: 0; transform: scale(1) rotate(-4deg); }
}

.amp-egg-saver { position: fixed; inset: 0; z-index: 9995; pointer-events: none; background: rgba(0, 0, 0, 0.72);
  animation: amp-egg-fade 1.5s ease-out; }
.amp-egg-saver .bouncer { position: absolute; left: 0; top: 0; width: 220px; will-change: transform; }
@keyframes amp-egg-fade { from { opacity: 0; } to { opacity: 1; } }

:root[data-reduced-motion="on"] .amp-egg-toast,
:root[data-reduced-motion="on"] .amp-egg-saver { animation: none; }
:root[data-reduced-motion="on"] .amp-egg-qed span { animation-name: amp-egg-fade-out; }
@keyframes amp-egg-fade-out { 0%, 70% { opacity: 0.92; } 100% { opacity: 0; } }
`;

/** A small original rubber duck. */
export function DuckIcon() {
  return (
    <svg viewBox="0 0 32 32" aria-hidden="true">
      <ellipse cx="15" cy="21" rx="11" ry="7" fill="#ffd23f" stroke="#c99a00" strokeWidth="1" />
      <circle cx="20" cy="11" r="6" fill="#ffd23f" stroke="#c99a00" strokeWidth="1" />
      <path d="M25 11.5 L30.5 12.5 L25.5 14.5 Z" fill="#ff8c1a" />
      <circle cx="21.5" cy="9.5" r="1.1" fill="#1a1a1a" />
      <path d="M9 19 q4 4 10 1" fill="none" stroke="#c99a00" strokeWidth="1.2" strokeLinecap="round" />
    </svg>
  );
}

function ToastItem({ t }: { t: EggToast }) {
  useEffect(() => {
    const id = setTimeout(() => dismissToast(t.id), TOAST_MS);
    return () => clearTimeout(id);
  }, [t.id]);
  return (
    <div className="amp-egg-toast">
      {t.icon === "duck" ? <DuckIcon /> : t.icon ? <span className="glyph" aria-hidden="true">{t.icon}</span> : null}
      <span>{t.text}</span>
    </div>
  );
}

/** Up to three toasts at a time; the rest wait. Hidden (queued) while `paused`. */
export function ToastStack({ paused }: { paused: boolean }) {
  const items = useEggToasts((s) => s.items);
  return (
    <div className="amp-egg-toasts" role="status" aria-live="polite">
      {!paused && items.slice(0, 3).map((t) => <ToastItem key={t.id} t={t} />)}
    </div>
  );
}

export function CrtOverlay() {
  return <div className="amp-egg-crt" aria-hidden="true" />;
}

export function QedStamp({ onDone }: { onDone: () => void }) {
  useEffect(() => {
    const id = setTimeout(onDone, STAMP_MS + 50);
    return () => clearTimeout(id);
  }, [onDone]);
  return (
    <div className="amp-egg-qed" aria-hidden="true">
      <span>∎</span>
    </div>
  );
}
