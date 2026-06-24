import { afterEach, describe, expect, it, vi } from 'vitest';
import { apiFetch, ApiError } from './client';

describe('apiFetch', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('returns parsed JSON on a successful response', async () => {
    const mockFetch = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ hello: 'world' }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      })
    );
    vi.stubGlobal('fetch', mockFetch);

    const result = await apiFetch<{ hello: string }>('/topics/');

    expect(result).toEqual({ hello: 'world' });
    expect(mockFetch).toHaveBeenCalledWith(expect.stringContaining('/topics/'), expect.any(Object));
  });

  it('throws ApiError with the response status on a non-2xx response', async () => {
    const mockFetch = vi
      .fn()
      .mockResolvedValue(new Response(JSON.stringify({ detail: 'Not found' }), { status: 404 }));
    vi.stubGlobal('fetch', mockFetch);

    await expect(apiFetch('/albums/999')).rejects.toMatchObject({
      status: 404,
      message: expect.stringContaining('404'),
    });
  });

  it('ApiError is an instance of Error with the correct name', () => {
    const err = new ApiError(500, 'boom');
    expect(err).toBeInstanceOf(Error);
    expect(err.name).toBe('ApiError');
    expect(err.status).toBe(500);
  });
});
