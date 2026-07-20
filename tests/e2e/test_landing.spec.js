const { test, expect } = require('@playwright/test');

test('landing page carga, hero visible y botón Acceder visible', async ({ page }) => {
  await page.goto('http://localhost:3000/landing.html');
  await expect(page.locator('nav.navbar')).toBeVisible();
  await expect(page.locator('section.hero')).toBeVisible();
  await expect(page.locator('section.hero h1')).toContainText('fichaje');
  const acceder = page.locator('a.navbar-cta', { hasText: 'Acceder' });
  await expect(acceder).toBeVisible();
  await expect(acceder).toHaveAttribute('href', 'https://jordialbarracin.github.io/talentup-fichaje/');
});
