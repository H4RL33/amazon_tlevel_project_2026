import type { UserResponse } from './types';

export interface TokenResponse {
  access_token: string;
  id_token: string;
  refresh_token: string;
  expires_in: number;
  token_type: string;
}

export function getCognitoLoginUrl(): string {
  throw new Error('not implemented');
}

export async function exchangeCode(_code: string): Promise<TokenResponse> {
  throw new Error('not implemented');
}

export async function syncUser(_firstName: string, _lastName: string): Promise<UserResponse> {
  throw new Error('not implemented');
}

export function signOut(): void {
  throw new Error('not implemented');
}
