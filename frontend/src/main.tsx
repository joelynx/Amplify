import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import App from "./App";
import { installConsoleForwarder } from "./lib/console-forward";
import "../styles/base.css";

installConsoleForwarder();

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
