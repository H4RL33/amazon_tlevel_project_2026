/**
 * Auth API module — Cognito PKCE token exchange and backend user sync.
 *
 * Token exchange flow:
 * 1. Cognito redirects to /auth/callback?code=<code>
 * 2. Call exchangeCode(code) to get tokens from Cognito
 * 3. Store id_token in localStorage as 'id_token'
 * 4. Call syncUser(firstName, lastName) to create/find the DB user
 */
import { apiFetch } from './client';
import type { UserResponse } from './types';

const COGNITO_DOMAIN = import.meta.env.VITE_COGNITO_DOMAIN as string;
const CLIENT_ID = import.meta.env.VITE_COGNITO_CLIENT_ID as string;
const REDIRECT_URI = import.meta.env.VITE_COGNITO_REDIRECT_URI as string;

export interface TokenResponse {
  access_token: string;
  id_token: string;
  refresh_token: string;
  expires_in: number;
  token_type: string;
}

/**
 * Exchange a Cognito authorization code for tokens using PKCE.
 * Stores the id_token in localStorage under 'id_token'.
 * Returns the full token response.
 */
export async function exchangeCode(code: string): Promise<TokenResponse> {
  const body = new URLSearchParams({
    grant_type: 'authorization_code',
    client_id: CLIENT_ID,
    code,
    redirect_uri: REDIRECT_URI,
  });
  const response = await fetch(`${COGNITO_DOMAIN}/oauth2/token`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: body.toString(),
  });
  if (!response.ok) throw new Error(`Token exchange failed: ${response.statusText}`);
  const tokens: TokenResponse = await response.json();
  localStorage.setItem('id_token', tokens.id_token);
  return tokens;
}

/**
 * Call POST /auth/sync to create or update the DB user record.
 * Must be called after exchangeCode so the id_token is in localStorage.
 */
export async function syncUser(firstName: string, lastName: string): Promise<UserResponse> {
  return apiFetch<UserResponse>('/auth/sync', {
    method: 'POST',
    body: JSON.stringify({ first_name: firstName, last_name: lastName }),
  });
}

/** Remove the stored token and redirect to the landing page. */
export function signOut(): void {
  localStorage.removeItem('id_token');
  window.location.href = '/';
}
