import { type ReactNode, useEffect, useState } from "react";
import { HashRouter, Link, Route, Routes, useLocation, useNavigate } from "react-router-dom";

import { AppearanceRoot } from "./appearance/AppearanceRoot";
import { Logo } from "./appearance/brand/Logo";
import { BootScreen } from "./appearance/brand/Loader";
import { ThemedIcon } from "./appearance/icons/ThemedIcon";
import { emit } from "./appearance/events";
import { loadPrefs } from "./appearance/prefs";
import { useAppearance } from "./appearance/store";
import { BridgeUnavailableError, ipc } from "./lib/ipc";
import { cn } from "./lib/cn";
import AboutPage from "./pages/About";
import BrowserPage from "./pages/Browser";
import GeneratePage from "./pages/Generate";
import HistoryPage from "./pages/History";
import QuizPage from "./pages/Quiz";
import QuizReviewPage from "./pages/QuizReview";
import SettingsPage from "./pages/Settings";
import StatsPage from "./pages/Stats";
import SubjectsPage from "./pages/Subjects";
import ThemesPage from "./pages/Themes";
import ThemeLabPage from "./pages/ThemeLab";
import TutorialPage from "./pages/Tutorial";
import WelcomePage from "./pages/Welcome";
import { useSubjectStore } from "./state/subject";

/**
 * Top-level shell. Probes the PyWebView bridge on mount so that — if the user
 * opens `localhost:5173` in a regular browser — every page degrades to the
 * "browser preview" state instead of dying with a 1.5s timeout.
 */

export default function App() {
  const [bridgeState, setBridgeState] = useState<"connecting" | "ready" | "standalone">("connecting");
  // The boot animation plays once to the end (or until a click / key press).
  const [bootDone, setBootDone] = useState(false);

  useEffect(() => {
    ipc
      .ping()
      .then(async () => {
        // Load the appearance loadout, UI prefs and the active subject before
        // the first page paints; AppearanceRoot applies the loadout to <html> on mount.
        await Promise.all([
          useAppearance.getState().load().catch(() => {
            /* fall back to the :root defaults */
          }),
          loadPrefs(),
          ipc
            .get_active_subject()
            .then((name) => useSubjectStore.getState().setActive(name))
            .catch(() => {}),
        ]);
        setBridgeState("ready");
      })
      .catch((e: unknown) => {
        if (e instanceof BridgeUnavailableError) {
          setBridgeState("standalone");
        } else {
          setBridgeState("standalone");
        }
      });
  }, []);

  if (bridgeState === "connecting" || (bridgeState === "ready" && !bootDone)) {
    return <BootScreen message="Connecting…" onDone={() => setBootDone(true)} />;
  }

  if (bridgeState === "standalone") {
    return (
      <main className="flex h-full items-center justify-center px-6">
        <div className="space-y-2 text-center">
          <h1 className="text-3xl font-semibold">Amplify</h1>
          <p className="text-muted">
            Browser preview — IPC unavailable. Launch via{" "}
            <code className="font-mono">uv run python -m app.main</code> for full integration.
          </p>
        </div>
      </main>
    );
  }

  return (
    <HashRouter>
      <AppearanceRoot />
      <div className="flex h-full flex-col">
        <NavBar />
        <Page>
          <Routes>
            <Route path="/" element={<WelcomePage />} />
            <Route path="/generate" element={<GeneratePage />} />
            <Route path="/subjects" element={<SubjectsPage />} />
            <Route path="/browser" element={<BrowserPage />} />
            <Route path="/quiz" element={<QuizPage />} />
            <Route path="/quiz/review/:attemptId" element={<QuizReviewPage />} />
            <Route path="/themes" element={<ThemesPage />} />
            <Route path="/history" element={<HistoryPage />} />
            <Route path="/stats" element={<StatsPage />} />
            <Route path="/settings" element={<SettingsPage />} />
            <Route path="/tutorial" element={<TutorialPage />} />
            <Route path="/about" element={<AboutPage />} />
            <Route path="/theme-lab" element={<ThemeLabPage />} />
          </Routes>
        </Page>
      </div>
    </HashRouter>
  );
}

// Daily-workflow only — Subjects/Themes/Tutorial/About live on the Welcome
// page as cards so the nav stays tight (spec §8).
const NAV: Array<{ to: string; label: string }> = [
  { to: "/", label: "Home" },
  { to: "/generate", label: "Generate" },
  { to: "/quiz", label: "Quiz" },
  { to: "/browser", label: "Browser" },
  { to: "/history", label: "History" },
  { to: "/stats", label: "Stats" },
  { to: "/settings", label: "Settings" },
];

/** Route container. Keyed by path so the motion slot's page transition replays. */
function Page({ children }: { children: ReactNode }) {
  const { pathname } = useLocation();
  return (
    <div key={pathname} data-ui="page" className="flex-1 overflow-hidden">
      {children}
    </div>
  );
}

function NavBar() {
  const { pathname } = useLocation();
  const navigate = useNavigate();
  const focus = useAppearance((s) => s.settings.focus);
  const setSettings = useAppearance((s) => s.setSettings);
  return (
    <nav data-ui="nav" className="flex h-12 items-center gap-1 border-b border-border bg-surface px-4 text-sm">
      <button
        type="button"
        onClick={() => {
          emit({ type: "logo_click" });
          navigate("/");
        }}
        className="mr-3 flex h-8 items-center rounded-md px-1 focus:outline-none focus-visible:ring-2 focus-visible:ring-primary"
        aria-label="Amplify home"
        title="ampliφ · Mathematics Club × Coding Club"
      >
        <Logo name="inline" className="nav-logo" style={{ width: 92 }} />
      </button>
      {NAV.map((item) => {
        const active = pathname === item.to;
        return (
          <Link
            key={item.to}
            to={item.to}
            data-ui="nav-link"
            aria-current={active ? "page" : undefined}
            className={
              "rounded-md px-3 py-1.5 text-text/80 hover:bg-background hover:text-text " +
              (active ? "bg-background text-text font-medium" : "")
            }
          >
            {item.label}
          </Link>
        );
      })}
      <div className="ml-auto flex items-center gap-1">
        <button
          type="button"
          onClick={() => setSettings({ focus: !focus })}
          aria-pressed={focus}
          title={focus ? "Focus mode is on: no wallpaper or decorative animation" : "Focus mode: hide the wallpaper and decorative animation"}
          className={cn(
            "flex h-8 w-8 items-center justify-center rounded-md text-text/70 hover:bg-background hover:text-text",
            focus && "bg-background text-primary",
          )}
        >
          <ThemedIcon name="focus" className="h-4 w-4" />
        </button>
        <Link
          to="/themes"
          data-ui="nav-link"
          aria-current={pathname === "/themes" ? "page" : undefined}
          title="Themes and Wardrobe"
          className="flex h-8 w-8 items-center justify-center rounded-md text-text/70 hover:bg-background hover:text-text"
        >
          <ThemedIcon name="themes" className="h-4 w-4" />
        </Link>
      </div>
    </nav>
  );
}
