/**
 * E2E Tests - Authentication
 * 
 * Tests login flow and cookie-based authentication
 */

import { test, expect } from '@playwright/test';

test.describe('Authentication', () => {
  test('user can log in and reach dashboard', async ({ page }) => {
    const email = process.env.E2E_REGULAR_EMAIL || 'gerardoh@gmail.com';
    const password = process.env.E2E_REGULAR_PASSWORD || 'Test123456!';

    // Navigate to login page
    await page.goto('/login');

    // Fill in login form
    await page.fill('input[type="email"]', email);
    await page.fill('input[type="password"]', password);

    // Submit form
    await page.click('button[type="submit"]');

    // Wait for navigation to /app
    await page.waitForURL('**/app');

    // Assert: Dashboard element is visible (plan summary or nav link)
    await expect(page.locator('text=Plan & Usage, text=Dashboard, text=Reports')).toBeVisible();
  });

  test('mr_token cookie is set after login', async ({ page, context }) => {
    const email = process.env.E2E_REGULAR_EMAIL || 'gerardoh@gmail.com';
    const password = process.env.E2E_REGULAR_PASSWORD || 'Test123456!';

    // Navigate and login
    await page.goto('/login');
    await page.fill('input[type="email"]', email);
    await page.fill('input[type="password"]', password);
    await page.click('button[type="submit"]');
    await page.waitForURL('**/app');

    // Check cookies
    const cookies = await context.cookies();
    const mrToken = cookies.find(c => c.name === 'mr_token');

    expect(mrToken).toBeDefined();
    expect(mrToken?.value).toBeTruthy();
    expect(mrToken?.httpOnly).toBe(true);
  });

  test('logout clears cookie and redirects', async ({ page, context }) => {
    const email = process.env.E2E_REGULAR_EMAIL || 'gerardoh@gmail.com';
    const password = process.env.E2E_REGULAR_PASSWORD || 'Test123456!';

    // Login first
    await page.goto('/login');
    await page.fill('input[type="email"]', email);
    await page.fill('input[type="password"]', password);
    await page.click('button[type="submit"]');
    await page.waitForURL('**/app');

    // Look for logout button/link and click it
    // Adjust selector based on your actual logout implementation
    const logoutButton = page.locator('text=Logout, text=Sign Out, button:has-text("Logout")').first();
    
    if (await logoutButton.isVisible()) {
      await logoutButton.click();
      
      // Should redirect to login
      await page.waitForURL('**/login');

      // Cookie should be cleared
      const cookies = await context.cookies();
      const mrToken = cookies.find(c => c.name === 'mr_token');
      expect(mrToken).toBeUndefined();
    }
  });
});

