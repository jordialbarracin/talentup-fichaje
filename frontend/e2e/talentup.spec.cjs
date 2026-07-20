// @ts-check
const { test, expect } = require('@playwright/test');

const LOGIN_EMAIL = process.env.TEST_LOGIN_EMAIL || 'owner@latagliatella.es';
const LOGIN_PASSWORD = process.env.TEST_LOGIN_PASSWORD || 'owner123';

/**
 * TalentUP Fichaje — End-to-end tests
 *
 * Tests run against the local frontend served at http://localhost:3000
 * and the FastAPI backend at http://localhost:8000 (started by Playwright's webServer).
 */

test('Landing page muestra título y CTA', async ({ page }) => {
  await page.goto('/landing.html');
  await expect(page).toHaveTitle(/TalentUP Fichaje/);
  await expect(page.locator('h1')).toContainText(/El fichaje que entiende la hosteler[íi]a/);
  await expect(page.locator('.btn-primary').first()).toBeVisible();
});

test('Login con owner redirige al dashboard', async ({ page }) => {
  await page.goto('/');
  await expect(page.locator('#login-screen')).toBeVisible();

  await page.fill('#login-email', LOGIN_EMAIL);
  await page.fill('#login-password', LOGIN_PASSWORD);
  await page.click('#login-btn');

  await expect(page.locator('#app')).not.toHaveClass(/hidden/);
  await expect(page.locator('#navbar-name')).toContainText(/María García|owner@latagliatella.es/);
  await expect(page.locator('#page-dashboard')).toBeVisible();
  await expect(page.locator('#online-text')).toContainText('Conectado');
});

test('Dashboard muestra elementos clave', async ({ page }) => {
  await page.goto('/');
  await page.fill('#login-email', LOGIN_EMAIL);
  await page.fill('#login-password', LOGIN_PASSWORD);
  await page.click('#login-btn');
  await page.waitForSelector('#page-dashboard', { state: 'visible' });

  await expect(page.locator('#stats-grid')).toBeVisible();
  await expect(page.locator('#stat-empleados')).toBeVisible();
  await expect(page.locator('#stat-fichajes')).toBeVisible();
  await expect(page.locator('#stat-incidencias')).toBeVisible();
  await expect(page.locator('#stat-extras')).toBeVisible();
  await expect(page.locator('#dashboard-table-body')).toBeVisible();
  await expect(page.locator('[data-page="empleados"]')).toContainText('Empleados');
});

test('Crear un empleado y aparece en la lista', async ({ page }) => {
  await page.goto('/');
  await page.fill('#login-email', LOGIN_EMAIL);
  await page.fill('#login-password', LOGIN_PASSWORD);
  await page.click('#login-btn');
  await page.waitForSelector('#page-dashboard', { state: 'visible' });

  // Navegar a Empleados
  await page.click('[data-page="empleados"]');
  await page.waitForSelector('#page-empleados', { state: 'visible' });

  // Abrir modal de añadir empleado haciendo click en el botón de la UI
  await page.getByRole('button', { name: /Añadir empleado/i }).click();
  await expect(page.locator('#modal-emp-name')).toBeVisible();

  const unique = Date.now();
  await page.fill('#modal-emp-name', `E2E-${unique}`);
  await page.fill('#modal-emp-lastname', 'Test');
  await page.fill('#modal-emp-dni', `${unique}T`);
  await page.fill('#modal-emp-nss', `${unique}SS`);
  await page.fill('#modal-emp-category', 'Camarero/a');
  await page.selectOption('#modal-emp-contract', 'IND');
  await page.fill('#modal-emp-pin', '1234');

  await page.getByRole('button', { name: /Guardar/i }).click();

  // Esperar a que aparezca el toast de éxito y la tabla recargue
  await expect(page.locator('.toast-success')).toContainText('Empleado creado', { timeout: 15_000 });
  await expect(page.locator('#empleados-table-body')).toContainText(`E2E-${unique}`);
});

test('Logout vuelve a la pantalla de login', async ({ page }) => {
  await page.goto('/');
  await page.fill('#login-email', LOGIN_EMAIL);
  await page.fill('#login-password', LOGIN_PASSWORD);
  await page.click('#login-btn');
  await page.waitForSelector('#app', { state: 'visible' });

  await page.click('#navbar-logout');

  await expect(page.locator('#login-screen')).toBeVisible();
  await expect(page.locator('#login-email')).toHaveValue('');
  await expect(page.locator('#login-password')).toHaveValue('');
});
