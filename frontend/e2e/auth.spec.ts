import { test, expect } from '@playwright/test';

test.use({ storageState: 'e2e/.auth/user.json' });

test.describe('authenticated paths', () => {
  test('home page shows authenticated layout with CTASidebar', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Authenticated branch renders .home-auth (not the guest hero)
    await expect(page.locator('.home-auth')).toBeVisible({ timeout: 10_000 });

    // Greeting is visible (Good morning/afternoon/evening, <name> 👋)
    await expect(page.locator('.greeting')).toBeVisible({ timeout: 10_000 });
  });

  test('settings page renders sidebar and upload controls', async ({ page }) => {
    await page.goto('/settings');
    await page.waitForLoadState('networkidle');

    // Sidebar NavLink
    await expect(page.getByText('Personalisation')).toBeVisible({ timeout: 10_000 });

    // Upload button in the content card
    await expect(page.locator('button', { hasText: 'Choose file' })).toBeVisible();
  });
});
