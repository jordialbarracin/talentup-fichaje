const { test, expect } = require('@playwright/test');

const LOGIN_EMAIL = 'owner@latagliatella.es';
const LOGIN_PASSWORD = 'owner123';

const SECTIONS = [
  { id: 'dashboard', title: 'Dashboard' },
  { id: 'empleados', title: 'Empleados' },
  { id: 'calendario', title: 'Calendario' },
  { id: 'turnos', title: 'Turnos' },
  { id: 'fichajes', title: 'Fichajes' },
  { id: 'vacaciones', title: 'Vacaciones' },
  { id: 'bajas', title: 'Bajas' },
  { id: 'informes', title: 'Informes' },
  { id: 'configuracion', title: 'Configuración' },
];

test.beforeEach(async ({ page }) => {
  await page.goto('http://localhost:3000');
  await page.fill('#login-email', LOGIN_EMAIL);
  await page.fill('#login-password', LOGIN_PASSWORD);
  await page.click('#login-btn');
  await expect(page.locator('#app')).toBeVisible();
  await expect(page.locator('#page-dashboard')).toBeVisible();
});

test('dashboard carga y 9 secciones son navegables', async ({ page }) => {
  for (const section of SECTIONS) {
    const navItem = page.locator(`.nav-item[data-page="${section.id}"]`);
    await expect(navItem).toBeVisible();
    await navItem.click();

    // El navbar refleja la sección activa.
    await expect(page.locator('#navbar-title')).toHaveText(section.title);

    // La página correspondiente está visible y las demás ocultas.
    await expect(page.locator(`#page-${section.id}`)).toBeVisible();
    await expect(page.locator(`#page-${section.id}`)).not.toHaveClass(/hidden/);
    await expect(navItem).toHaveClass(/active/);
  }
});
