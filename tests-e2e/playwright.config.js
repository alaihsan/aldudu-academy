// @ts-check
const { defineConfig, devices } = require('@playwright/test');

const PYTHON_BIN = process.env.PYTHON_BIN || 'python3';
const PORT = process.env.E2E_PORT || '5055';
const BASE_URL = `http://127.0.0.1:${PORT}`;

module.exports = defineConfig({
  testDir: './tests',
  timeout: 30_000,
  fullyParallel: false, // shared SQLite file + single Flask dev server
  workers: 1,
  reporter: [['list']],
  use: {
    baseURL: BASE_URL,
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
  },
  projects: [
    {
      name: 'chromium',
      use: {
        ...devices['Desktop Chrome'],
        launchOptions: {
          executablePath: '/opt/pw-browsers/chromium',
        },
      },
    },
  ],
  webServer: {
    // Reseed the throwaway SQLite DB, then boot the Flask dev server against it.
    command: `${PYTHON_BIN} seed.py && ${PYTHON_BIN} ../run.py`,
    url: BASE_URL,
    reuseExistingServer: !process.env.CI,
    timeout: 60_000,
    cwd: __dirname,
    env: {
      SECRET_KEY: 'e2e-smoke-test-secret-key-not-for-prod-32chars',
      DATABASE_URL: `sqlite:///${__dirname}/../instance/e2e_test.db`,
      APP_URL: BASE_URL,
      FLASK_DEBUG: '0',
    },
  },
});
