/**
 * E2E Tests - Affiliate Dashboard
 * 
 * Tests affiliate-specific functionality
 */

import { test, expect } from '@playwright/test';

// Helper to login as affiliate
async function loginAsAffiliate(page: any) {
  const email = process.env.E2E_AFFILIATE_EMAIL || 'affiliate@example.com';
  const password = process.env.E2E_AFFILIATE_PASSWORD || 'AffiliateTest123!';

  await page.goto('/login');
  await page.fill('input[type="email"]', email);
  await page.fill('input[type="password"]', password);
  await page.click('button[type="submit"]');
  await page.waitForURL('**/app');
}

test.describe('Affiliate Dashboard', () => {
  test('affiliate user can log in', async ({ page }) => {
    await loginAsAffiliate(page);

    // Assert: Successfully reached dashboard
    await expect(page).toHaveURL(/.*\/app/);
  });

  test('affiliate dashboard loads', async ({ page }) => {
    await loginAsAffiliate(page);

    // Navigate to affiliate page
    await page.goto('/app/affiliate');

    // Assert: "Sponsored accounts" or similar text visible
    await expect(page.locator('text=Sponsored, text=Affiliate, text=Agents')).toBeVisible({ timeout: 10000 });
  });

  test('sponsored accounts table is visible', async ({ page }) => {
    await loginAsAffiliate(page);
    await page.goto('/app/affiliate');

    // Wait for page load
    await page.waitForLoadState('networkidle');

    // Assert: Table header row present
    // Look for common table headers like "Name", "Email", "Status", etc.
    const tableHeader = page.locator('th, [role="columnheader"]').first();
    await expect(tableHeader).toBeVisible({ timeout: 10000 });
  });

  test('branding page renders for affiliates', async ({ page }) => {
    await loginAsAffiliate(page);

    // Navigate to branding page
    await page.goto('/app/affiliate/branding');

    // Wait for page load
    await page.waitForLoadState('networkidle');

    // Assert: Branding form is visible
    // Look for form elements like "Brand Display Name" or input fields
    const brandingForm = page.locator('text=Brand, text=Logo, text=Color, input, form').first();
    await expect(brandingForm).toBeVisible({ timeout: 10000 });
  });

  test('branding form has expected fields', async ({ page }) => {
    await loginAsAffiliate(page);
    await page.goto('/app/affiliate/branding');

    // Assert: Key form fields are present
    // Check for common branding field labels
    await expect(page.locator('text=Display Name, text=Brand Name, text=Logo')).toBeVisible({ timeout: 10000 });
    await expect(page.locator('text=Primary Color, text=Color, text=Accent')).toBeVisible({ timeout: 10000 });
  });
});

test.describe('Affiliate Branding - Non-Affiliate Access', () => {
  test('regular user gets 403 on branding page', async ({ page }) => {
    // Login as regular user
    const email = process.env.E2E_REGULAR_EMAIL || 'gerardoh@gmail.com';
    const password = process.env.E2E_REGULAR_PASSWORD || 'Test123456!';

    await page.goto('/login');
    await page.fill('input[type="email"]', email);
    await page.fill('input[type="password"]', password);
    await page.click('button[type="submit"]');
    await page.waitForURL('**/app');

    // Try to access affiliate branding
    await page.goto('/app/affiliate/branding');
    
    // Assert: Error message or "not an affiliate" text
    await expect(page.locator('text=not an affiliate, text=not an industry affiliate, text=403')).toBeVisible({ timeout: 10000 });
  });
});

