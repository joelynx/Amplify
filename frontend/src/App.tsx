import { useEffect, useState } from "react";
import { HashRouter, Link, Route, Routes, useLocation } from "react-router-dom";

import { BridgeUnavailableError, ipc } from "./lib/ipc";
import { applyTheme, setAccessibilityMode, type ThemeId } from "./lib/theme";
import AboutPage from "./pages/About";
import BrowserPage from "./pages/Browser";
import GeneratePage from "./pages/Generate";
import HistoryPage from "./pages/History";
import SettingsPage from "./pages/Settings";
import StatsPage from "./pages/Stats";
import SubjectsPage from "./pages/Subjects";
import ThemesPage from "./pages/Themes";
import TutorialPage from "./pages/Tutorial";
import WelcomePage from "./pages/Welcome";

/**
 * Top-level shell. Probes the PyWebView bridge on mount so that — if the user
 * opens `localhost:5173` in a regular browser — every page degrades to the
 * "browser preview" state instead of dying with a 1.5s timeout.
 */

export default function App() {
  const [bridgeState, setBridgeState] = useState<"connecting" | "ready" | "standalone">("connecting");

  useEffect(() => {
    ipc
      .ping()
      .then(async () => {
        // Apply the persisted theme before the first paint of any page —
        // CSS vars are already loaded by the bundle; this just flips the
        // active selector.
        try {
          const [saved, savedA11y] = await Promise.all([
            ipc.get_config("THEME_SELECTED") as Promise<string | null>,
            ipc.get_config("THEME_A11Y_MODE") as Promise<boolean | null>,
          ]);
          if (saved) {
            await applyTheme(saved as ThemeId, { persist: false });
          }
          if (savedA11y) {
            await setAccessibilityMode(true, { persist: false });
          }
        } catch {
          /* fall back to the :root defaults */
        }
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

  if (bridgeState === "connecting") {
    return (
      <main className="flex h-full items-center justify-center">
        <p className="text-muted">Connecting to Python…</p>
      </main>
    );
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
      <div className="flex h-full flex-col">
        <NavBar />
        <div className="flex-1 overflow-hidden">
          <Routes>
            <Route path="/" element={<WelcomePage />} />
            <Route path="/generate" element={<GeneratePage />} />
            <Route path="/subjects" element={<SubjectsPage />} />
            <Route path="/browser" element={<BrowserPage />} />
            <Route path="/themes" element={<ThemesPage />} />
            <Route path="/history" element={<HistoryPage />} />
            <Route path="/stats" element={<StatsPage />} />
            <Route path="/settings" element={<SettingsPage />} />
            <Route path="/tutorial" element={<TutorialPage />} />
            <Route path="/about" element={<AboutPage />} />
          </Routes>
        </div>
      </div>
    </HashRouter>
  );
}

const NAV: Array<{ to: string; label: string }> = [
  { to: "/", label: "Home" },
  { to: "/generate", label: "Generate" },
  { to: "/browser", label: "Browser" },
  { to: "/subjects", label: "Subjects" },
  { to: "/history", label: "History" },
  { to: "/stats", label: "Stats" },
  { to: "/themes", label: "Themes" },
  { to: "/settings", label: "Settings" },
  { to: "/tutorial", label: "Tutorial" },
  { to: "/about", label: "About" },
];

function NavBar() {
  const { pathname } = useLocation();
  return (
    <nav className="flex h-12 items-center gap-1 border-b border-border bg-surface px-4 text-sm">
      <span className="mr-3 font-semibold tracking-tight">Amplify</span>
      {NAV.map((item) => {
        const active = pathname === item.to;
        return (
          <Link
            key={item.to}
            to={item.to}
            className={
              "rounded-md px-3 py-1.5 text-text/80 hover:bg-background hover:text-text " +
              (active ? "bg-background text-text font-medium" : "")
            }
          >
            {item.label}
          </Link>
        );
      })}
    </nav>
  );
}
