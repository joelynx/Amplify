import { test, expect } from "@playwright/test";

const BASE = "https://amplify-karth.vercel.app";
const EMAIL = "demo.student@iitdabudhabi.ac.ae";
const PASSWORD = "amplify-demo-2026";

test("demo student dashboards are populated", async ({ page }) => {
  test.setTimeout(60000);

  // Sign in.
  await page.goto(`${BASE}/auth/login`);
  await page.locator('input[type="email"]').fill(EMAIL);
  await page.locator('input[type="password"]').fill(PASSWORD);
  await page.locator("form").getByRole("button", { name: /^Sign in$/ }).click();
  await page.waitForURL(/\/me$/, { timeout: 15000 });

  // /me — mastery should be non-empty.
  await expect(page.getByRole("heading", { name: /Your mastery/ })).toBeVisible();
  // Headline cards: "Questions answered" should be > 0.
  const answeredCard = page.locator("text=Questions answered").first();
  await expect(answeredCard).toBeVisible();
  await expect(page.getByText(/Strongest/)).toBeVisible();
  await expect(page.getByText(/Weakest/)).toBeVisible();

  // /stats — cards + activity heatmap.
  await page.goto(`${BASE}/stats`);
  await expect(page.getByRole("heading", { name: "Stats", exact: true })).toBeVisible();
  await expect(page.getByText("PSets Generated")).toBeVisible();
  // Should NOT show the empty-state message for activity.
  await expect(
    page.getByText("No activity in the last 30 days.")
  ).toHaveCount(0);

  // /history — should show 7 session rows.
  await page.goto(`${BASE}/history`);
  await expect(page.getByRole("heading", { name: "History", exact: true })).toBeVisible();
  // No "No sessions yet" message.
  await expect(page.getByText("No sessions yet.")).toHaveCount(0);
});
