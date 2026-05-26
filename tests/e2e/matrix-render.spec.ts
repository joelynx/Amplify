import { test, expect } from "@playwright/test";

test("matrix questions don't leak the @@AMP_BR@@ sentinel", async ({ page }) => {
  // Walk a sample of questions; the bug was inside matrix-containing rows.
  for (const id of [178, 179, 196, 52]) {
    await page.goto(`/q/${id}`);
    const body = await page.locator("body").innerText();
    expect(body, `q/${id} leaks @@AMP`).not.toContain("@@AMP");
  }
});
