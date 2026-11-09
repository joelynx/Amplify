import { act, createElement } from "react";
import { createRoot } from "react-dom/client";
import { describe, expect, it } from "vitest";

import { DEFAULT_SETTINGS, useAppearance } from "../../store";
import { WallpaperLayer } from "../WallpaperLayer";

(globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

describe("wallpaper and focus mode", () => {
  it("shows the wallpaper normally and hides it in focus mode", () => {
    const host = document.createElement("div");
    document.body.appendChild(host);
    const root = createRoot(host);
    act(() => {
      useAppearance.setState({
        loadout: { ...useAppearance.getState().loadout, wallpaper: "wallpaper.hills" },
        settings: { ...DEFAULT_SETTINGS },
      });
      root.render(createElement(WallpaperLayer));
    });
    expect(host.querySelector("[data-layer=wallpaper]")).not.toBeNull();
    act(() => useAppearance.setState({ settings: { ...DEFAULT_SETTINGS, focus: true } }));
    expect(host.querySelector("[data-layer=wallpaper]")).toBeNull();
    act(() => root.unmount());
    host.remove();
  });
});
