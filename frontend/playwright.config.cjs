// @ts-check
const { defineConfig, devices } = require('@playwright/test');

/**
 * @see https://playwright.dev/docs/test-configuration
 */
module.exports = defineConfig({
  testDir: './e2e',
  testMatch: '*.spec.cjs',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 1,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'line',
  timeout: 30_000,
  expect: {
    timeout: 10_000,
  },
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
  ],

  /* Arrancar backend (FastAPI) y frontend (servidor estático) antes de los tests */
  webServer: [
    {
      command: 'cd ..\\backend && ..\\backend\\venv\\Scripts\\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000',
      url: 'http://localhost:8000/api/health',
      timeout: 60_000,
      reuseExistingServer: !process.env.CI,
      env: {
        DATABASE_URL: 'sqlite+aiosqlite:///./talentup_fichaje.db',
        PIN_HASH_SALT: 'test-salt',
        JWT_SECRET: 'test-secret',
        COOKIE_SECURE: 'false',
        COOKIE_SAMESITE: 'none',
      },
    },
    {
      command: 'python -m http.server 3000',
      url: 'http://localhost:3000',
      timeout: 30_000,
      reuseExistingServer: !process.env.CI,
    },
  ],
});
