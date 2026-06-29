import { test, expect } from '@playwright/test';

test.describe('guest — unauthenticated paths', () => {
  test('home page shows hero and get-started button', async ({ page }) => {
    await page.goto('/');
    await expect(page.locator('h1')).toContainText('Discover your future');
    await expect(page.locator('button.cta')).toBeVisible();
  });

  test('learn page shows at least one album card', async ({ page }) => {
    await page.goto('/learn');
    // Album cards load from the API — wait up to 10 s for the first one
    await expect(page.locator('.album-card').first()).toBeVisible({ timeout: 10_000 });
  });

  test('album detail page shows sidebar and snippet content on click', async ({ page }) => {
    // Navigate to /learn, click the first album card to land on /learn/[id]
    await page.goto('/learn');
    await page.locator('.album-card').first().click();
    // Wait for SvelteKit client-side navigation to /learn/[id]
    await page.waitForURL(/\/learn\/.+/);

    // AlbumSidebar renders as <aside>
    await expect(page.locator('aside')).toBeVisible({ timeout: 10_000 });

    // Click the first NavLink inside the sidebar (a ?snippet= link)
    await page.locator('aside a').first().click();
    // Wait for the snippet content to load (URL gains ?snippet= param)
    await page.waitForLoadState('networkidle');

    // The main PageCard should now contain non-empty text (the snippet body)
    await expect(page.locator('main')).not.toBeEmpty({ timeout: 10_000 });
  });
});
