/**
 * Welcome screen — spec §8: Enter button + 4 navlinks (About / Theme /
 * Subjects / Tutorial). Those four pages live here so the top nav stays
 * focused on the daily workflow (Generate / Browser / History / Stats /
 * Settings).
 */

import { Link } from "react-router-dom";
import {
  BookOpen,
  Info,
  Layers,
  Palette,
} from "lucide-react";

import { Button } from "../components/ui/Button";
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
    blurb: "Pick a look — two defaults plus seven flavor themes. Switching applies live.",
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
  return (
    <main className="h-full overflow-y-auto">
      <div className="mx-auto flex max-w-3xl flex-col items-center gap-10 px-6 py-12">
        <header className="space-y-2 text-center">
          <h1 className="text-5xl font-semibold tracking-tight">Amplify</h1>
          <p className="text-sm text-muted">
            Practice problem sets, generated from a curated bank.
          </p>
        </header>

        <Link to="/generate">
          <Button variant="primary" size="md">
            Enter
          </Button>
        </Link>

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
      </div>
    </main>
  );
}
