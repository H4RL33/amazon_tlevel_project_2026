import { afterEach, describe, expect, it, vi } from 'vitest';
import { getMe, requestAvatarUploadUrl, updateAvatar } from './users';
import type { UserResponse } from './types';

const user: UserResponse = {
  id: 1,
  cognito_sub: 'sub-1',
  email: 'a@example.com',
  first_name: 'A',
  last_name: 'B',
  avatar_url: null,
  created_at: new Date().toISOString(),
};

describe('getMe', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('calls GET /users/me', async () => {
    const mockFetch = vi.fn().mockResolvedValue(new Response(JSON.stringify(user), { status: 200 }));
    vi.stubGlobal('fetch', mockFetch);

    const result = await getMe();

    expect(result).toEqual(user);
    expect(mockFetch).toHaveBeenCalledWith(expect.stringContaining('/users/me'), expect.any(Object));
  });
});

describe('requestAvatarUploadUrl', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('POSTs the content type and returns the upload url and key', async () => {
    const body = { upload_url: 'https://example.com/put', key: 'avatars/1/x.png' };
    const mockFetch = vi.fn().mockResolvedValue(new Response(JSON.stringify(body), { status: 200 }));
    vi.stubGlobal('fetch', mockFetch);

    const result = await requestAvatarUploadUrl('image/png');

    expect(result).toEqual(body);
    const [, init] = mockFetch.mock.calls[0];
    expect(init.body).toContain('image/png');
  });
});

describe('updateAvatar', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('PATCHes the avatar_s3_key and returns the updated user', async () => {
    const mockFetch = vi.fn().mockResolvedValue(new Response(JSON.stringify(user), { status: 200 }));
    vi.stubGlobal('fetch', mockFetch);

    const result = await updateAvatar('avatars/1/x.png');

    expect(result).toEqual(user);
    const [, init] = mockFetch.mock.calls[0];
    expect(init.method).toBe('PATCH');
    expect(init.body).toContain('avatars/1/x.png');
  });
});
