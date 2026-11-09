/**
 * Thematic icons (spec §11.2 "sprite pack"). Semantic names map to the
 * active icon set: line icons (lucide), pixel (the same icons, square-capped
 * and crisp; styles/appearance/places.css), text glyphs for terminal themes,
 * or images from a drop-in pack (`data.icons: { name: url }`). Functional
 * icons (close, chevrons) stay plain lucide.
 */

import {
  BarChart3,
  Bookmark,
  BookmarkCheck,
  Brain,
  Clock,
  Eye,
  FileText,
  Focus,
  History,
  Home,
  Lightbulb,
  Palette,
  Search,
  Send,
  Settings,
  Sparkles,
  type LucideIcon,
} from "lucide-react";

import { cn } from "../../lib/cn";
import { resolve } from "../registry";
import { useAppearance } from "../store";

export type IconName =
  | "home" | "generate" | "quiz" | "browser" | "history" | "stats" | "settings" | "themes" | "focus"
  | "hint" | "reveal" | "bookmark" | "bookmarked" | "submit" | "timer" | "review";

const LUCIDE: Record<IconName, LucideIcon> = {
  home: Home, generate: FileText, quiz: Brain, browser: Search, history: History, stats: BarChart3,
  settings: Settings, themes: Palette, focus: Focus, hint: Lightbulb, reveal: Eye, bookmark: Bookmark,
  bookmarked: BookmarkCheck, submit: Send, timer: Clock, review: Sparkles,
};

const GLYPHS: Record<IconName, string> = {
  home: "~", generate: "[#]", quiz: "?_", browser: "/", history: "<<", stats: "|||", settings: "*",
  themes: "%", focus: "( )", hint: "!", reveal: "o_o", bookmark: "[ ]", bookmarked: "[x]", submit: ">>",
  timer: "@", review: "<>",
};

export function ThemedIcon({ name, className, title }: { name: IconName; className?: string; title?: string }) {
  const set = useAppearance((s) => resolve(s.loadout, "icons"));
  const urls = set?.data?.icons as Record<string, string> | undefined;
  if (urls?.[name]) {
    return <img src={urls[name]} alt={title ?? ""} className={cn("inline-block object-contain", className)} draggable={false} />;
  }
  if (set?.id === "icons.terminal") {
    return (
      <span aria-hidden={title ? undefined : true} title={title} className={cn("inline-flex items-center justify-center font-mono text-[0.8em] leading-none", className)}>
        {GLYPHS[name]}
      </span>
    );
  }
  const Icon = LUCIDE[name];
  return <Icon className={className} aria-hidden={title ? undefined : true} aria-label={title} />;
}
