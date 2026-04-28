import { test, expect } from '@playwright/test';

test.describe('Dashboard Theme & Settings', () => {
  // Use the local dev server or target url
  test.use({ baseURL: process.env.BASE_URL || 'http://localhost:3000' });

  test('should allow user to toggle dark and light modes via Appearance Settings', async ({ page }) => {
    // 1. Visit Login page
    await page.goto('/login');
    
    // Expect login page to be loaded
    await expect(page.getByText('Data Leak Monitor')).toBeVisible();

    // Log in using default credentials explicitly for e2e
    // In actual E2E, it's better to have test environment credentials injected. 
    await page.fill('input[type="email"]', 'admin@dataleak.com');
    await page.fill('input[type="password"]', 'admin123');
    await page.click('button[type="submit"]');

    // 2. Expect successful login & redirect to dashboard overview
    await expect(page).toHaveURL('/');
    await expect(page.getByText('Monitoring Active')).toBeVisible({ timeout: 10000 });

    // 3. Navigate to Settings page
    await page.click('button:has-text("Settings")');
    await expect(page.getByText('Theme Preferences')).toBeVisible();

    // 4. Test Theme Toggling
    const html = page.locator('html');
    
    // Initially dark
    await expect(html).toHaveClass(/dark/);
    
    // Switch to Light Mode
    await page.click('button:has-text("Light")');
    await expect(html).not.toHaveClass(/dark/);

    // Switch to Dark Mode
    await page.click('button:has-text("Dark")');
    await expect(html).toHaveClass(/dark/);
    
    console.log("✅ Theme toggle successfully verified via Settings Panel.");
  });
});
