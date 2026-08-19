import { test, expect } from "@playwright/test";

test("website foundation shell loads", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Customer Website foundation" })).toBeVisible();
});
