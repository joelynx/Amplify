import { test } from "@playwright/test";

const THEMES = [
  "default-light",
  "default-dark",
  "pastel",
  "frutiger-aero",
  "pixel-art",
  "windows-xp",
  "comic",
  "ascii",
  "android-kitkat",
];

for (const theme of THEMES) {
  test(`screenshot every page in ${theme}`, async ({ page }) => {
    await page.addInitScript((t: string) => {
      localStorage.setItem("amplify-theme", t);
    }, theme);

    for (const route of ["/", "/practice", "/stats", "/q/1", "/pbs", "/about"]) {
      await page.goto(route);
      await page.waitForLoadState("networkidle");
      // Wait a tick for theme client effect to apply data-theme.
      await page.waitForTimeout(200);
      const slug = route.replace(/\W+/g, "_") || "root";
      await page.screenshot({
        path: `tests/e2e/theme-shots/${theme}${slug}.png`,
        fullPage: true,
      });
    }
  });
}
