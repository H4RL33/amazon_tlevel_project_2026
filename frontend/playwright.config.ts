import { defineConfig, devices } from '@playwright/test';
import { config as loadEnv } from 'dotenv';

loadEnv({ path: '.env.test' });

export default defineConfig({
  testDir: './e2e',
  timeout: 30_000,
  retries: process.env.CI ? 1 : 0,
  reporter: [['html', { open: 'never' }]],
  // No webServer block — tests target the docker-compose stack (localhost:3000).
  // Run `docker compose up -d` before `npm run test:e2e`.
  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
  },
  projects: [
    {
      // Obtains a real Cognito token via USER_PASSWORD_AUTH and saves storageState.
      name: 'setup',
      testMatch: /auth\.setup\.ts/,
      timeout: 60_000,
    },
    {
      // Unauthenticated tests — no dependency on setup so they run even if Cognito is unavailable.
      name: 'chromium-guest',
      testMatch: /guest\.spec\.ts/,
      use: { ...devices['Desktop Chrome'] },
    },
    {
      // Authenticated tests — require a valid storageState from the setup project.
      name: 'chromium-auth',
      testMatch: /auth\.spec\.ts/,
      use: { ...devices['Desktop Chrome'] },
      dependencies: ['setup'],
    },
  ],
});
