import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import App from "./App";
import { applyBootTheme } from "./appearance/apply";
import { installConsoleForwarder } from "./lib/console-forward";
import "../styles/base.css";

installConsoleForwarder();
if (applyBootTheme(window.location.hash)) {
  // Clear it so the hash router starts at Home.
  history.replaceState(null, "", window.location.pathname + window.location.search);
}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
