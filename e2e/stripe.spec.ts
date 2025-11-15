/**
 * E2E Tests - Stripe Integration
 * 
 * Optional tests for Stripe checkout flow
 */

import { test, expect } from '@playwright/test';

// Helper to login
async function login(page: any) {
  const email = process.env.E2E_REGULAR_EMAIL || 'gerardoh@gmail.com';
  const password = process.env.E2E_REGULAR_PASSWORD || 'Test123456!';

  await page.goto('/login');
  await page.fill('input[type="email"]', email);
  await page.fill('input[type="password"]', password);
  await page.click('button[type="submit"]');
  await page.waitForURL('**/app');
}

test.describe('Stripe Checkout', () => {
  test('clicking upgrade redirects to Stripe checkout', async ({ page }) => {
    await login(page);
    
    // Go to plan page
    await page.goto('/account/plan');
    await page.waitForLoadState('networkidle');

    // Check if this is a Free or non-Pro account by looking for upgrade button
    const upgradeButton = page.locator('text=Upgrade to Pro, text=Upgrade to Team, button:has-text("Upgrade")').first();
    
    if (await upgradeButton.isVisible()) {
      // Click the upgrade button
      await upgradeButton.click();

      // Assert: Navigation to checkout.stripe.com (test mode)
      await page.waitForURL(/.*checkout\.stripe\.com.*/, { timeout: 15000 });
      
      // Assert: Page contains Stripe checkout elements
      await expect(page).toHaveURL(/checkout\.stripe\.com/);
    } else {
      // User already has a plan or is sponsored - skip test
      test.skip();
    }
  });

  test('manage billing redirects to Stripe portal', async ({ page }) => {
    await login(page);
    
    // Go to plan page
    await page.goto('/account/plan');
    await page.waitForLoadState('networkidle');

    // Look for "Manage Billing" button (only visible for users with active subscriptions)
    const manageBillingButton = page.locator('text=Manage Billing, button:has-text("Manage")').first();
    
    if (await manageBillingButton.isVisible()) {
      // Click the manage billing button
      await manageBillingButton.click();

      // Assert: Navigation to billing.stripe.com
      await page.waitForURL(/.*billing\.stripe\.com.*/, { timeout: 15000 });
      
      // Assert: Page contains Stripe billing portal
      await expect(page).toHaveURL(/billing\.stripe\.com/);
    } else {
      // User doesn't have an active subscription - skip test
      test.skip();
    }
  });
});

test.describe('Stripe Success/Cancel Flow', () => {
  test('checkout success banner displays', async ({ page }) => {
    await login(page);
    
    // Simulate successful checkout by navigating with success query param
    await page.goto('/account/plan?checkout=success');
    
    // Assert: Success banner or message is visible
    await expect(page.locator('text=success, text=upgraded, text=thank you, [role="alert"]')).toBeVisible({ timeout: 10000 });
  });

  test('checkout cancel banner displays', async ({ page }) => {
    await login(page);
    
    // Simulate cancelled checkout by navigating with cancel query param
    await page.goto('/account/plan?checkout=cancel');
    
    // Assert: Cancel message or info is visible
    await expect(page.locator('text=cancel, text=cancelled, [role="alert"]')).toBeVisible({ timeout: 10000 });
  });
});

