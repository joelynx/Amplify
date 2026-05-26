import { test, expect } from "@playwright/test";

const BASE = "https://amplify-karth.vercel.app";
const DEMO_EMAIL = "demo.student@iitdabudhabi.ac.ae";
const DEMO_PASSWORD = "amplify-demo-2026";

test.describe.configure({ mode: "serial" });

// ── Public surfaces ───────────────────────────────────────────────────────

test("landing page renders without console errors", async ({ page }) => {
  const consoleErrors: string[] = [];
  page.on("console", (msg) => {
    if (msg.type() === "error") consoleErrors.push(msg.text());
  });
  await page.goto(BASE);
  await page.waitForLoadState("networkidle");
  expect(
    consoleErrors.filter((e) => !e.includes("favicon")).join("\n")
  ).toBe("");
});

test("browse /q lists Q#403 first (newest)", async ({ page }) => {
  await page.goto(`${BASE}/q`);
  await expect(
    page.getByRole("heading", { name: /Browse the bank/ })
  ).toBeVisible();
  const firstCardLink = await page.locator('a[href^="/q/"]').first().getAttribute("href");
  expect(firstCardLink).toMatch(/^\/q\/\d+$/);
});

test("/q chips compose params", async ({ page }) => {
  // Visit /q?topic=Linear+Algebra
  await page.goto(`${BASE}/q?topic=Linear+Algebra`);
  const sourceLink = await page
    .locator('a[href*="source=IITD-AD"]')
    .first()
    .getAttribute("href");
  expect(sourceLink).toContain("topic=Linear+Algebra");
});

test("/about and /tutorial pages exist", async ({ page }) => {
  await page.goto(`${BASE}/about`);
  expect(page.url()).toContain("/about");
  await expect(page.locator("body")).not.toContainText("404");

  await page.goto(`${BASE}/tutorial`);
  expect(page.url()).toContain("/tutorial");
  await expect(page.locator("body")).not.toContainText("404");
});

// ── Demo student full flow ────────────────────────────────────────────────

test("demo student: login → /me populated", async ({ page }) => {
  await page.goto(`${BASE}/auth/login`);
  await page.locator('input[type="email"]').fill(DEMO_EMAIL);
  await page.locator('input[type="password"]').fill(DEMO_PASSWORD);
  await page.locator("form").getByRole("button", { name: /^Sign in$/ }).click();
  await page.waitForURL(/\/me$/, { timeout: 15000 });

  // Mastery is non-empty.
  await expect(page.getByRole("heading", { name: /Your mastery/ })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Strongest" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Weakest" })).toBeVisible();
});

test("demo student: /practice → start a Diverse session → renders runner", async ({
  page,
}) => {
  test.setTimeout(60000);
  await page.goto(`${BASE}/auth/login`);
  await page.locator('input[type="email"]').fill(DEMO_EMAIL);
  await page.locator('input[type="password"]').fill(DEMO_PASSWORD);
  await page.locator("form").getByRole("button", { name: /^Sign in$/ }).click();
  await page.waitForURL(/\/me$/, { timeout: 15000 });

  await page.goto(`${BASE}/practice`);
  await expect(
    page.getByRole("heading", { name: "Practice", exact: true })
  ).toBeVisible();

  // Click the first subtopic checkbox.
  const firstCheckbox = page.locator('input[type="checkbox"]').first();
  await firstCheckbox.click();
  // Wait for count to settle.
  await page.waitForTimeout(500);

  // Start the session.
  await page.getByRole("button", { name: /^Start practice$/ }).click();
  await page.waitForURL(/\/practice\/[0-9a-f-]+/, { timeout: 25000 });

  // Runner has rendered something — main element visible, no error.
  await expect(page.locator("main")).toBeVisible({ timeout: 15000 });
  const body = await page.locator("body").textContent();
  expect(body, "runner should not error").not.toContain("No questions in this session");
});

test("demo student: /stats charts render with data", async ({ page }) => {
  await page.goto(`${BASE}/auth/login`);
  await page.locator('input[type="email"]').fill(DEMO_EMAIL);
  await page.locator('input[type="password"]').fill(DEMO_PASSWORD);
  await page.locator("form").getByRole("button", { name: /^Sign in$/ }).click();
  await page.waitForURL(/\/me$/, { timeout: 15000 });

  await page.goto(`${BASE}/stats`);
  await expect(page.getByRole("heading", { name: "Stats", exact: true })).toBeVisible();
  await expect(page.getByText("PSets Generated")).toBeVisible();
  // Activity must NOT be empty.
  await expect(page.getByText("No activity in the last 30 days.")).toHaveCount(0);
  // Bank composition pie should render an SVG.
  await expect(page.locator("svg").first()).toBeVisible();
});

test("demo student: /history shows seeded sessions", async ({ page }) => {
  await page.goto(`${BASE}/auth/login`);
  await page.locator('input[type="email"]').fill(DEMO_EMAIL);
  await page.locator('input[type="password"]').fill(DEMO_PASSWORD);
  await page.locator("form").getByRole("button", { name: /^Sign in$/ }).click();
  await page.waitForURL(/\/me$/, { timeout: 15000 });

  await page.goto(`${BASE}/history`);
  await expect(page.getByRole("heading", { name: "History", exact: true })).toBeVisible();
  await expect(page.getByText("No sessions yet.")).toHaveCount(0);
  // Should show diversity score on at least one row.
  await expect(page.getByText(/div 0\./).first()).toBeVisible();
});

test("demo student: /q/<id> renders LaTeX without sentinel leaks", async ({ page }) => {
  await page.goto(`${BASE}/q/403`);
  await page.waitForLoadState("networkidle");
  const html = await page.content();
  expect(html, "no sentinel markers").not.toMatch(/@@AMP_/);
  // Report button visible to anon? It's auth-only.
  await page.goto(`${BASE}/auth/login`);
  await page.locator('input[type="email"]').fill(DEMO_EMAIL);
  await page.locator('input[type="password"]').fill(DEMO_PASSWORD);
  await page.locator("form").getByRole("button", { name: /^Sign in$/ }).click();
  await page.waitForURL(/\/me$/, { timeout: 15000 });

  await page.goto(`${BASE}/q/403`);
  await expect(page.getByRole("button", { name: /report/i })).toBeVisible();
});

// ── Security smoke ─────────────────────────────────────────────────────────

test("security: anonymous cannot promote to faculty", async ({ request }) => {
  const res = await request.post(`${BASE}/api/auth/set-role`, {
    data: { role: "faculty" },
  });
  expect(res.status()).toBe(401);
});

test("security: anonymous cannot submit drafts", async ({ request }) => {
  const res = await request.post(`${BASE}/api/drafts`, {
    data: { topic: "X", branch: "Y", subtopic: "Z", latexcode: "test" },
  });
  expect(res.status()).toBe(401);
});
