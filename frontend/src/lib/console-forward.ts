/**
 * Mirror `console.{log,info,warn,error,debug}` into the Python rotating logger
 * via the IPC bridge. Original console methods still run so devtools stay useful.
 *
 * Spec §1 / Step 1 of the dev cycle: "JS-side console.log forwarder via an IPC
 * `log(level, message)` call".
 */

import { BridgeUnavailableError, ipc, type LogLevel } from "./ipc";

type ConsoleMethod = "log" | "info" | "warn" | "error" | "debug";

const METHOD_LEVELS: Record<ConsoleMethod, LogLevel> = {
  log: "info",
  info: "info",
  warn: "warning",
  error: "error",
  debug: "debug",
};

function format(args: unknown[]): string {
  return args
    .map((a) => {
      if (typeof a === "string") return a;
      if (a instanceof Error) return `${a.name}: ${a.message}\n${a.stack ?? ""}`;
      try {
        return JSON.stringify(a);
      } catch {
        return String(a);
      }
    })
    .join(" ");
}

let installed = false;
let bridgeGone = false;

export function installConsoleForwarder(): void {
  if (installed) return;
  installed = true;

  (Object.keys(METHOD_LEVELS) as ConsoleMethod[]).forEach((name) => {
    const original = console[name].bind(console);
    console[name] = (...args: unknown[]) => {
      original(...args);
      if (bridgeGone) return;
      // fire-and-forget; if the bridge isn't there, latch and stop forwarding
      ipc.log(METHOD_LEVELS[name], format(args)).catch((e: unknown) => {
        if (e instanceof BridgeUnavailableError) bridgeGone = true;
      });
    };
  });
}
