import { test, expect } from "@playwright/test";

test.describe("Full app sweep", () => {
  test("landing renders + nav links present", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByRole("heading", { name: /problem-bank commons/i })).toBeVisible();
    for (const label of ["Practice", "PBS", "Browse", "Stats", "Tutorial", "About"]) {
      await expect(page.getByRole("link", { name: label, exact: true })).toBeVisible();
    }
  });

  test("theme switcher applies the picked theme to html[data-theme]", async ({ page }) => {
    await page.goto("/");
    await page.getByRole("button", { name: /choose theme/i }).click();
    // Theme buttons have a glyph + label, so use a substring match.
    await page.getByRole("button", { name: /Pastel/ }).click();
    await expect(page.locator("html")).toHaveAttribute("data-theme", "pastel");
    await page.getByRole("button", { name: /choose theme/i }).click();
    await page.getByRole("button", { name: /Frutiger Aero/ }).click();
    await expect(page.locator("html")).toHaveAttribute("data-theme", "frutiger-aero");
  });

  test("/practice has filter form, mode toggle, tag tray, tree", async ({ page }) => {
    await page.goto("/practice");
    await expect(page.getByRole("heading", { name: "Practice", exact: true })).toBeVisible();
    await expect(page.getByText("Generation mode", { exact: true })).toBeVisible();
    await expect(page.getByRole("button", { name: "Diverse", exact: true })).toBeVisible();
    await expect(page.getByRole("button", { name: "Random", exact: true })).toBeVisible();
    await expect(page.getByText("Topics", { exact: true })).toBeVisible();
    await expect(page.getByText("Tags", { exact: true })).toBeVisible();
    // CheckableTree: tri-state checkbox role present
    expect(await page.locator('[role="checkbox"]').count()).toBeGreaterThan(0);
  });

  test("/practice CheckableTree cascade works", async ({ page }) => {
    await page.goto("/practice");
    // Click the first checkbox (a topic-level one)
    const firstCheckbox = page.locator('[role="checkbox"]').first();
    await firstCheckbox.click();
    // Status bar should update (live counter)
    await expect(page.getByText(/questions match your filters|counting/i)).toBeVisible({ timeout: 5000 });
  });

  test("/practice — create a Diverse session and land on the runner", async ({ page }) => {
    await page.goto("/practice");
    // Pick the first TOPIC checkbox to cascade-select all subtopics under it.
    await page.locator('[role="checkbox"]').first().click();
    // Wait for live counter to confirm matches exist.
    await expect(page.getByText(/questions match your filters/i)).toBeVisible({ timeout: 5000 });
    // Submit
    await page.getByRole("button", { name: /^Start practice$/ }).click();
    await page.waitForURL(/\/practice\/[0-9a-f-]+$/, { timeout: 15000 });
    // Diversity badge should render (Diverse is default mode)
    await expect(page.getByText(/Diverse session/i)).toBeVisible({ timeout: 10000 });
  });

  test("/q list page renders question cards", async ({ page }) => {
    await page.goto("/q");
    // Some questions should be visible
    const links = page.locator('a[href^="/q/"]');
    expect(await links.count()).toBeGreaterThan(3);
  });

  test("/q/1 detail — Similar Questions section + Reveal solution toggle", async ({ page }) => {
    await page.goto("/q/1");
    await expect(page.getByText(/Similar questions/i)).toBeVisible();
    // % similar badges should appear
    const similarBadges = page.locator("text=/% similar/");
    expect(await similarBadges.count()).toBeGreaterThan(0);
    // Reveal solution
    const revealBtn = page.getByRole("button", { name: /reveal solution/i });
    if (await revealBtn.isVisible()) {
      await revealBtn.click();
      await expect(page.getByText(/^Solution$/)).toBeVisible({ timeout: 3000 });
    }
  });

  test("/q/1 — no leaking raw LaTeX commands", async ({ page }) => {
    await page.goto("/q/1");
    const body = await page.locator("body").innerText();
    expect(body).not.toContain("\\textbf");
    expect(body).not.toContain("\\textit");
    expect(body).not.toContain("\\begin{");
    expect(body).not.toContain("\\end{");
    expect(body).not.toContain("\\item");
    expect(body).not.toContain("\\hfill");
  });

  test("/me redirects to login when unauthenticated", async ({ page }) => {
    const resp = await page.goto("/me");
    // Redirect chain ends at /auth/login
    expect(page.url()).toMatch(/\/auth\/login/);
    expect(resp?.ok()).toBe(true);
  });

  test("/history redirects to login when unauthenticated", async ({ page }) => {
    await page.goto("/history");
    expect(page.url()).toMatch(/\/auth\/login/);
  });

  test("/stats renders all 4 D3 charts + 8 stat cards", async ({ page }) => {
    await page.goto("/stats");
    await expect(page.getByRole("heading", { name: "Stats", exact: true })).toBeVisible();
    // 8 StatsCards labels (from Joel's component)
    for (const label of [
      "PSets Generated",
      "Total Questions Seen",
      "Unique Questions Seen",
      "Fraction Seen",
      "Max in single PSet",
      "Max Multiplicity",
      "Avg Multiplicity",
      "Avg Difficulty",
    ]) {
      await expect(page.getByText(label, { exact: true })).toBeVisible();
    }
    // 4 chart card titles — use heading role to disambiguate from any
    // matching paragraph text in empty-state messages.
    await expect(page.getByRole("heading", { name: /bank composition by topic/i })).toBeVisible();
    await expect(page.getByRole("heading", { name: /question multiplicity/i })).toBeVisible();
    await expect(page.getByRole("heading", { name: /^Activity — last 30 days$/ })).toBeVisible();
    await expect(page.getByRole("heading", { name: /^Calendar — \d{4}$/ })).toBeVisible();
    // SVGs should render (D3 outputs SVG)
    expect(await page.locator("svg").count()).toBeGreaterThanOrEqual(3);
  });

  test("/pbs setup screen renders + Start button enabled", async ({ page }) => {
    await page.goto("/pbs");
    await expect(page.getByRole("heading", { name: /Parallel Burst/i })).toBeVisible();
    await expect(page.getByRole("button", { name: /^Start PBS$/ })).toBeVisible();
    await expect(page.getByRole("button", { name: /^Start PBS$/ })).toBeEnabled();
  });

  test("/pbs — start a run and verify 3 widgets + score + timer visible", async ({ page }) => {
    await page.goto("/pbs");
    await page.getByRole("button", { name: /^Start PBS$/ }).click();
    // Timer mm:ss format
    await expect(page.getByText(/^\d:\d{2}$|^\d{1,2}:\d{2}$/).first()).toBeVisible();
    // "score" + "remaining" labels visible
    await expect(page.getByText("score", { exact: true })).toBeVisible();
    await expect(page.getByText("remaining", { exact: true })).toBeVisible();
    // 3 widget input boxes
    const inputs = page.locator('input[placeholder="answer"]');
    expect(await inputs.count()).toBe(3);
    // Each widget has "X pts" badge
    expect(await page.locator("text=/^\\d+ pts$/").count()).toBeGreaterThanOrEqual(3);
  });

  test("/about renders Joel-style Cards", async ({ page }) => {
    await page.goto("/about");
    await expect(page.getByRole("heading", { name: /About Amplify/i })).toBeVisible();
    await expect(page.getByText(/What this is/i)).toBeVisible();
    await expect(page.getByText(/Question sources/i)).toBeVisible();
    await expect(page.getByText(/Credits/i)).toBeVisible();
  });

  test("/tutorial renders all sections", async ({ page }) => {
    await page.goto("/tutorial");
    await expect(page.getByRole("heading", { name: "Tutorial", exact: true })).toBeVisible();
    // Card titles are <h2>. Use heading role to disambiguate from nav links.
    for (const section of [
      "Practice",
      "PBS — Parallel Burst Session",
      "Browse",
      "Your mastery (/me)",
      "Stats",
      "History",
      "Themes",
    ]) {
      await expect(page.getByRole("heading", { name: section, exact: true })).toBeVisible();
    }
  });

  test("no console errors on key routes", async ({ page }) => {
    const errors: string[] = [];
    page.on("console", (msg) => {
      if (msg.type() === "error") errors.push(msg.text());
    });
    for (const r of ["/", "/practice", "/q", "/q/1", "/stats", "/pbs", "/about", "/tutorial"]) {
      await page.goto(r);
      await page.waitForLoadState("networkidle");
    }
    // Filter out noisy / known harmless (e.g. hydration warnings, favicon)
    const real = errors.filter(
      (e) =>
        !/favicon|404|fetchAll|hydrated/i.test(e) &&
        !/Warning: Each child in a list/i.test(e)
    );
    expect(real, `Console errors found:\n${real.join("\n")}`).toEqual([]);
  });
});
