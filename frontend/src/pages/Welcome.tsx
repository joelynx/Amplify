/**
 * Welcome screen: today's status and the main actions first (practise,
 * review, create a paper), then the optional study room, then 4 navlinks
 * (About / Theme / Subjects / Tutorial). Those four pages live here so the
 * top nav stays focused on the daily workflow (Generate / Browser / History /
 * Stats / Settings).
 */

import { Link } from "react-router-dom";
import {
  BookOpen,
  Info,
  Layers,
  Palette,
} from "lucide-react";

import { Logo } from "../appearance/brand/Logo";
import { StudyRoom } from "../appearance/room/StudyRoom";
import { useAppearance } from "../appearance/store";
import { TodayCard } from "../components/quiz/TodayCard";
import { cn } from "../lib/cn";

interface NavCard {
  to: string;
  title: string;
  blurb: string;
  Icon: typeof BookOpen;
}

const CARDS: readonly NavCard[] = [
  {
    to: "/subjects",
    title: "Subjects",
    blurb: "Define curricular bundles (topics + exclusions). Activate one to scope every other page.",
    Icon: Layers,
  },
  {
    to: "/themes",
    title: "Themes",
    blurb: "Presets, a wardrobe of swappable parts, sounds, a study room. Three presets are earned by practising.",
    Icon: Palette,
  },
  {
    to: "/tutorial",
    title: "Tutorial",
    blurb: "Five-minute orientation: what each page does and how the pieces fit together.",
    Icon: BookOpen,
  },
  {
    to: "/about",
    title: "About",
    blurb: "Version, question sources, and stack credits.",
    Icon: Info,
  },
];

export default function WelcomePage() {
  const room = useAppearance((s) => s.settings.room);
  return (
    <main className="h-full overflow-y-auto">
      {room ? (
        <div className="mx-auto flex max-w-5xl flex-col items-center gap-6 px-6 py-6">
          <TodayCard />
          {/* Kept below the actions and narrower, so they stay in view with it. */}
          <div className="w-full max-w-[760px]">
            <StudyRoom />
          </div>
          <ClubCredit />
          <NavCards />
        </div>
      ) : (
      <div className="mx-auto flex max-w-3xl flex-col items-center gap-10 px-6 py-12">
        <header className="flex flex-col items-center gap-3 text-center">
          <h1 className="sr-only">Amplify</h1>
          <Logo name="matrix" style={{ width: 220 }} />
          <ClubCredit />
          <p className="text-sm text-muted">
            Practice problem sets, generated from a curated bank.
          </p>
        </header>

        <TodayCard />

        <NavCards />
      </div>
      )}
    </main>
  );
}

/** Subjects, Themes, Tutorial and About: the room has no object for most of them. */
function NavCards() {
  return (
    <nav className="grid w-full gap-3 sm:grid-cols-2">
      {CARDS.map(({ to, title, blurb, Icon }) => (
        <Link
          key={to}
          to={to}
          className={cn(
            "flex flex-col gap-2 rounded-lg border border-border bg-surface p-4 text-left transition",
            "hover:border-primary hover:shadow-md",
          )}
        >
          <span className="flex items-center gap-2 font-semibold">
            <Icon className="h-4 w-4 text-primary" />
            {title}
          </span>
          <span className="text-sm text-muted">{blurb}</span>
        </Link>
      ))}
    </nav>
  );
}

/** Both club marks side by side; links to About. */
function ClubCredit() {
  return (
    <Link to="/about" className="flex items-center gap-2 text-xs text-muted hover:text-text" aria-label="ampliφ × Coding Club: about">
      <Logo name="inline" style={{ width: 64 }} />
      <span aria-hidden="true">×</span>
      <Logo name="coding" style={{ width: 70 }} />
    </Link>
  );
}
