import { test, expect } from "@playwright/test";

const BASE = "https://amplify-karth.vercel.app";

test("q: clicking source chip preserves active topic param", async ({ page }) => {
  // Land on /q first to discover a real topic.
  await page.goto(`${BASE}/q`);

  const firstTopicHref = await page
    .locator('a[href*="?topic="]')
    .first()
    .getAttribute("href");
  expect(firstTopicHref, "should find at least one topic chip").not.toBeNull();

  // Navigate to /q?topic=X
  await page.goto(`${BASE}${firstTopicHref}`);
  await page.waitForLoadState("networkidle");
  expect(page.url()).toContain("topic=");

  // Find a source chip Link (one that has source= AND topic= in it now).
  const sourceLink = page
    .locator('a[href*="source="]')
    .filter({ hasNotText: "All" })
    .first();
  const sourceHref = await sourceLink.getAttribute("href");
  expect(sourceHref, "source href should preserve topic").toContain("topic=");
  expect(sourceHref).toContain("source=");

  // Click it and verify the resulting URL has both.
  await sourceLink.click();
  await page.waitForLoadState("networkidle");
  const url = new URL(page.url());
  expect(url.searchParams.get("topic")).not.toBeNull();
  expect(url.searchParams.get("source")).not.toBeNull();
});

test("q: clicking topic chip preserves active source param", async ({ page }) => {
  await page.goto(`${BASE}/q`);

  // Find a source href to seed the URL.
  const firstSourceHref = await page
    .locator('a[href*="?source="]')
    .first()
    .getAttribute("href");
  expect(firstSourceHref).not.toBeNull();

  await page.goto(`${BASE}${firstSourceHref}`);
  await page.waitForLoadState("networkidle");
  expect(page.url()).toContain("source=");

  // Find a topic chip and verify its href has source= in it.
  const topicLink = page
    .locator('a[href*="topic="]')
    .filter({ hasNotText: "All" })
    .first();
  const topicHref = await topicLink.getAttribute("href");
  expect(topicHref).toContain("topic=");
  expect(topicHref, "topic chip href should preserve source").toContain("source=");
});
