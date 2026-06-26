import { test as setup, expect } from '@playwright/test';
import { config as loadEnv } from 'dotenv';
import { mkdir } from 'fs/promises';

loadEnv({ path: '.env.test' });

const AUTH_FILE = 'e2e/.auth/user.json';
const TOKEN_KEY = 'id_token';

setup('authenticate test user', async ({ page, request }) => {
  const userPoolId = process.env.TEST_COGNITO_USER_POOL_ID;
  const clientId = process.env.TEST_COGNITO_CLIENT_ID;
  const username = process.env.TEST_COGNITO_USERNAME;
  const password = process.env.TEST_COGNITO_PASSWORD;

  if (!userPoolId || !clientId || !username || !password) {
    throw new Error(
      'Missing TEST_COGNITO_* env vars. Create frontend/.env.test — see docs/superpowers/specs/2026-06-26-playwright-e2e-design.md'
    );
  }

  const region = userPoolId.split('_')[0];

  const response = await request.post(`https://cognito-idp.${region}.amazonaws.com/`, {
    headers: {
      'Content-Type': 'application/x-amz-json-1.1',
      'X-Amz-Target': 'AWSCognitoIdentityProviderService.InitiateAuth',
    },
    data: {
      AuthFlow: 'USER_PASSWORD_AUTH',
      ClientId: clientId,
      AuthParameters: {
        USERNAME: username,
        PASSWORD: password,
      },
    },
  });

  expect(response.ok(), `Cognito InitiateAuth failed: ${await response.text()}`).toBeTruthy();

  const body = await response.json();
  const idToken: string | undefined = body?.AuthenticationResult?.IdToken;
  if (!idToken) {
    throw new Error(
      `InitiateAuth returned 200 but no IdToken — Cognito may have issued a challenge (e.g. NEW_PASSWORD_REQUIRED). Ensure the test user has completed the force-change-password step.\nBody: ${JSON.stringify(body)}`
    );
  }

  // Load the SvelteKit app shell first (localStorage is empty here — layout shows guest view)
  await page.goto('/');

  // Inject the real IdToken — same key the app uses (TOKEN_KEY = 'id_token' in client.ts)
  await page.evaluate(
    ([key, token]) => window.localStorage.setItem(key, token),
    [TOKEN_KEY, idToken] as const
  );

  // Reload: layout's onMount now reads the token and calls POST /auth/sync
  await page.goto('/');
  await page.waitForLoadState('networkidle');

  // Save storage state (includes localStorage with the injected token)
  await mkdir('e2e/.auth', { recursive: true });
  await page.context().storageState({ path: AUTH_FILE });
});
