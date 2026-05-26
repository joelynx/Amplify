import { test, expect, type Page } from "@playwright/test";

const BASE = "https://amplify-karth.vercel.app";

const RUN = Date.now();
const STUDENT_EMAIL = `student-${RUN}@e2e.amplify`;
const TA_EMAIL = `ta-${RUN}@e2e.amplify`;
const PASSWORD = "demo-password-123";

async function signUp(
  page: Page,
  email: string,
  password: string,
  role: "student" | "ta"
) {
  await page.goto(`${BASE}/auth/login`);
  await page.getByRole("button", { name: /^Sign up$/ }).click();
  if (role === "ta") {
    await page.getByRole("button", { name: /TA \/ contributor/ }).click();
  }
  await page.locator('input[type="email"]').fill(email);
  await page.locator('input[type="password"]').fill(password);
  await page.getByRole("button", { name: /Create account/ }).click();
}

test.describe.configure({ mode: "serial" });

// ─────────────────────────────────────────────────────────────────────────
// Auth gates — anonymous users blocked from gated routes
// ─────────────────────────────────────────────────────────────────────────

test("anon: /practice → /auth/login", async ({ page }) => {
  await page.goto(`${BASE}/practice`);
  await expect(page).toHaveURL(/\/auth\/login/);
});

test("anon: /stats → /auth/login", async ({ page }) => {
  await page.goto(`${BASE}/stats`);
  await expect(page).toHaveURL(/\/auth\/login/);
});

test("anon: /me → /auth/login", async ({ page }) => {
  await page.goto(`${BASE}/me`);
  await expect(page).toHaveURL(/\/auth\/login/);
});

test("anon: /history → /auth/login", async ({ page }) => {
  await page.goto(`${BASE}/history`);
  await expect(page).toHaveURL(/\/auth\/login/);
});

test("anon: /author → /auth/login", async ({ page }) => {
  await page.goto(`${BASE}/author`);
  await expect(page).toHaveURL(/\/auth\/login/);
});

test("anon: /q is public", async ({ page }) => {
  await page.goto(`${BASE}/q`);
  await expect(
    page.getByRole("heading", { name: /Browse the bank/ })
  ).toBeVisible();
});

// ─────────────────────────────────────────────────────────────────────────
// Student flow — one big serial test, signup then everything
// ─────────────────────────────────────────────────────────────────────────

test("student: signup → /me → /practice → /q → /stats → /history → /author gated", async ({
  page,
}) => {
  test.setTimeout(180000);

  // ── 1. Sign up as a student.
  await signUp(page, STUDENT_EMAIL, PASSWORD, "student");
  await page.waitForURL(/\/me$/, { timeout: 30000 });

  // ── 2. Verify student nav (Practice/Stats/History, NO Author).
  const nav = page.getByRole("navigation");
  await expect(
    nav.getByRole("link", { name: "Practice", exact: true })
  ).toBeVisible();
  await expect(
    nav.getByRole("link", { name: "Stats", exact: true })
  ).toBeVisible();
  await expect(
    nav.getByRole("link", { name: "History", exact: true })
  ).toBeVisible();
  await expect(
    nav.getByRole("link", { name: "Author", exact: true })
  ).toHaveCount(0);

  // ── 3. /me — fresh-state empty mastery heading is visible.
  await expect(
    page.getByRole("heading", { name: /Your mastery/ })
  ).toBeVisible();

  // ── 4. /practice — page loads, Diverse mode visible.
  await page.goto(`${BASE}/practice`);
  await expect(
    page.getByRole("heading", { name: "Practice", exact: true })
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Diverse", exact: true })
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: /^Start practice$/ })
  ).toBeVisible();

  // ── 5. /q — browse list renders, click into a question.
  await page.goto(`${BASE}/q`);
  await expect(
    page.getByRole("heading", { name: /Browse the bank/ })
  ).toBeVisible();
  const firstQLink = page.locator('a[href^="/q/"]').first();
  await firstQLink.click();
  await page.waitForURL(/\/q\/\d+/, { timeout: 10000 });
  // Report button is auth-only — student is signed in, so should be visible.
  await expect(page.getByRole("button", { name: /report/i })).toBeVisible();

  // ── 6. /stats — stat cards render.
  await page.goto(`${BASE}/stats`);
  await expect(
    page.getByRole("heading", { name: "Stats", exact: true })
  ).toBeVisible();
  await expect(page.getByText("PSets Generated")).toBeVisible();

  // ── 7. /history — heading renders.
  await page.goto(`${BASE}/history`);
  await expect(
    page.getByRole("heading", { name: "History", exact: true })
  ).toBeVisible();

  // ── 8. Try to visit /author — student should be blocked or redirected.
  await page.goto(`${BASE}/author`);
  await page.waitForLoadState("networkidle");
  // Student must NOT see the authoring form's "Submit to the bank" button.
  await expect(
    page.getByRole("button", { name: /Submit to the bank/ })
  ).toHaveCount(0);
});

// ─────────────────────────────────────────────────────────────────────────
// TA flow — one big serial test, signup → submit → verify live
// ─────────────────────────────────────────────────────────────────────────

test("TA: signup → /author → submit question → goes live in /q → role-gated", async ({
  page,
}) => {
  test.setTimeout(180000);

  // ── 1. Sign up as a TA.
  await signUp(page, TA_EMAIL, PASSWORD, "ta");
  await page.waitForURL(/\/author$/, { timeout: 30000 });

  // ── 2. Nav must show Author and NOT Practice/Stats/History.
  const nav = page.getByRole("navigation");
  await expect(
    nav.getByRole("link", { name: "Author", exact: true })
  ).toBeVisible();
  await expect(
    nav.getByRole("link", { name: "Practice", exact: true })
  ).toHaveCount(0);
  await expect(
    nav.getByRole("link", { name: "Stats", exact: true })
  ).toHaveCount(0);
  await expect(
    nav.getByRole("link", { name: "History", exact: true })
  ).toHaveCount(0);

  await expect(
    page.getByRole("heading", { name: /Add to the commons/ })
  ).toBeVisible();

  // ── 3. Submit a sentinel question.
  const unique = `E2E-Sentinel-${RUN}`;
  const sourceTag = `Tut Sheet ${RUN}`;

  const listInputs = page.locator("input[list]");
  await listInputs.nth(0).fill(unique);
  await listInputs.nth(1).fill("e2e-branch");
  await listInputs.nth(2).fill("e2e-subtopic");

  await page
    .locator("textarea")
    .first()
    .fill(`Evaluate $\\int_0^1 x^2 \\, dx$. (sentinel ${unique})`);

  // Answer input — placeholder unique substring.
  await page.locator('input[placeholder*="e^{i"]').fill("1/3");
  // Source input — placeholder unique substring.
  await page.locator('input[placeholder*="IITD-AD Quiz"]').fill(sourceTag);

  await page.getByRole("button", { name: /^Submit to the bank$/ }).click();

  // Wait for success message.
  await expect(page.getByText(/is live\. Embedded, tagged/)).toBeVisible({
    timeout: 90000,
  });

  // ── 4. Verify it's queryable on /q via the unique source.
  await page.goto(`${BASE}/q?source=${encodeURIComponent(sourceTag)}`);
  await page.waitForLoadState("networkidle");
  await expect(page.getByText(unique).first()).toBeVisible({
    timeout: 15000,
  });

  // ── 5. Confirm role-gating: TA visits /practice, /me, /stats, /history.
  for (const route of ["/practice", "/me", "/stats", "/history"]) {
    await page.goto(`${BASE}${route}`);
    await expect(page).toHaveURL(/\/author/, { timeout: 10000 });
  }
});
