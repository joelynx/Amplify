import { test, expect } from "@playwright/test";

test.describe("LaTeX render audit", () => {
  test("q/1 — question body has no leaking \\textbf / \\begin{}", async ({ page }) => {
    await page.goto("/q/1");
    await page.waitForLoadState("networkidle");

    // Article holds the question body (rendered server-side via LatexBlock).
    const articleText = await page.locator("article").innerText();
    console.log("--- q/1 article text ---");
    console.log(articleText);

    // Take a screenshot for visual confirmation.
    await page.screenshot({ path: "tests/e2e/screenshots/q1-question.png", fullPage: true });

    expect(articleText).not.toContain("\\textbf");
    expect(articleText).not.toContain("\\begin{");
    expect(articleText).not.toContain("\\end{");
    expect(articleText).not.toContain("\\item");
  });

  test("q/1 — reveal solution and audit", async ({ page }) => {
    await page.goto("/q/1");
    await page.waitForLoadState("networkidle");

    // Find and click the reveal-solution button.
    const reveal = page.getByRole("button", { name: /reveal solution/i });
    await reveal.click();

    // Wait for the solution panel to mount.
    await page.waitForSelector("text=Solution", { state: "visible" });

    // Read the entire main panel after reveal.
    const mainText = await page.locator("main").innerText();
    console.log("--- q/1 main text (post-reveal) ---");
    console.log(mainText);

    await page.screenshot({
      path: "tests/e2e/screenshots/q1-solution-revealed.png",
      fullPage: true,
    });

    // Hard checks — these are what Karth was seeing.
    expect(mainText).not.toContain("\\textbf");
    expect(mainText).not.toContain("\\textit");
    expect(mainText).not.toContain("\\emph");
    expect(mainText).not.toContain("\\begin{");
    expect(mainText).not.toContain("\\end{");
  });

  test("practice form — Diverse mode + Kulesza-Taskar callout visible", async ({ page }) => {
    await page.goto("/practice");
    await page.waitForLoadState("networkidle");

    const bodyText = await page.locator("body").innerText();
    expect(bodyText).toContain("Generation mode");
    expect(bodyText).toContain("Diverse");
    expect(bodyText).toContain("Random");
    expect(bodyText).toMatch(/Kulesza/i);

    await page.screenshot({ path: "tests/e2e/screenshots/practice-form.png", fullPage: true });
  });
});
