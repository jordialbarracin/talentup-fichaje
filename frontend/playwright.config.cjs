// @ts-check
const { defineConfig, devices } = require('@playwright/test');
const path = require('path');
const fs = require('fs');

const backendDir = path.resolve(__dirname, '..', 'backend');
const pythonExe = path.join(backendDir, 'venv', 'Scripts', 'python.exe');
const dbFile = path.join(backendDir, 'talentup_fichaje.db');

module.exports = defineConfig({
  testDir: './e2e',
  testMatch: '*.spec.cjs',
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 1,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'line',
  timeout: 30_000,
  expect: { timeout: 10_000 },
  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    headless: true,
  },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
  webServer: [
    {
      // Delete old DB, seed fresh, then start backend
      command: `"${pythonExe}" -c "import os,asyncio; os.chdir(r'${backendDir}'); os.environ['DATABASE_URL']='sqlite+aiosqlite:///./talentup_fichaje.db'; os.environ['PIN_HASH_SALT']='test-salt'; os.environ['JWT_SECRET']='test-secret'; [os.remove(f) for f in [x for x in os.listdir('.') if x.startswith('talentup_fichaje.db')]]; from app.seed import seed; asyncio.run(seed())" && "${pythonExe}" -m uvicorn app.main:app --host 0.0.0.0 --port 8080`,
      cwd: backendDir,
      url: 'http://localhost:8080/api/health',
      timeout: 60_000,
      reuseExistingServer: false,
      env: {
        DATABASE_URL: 'sqlite+aiosqlite:///./talentup_fichaje.db',
        PIN_HASH_SALT: 'test-salt',
        JWT_SECRET: 'test-secret',
        COOKIE_SECURE: 'false',
        COOKIE_SAMESITE: 'lax',
      },
    },
    {
      command: 'python -m http.server 3000',
      url: 'http://localhost:3000',
      timeout: 30_000,
      reuseExistingServer: false,
    },
  ],
});
