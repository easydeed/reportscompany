/**
 * E2E Tests - Plan & Usage Page
 * 
 * Tests that the plan page loads and displays plan information correctly
 */

import { test, expect } from '@playwright/test';

// Helper to login before each test
async function login(page: any) {
  const email = process.env.E2E_REGULAR_EMAIL || 'gerardoh@gmail.com';
  const password = process.env.E2E_REGULAR_PASSWORD || 'Test123456!';

  await page.goto('/login');
  await page.fill('input[type="email"]', email);
  await page.fill('input[type="password"]', password);
  await page.click('button[type="submit"]');
  await page.waitForURL('**/app');
}

test.describe('Plan & Usage Page', () => {
  test('plan page loads after login', async ({ page }) => {
    await login(page);

    // Navigate to plan page
    await page.goto('/account/plan');

    // Assert: "Plan & Usage" text appears
    await expect(page.locator('text=Plan & Usage, text=Plan, text=Usage')).toBeVisible({ timeout: 10000 });
  });

  test('plan name is visible', async ({ page }) => {
    await login(page);
    await page.goto('/account/plan');

    // Assert: Plan name (Free, Pro, Team, etc.) is visible
    // Using a regex to match common plan names
    await expect(page.locator('text=/Free|Professional|Pro|Team|Sponsored/')).toBeVisible({ timeout: 10000 });
  });

  test('usage meter or usage text is present', async ({ page }) => {
    await login(page);
    await page.goto('/account/plan');

    // Assert: Usage meter shows format like "X / Y" or "X of Y"
    // or a progress bar/meter element exists
    const usageMeter = page.locator('text=/ , text= of , [role="progressbar"]').first();
    await expect(usageMeter).toBeVisible({ timeout: 10000 });
  });

  test('stripe buttons visible for non-sponsored accounts', async ({ page }) => {
    await login(page);
    await page.goto('/account/plan');

    // Wait for page to load
    await page.waitForLoadState('networkidle');

    // Check if this is a sponsored account by looking for "sponsored" text
    const isSponsoredAccount = await page.locator('text=sponsored').count() > 0;

    if (!isSponsoredAccount) {
      // Assert: Upgrade or Manage Billing button should be visible
      const stripeButton = page.locator('text=Upgrade, text=Manage Billing, button:has-text("Upgrade"), button:has-text("Manage")').first();
      await expect(stripeButton).toBeVisible({ timeout: 5000 });
    }
  });
});

