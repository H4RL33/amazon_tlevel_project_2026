import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { decodeJwtPayload, exchangeCode, getCognitoLoginUrl, signOut, syncUser } from './auth';
import { TOKEN_KEY } from './client';

function makeUnsignedJwt(payload: Record<string, unknown>): string {
  const base64url = (json: string) =>
    btoa(json).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
  return `${base64url('{"alg":"none"}')}.${base64url(JSON.stringify(payload))}.`;
}

describe('decodeJwtPayload', () => {
  it('decodes a base64url-encoded payload regardless of padding/character substitutions', () => {
    // payloads of varying length exercise every padding case (0/1/2 '=' chars stripped),
    // and varying content makes - / _ substitutions in the base64url encoding likely
    const payloads = [
      { sub: 'a' },
      { sub: 'ab', given_name: 'Test' },
      { sub: 'abc', given_name: 'Test', family_name: 'User-Name_123' },
    ];

    for (const payload of payloads) {
      expect(decodeJwtPayload(makeUnsignedJwt(payload))).toEqual(payload);
    }
  });
});

describe('getCognitoLoginUrl', () => {
  it('builds a Hosted UI authorize URL with PKCE params and stores the verifier', async () => {
    const url = await getCognitoLoginUrl();

    expect(url).toContain('/login?');
    expect(url).toContain('response_type=code');
    expect(url).toContain('code_challenge=');
    expect(url).toContain('code_challenge_method=S256');
    expect(sessionStorage.getItem('pkce_code_verifier')).toBeTruthy();
  });
});

describe('exchangeCode', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    sessionStorage.clear();
  });

  it('POSTs to the Cognito token endpoint with the stored code_verifier', async () => {
    sessionStorage.setItem('pkce_code_verifier', 'stored-verifier');
    const tokenResponse = {
      access_token: 'a',
      id_token: 'b',
      refresh_token: 'c',
      expires_in: 3600,
      token_type: 'Bearer',
    };
    const mockFetch = vi
      .fn()
      .mockResolvedValue(new Response(JSON.stringify(tokenResponse), { status: 200 }));
    vi.stubGlobal('fetch', mockFetch);

    const result = await exchangeCode('auth-code-123');

    expect(result).toEqual(tokenResponse);
    const [, init] = mockFetch.mock.calls[0];
    expect(init.body).toContain('code=auth-code-123');
    expect(init.body).toContain('code_verifier=stored-verifier');
  });

  it('throws when Cognito returns a non-2xx response', async () => {
    sessionStorage.setItem('pkce_code_verifier', 'stored-verifier');
    const mockFetch = vi
      .fn()
      .mockResolvedValue(new Response(JSON.stringify({ error: 'invalid_grant' }), { status: 400 }));
    vi.stubGlobal('fetch', mockFetch);

    await expect(exchangeCode('bad-code')).rejects.toThrow();
  });
});

describe('syncUser', () => {
  beforeEach(() => {
    localStorage.setItem(TOKEN_KEY, 'fake-id-token');
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    localStorage.clear();
  });

  it('POSTs to /auth/sync with the stored id_token as a bearer header', async () => {
    const user = {
      id: 1,
      cognito_sub: 'sub-1',
      email: 'a@example.com',
      first_name: 'A',
      last_name: 'B',
      avatar_url: null,
      created_at: new Date().toISOString(),
    };
    const mockFetch = vi.fn().mockResolvedValue(new Response(JSON.stringify(user), { status: 200 }));
    vi.stubGlobal('fetch', mockFetch);

    const result = await syncUser('A', 'B');

    expect(result).toEqual(user);
    const [, init] = mockFetch.mock.calls[0];
    expect(init.headers.Authorization).toBe('Bearer fake-id-token');
  });
});

describe('signOut', () => {
  it('clears the stored token', () => {
    localStorage.setItem(TOKEN_KEY, 'fake-id-token');
    signOut();
    expect(localStorage.getItem(TOKEN_KEY)).toBeNull();
  });
});
