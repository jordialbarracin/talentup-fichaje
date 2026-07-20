const { test, expect } = require('@playwright/test');

const LOGIN_EMAIL = 'owner@latagliatella.es';
const LOGIN_PASSWORD = 'owner123';

test('login con credenciales reales entra al dashboard', async ({ page }) => {
  await page.goto('http://localhost:3000');
  await expect(page.locator('#login-screen')).toBeVisible();

  await page.fill('#login-email', LOGIN_EMAIL);
  await page.fill('#login-password', LOGIN_PASSWORD);

  const loginPromise = page.waitForResponse((res) =>
    res.url().includes('/api/auth/login') && res.request().method() === 'POST'
  );
  await page.click('#login-btn');
  const loginRes = await loginPromise;
  expect(loginRes.status()).toBe(200);

  // Esperamos a que la app renderice el dashboard tras login real.
  await expect(page.locator('#app')).toBeVisible();
  await expect(page.locator('#sidebar')).toBeVisible();
  await expect(page.locator('#page-dashboard')).toBeVisible();
  await expect(page.locator('#navbar-name')).toHaveText(/María García|owner@latagliatella\.es/);
});
