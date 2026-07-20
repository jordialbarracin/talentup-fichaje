// @ts-check
const { defineConfig, devices } = require('@playwright/test');

/**
 * @see https://playwright.dev/docs/test-configuration
 */
module.exports = defineConfig({
  testDir: './tests/e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'list',
  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    headless: true,
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    // Tests móviles se ejecutan en chromium con viewport reducido dentro del mismo test.
  ],

  // No lanzamos automáticamente servidores para no interferir con los existentes.
  // El usuario debe tener corriendo:
  //   - backend en http://localhost:8000
  //   - frontend/landing en http://localhost:3000
  //   - terminal en http://localhost:3001
  //   - PWA mobile en http://localhost:3000/mobile/
  webServer: [],
});
