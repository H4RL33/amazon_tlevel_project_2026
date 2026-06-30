import { afterEach, describe, expect, it, vi } from 'vitest';
import { getAlbumDetail, listAlbums } from './albums';
import type { AlbumDetailResponse, AlbumListResponse } from './types';

describe('listAlbums', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('calls GET /albums/ and returns the parsed list', async () => {
    const albums: AlbumListResponse[] = [
      {
        id: 1,
        t_level_id: 1,
        title: 'Cloud Computing Fundamentals',
        description: '...',
        icon: 'cloud',
      },
    ];
    const mockFetch = vi
      .fn()
      .mockResolvedValue(new Response(JSON.stringify(albums), { status: 200 }));
    vi.stubGlobal('fetch', mockFetch);

    const result = await listAlbums();

    expect(result).toEqual(albums);
    expect(mockFetch).toHaveBeenCalledWith(expect.stringContaining('/albums/'), expect.any(Object));
  });
});

describe('getAlbumDetail', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('calls GET /albums/{id} and returns the parsed detail', async () => {
    const album: AlbumDetailResponse = {
      id: 1,
      t_level_id: 1,
      title: 'Cloud Computing Fundamentals',
      description: '...',
      icon: 'cloud',
      sides: [],
    };
    const mockFetch = vi
      .fn()
      .mockResolvedValue(new Response(JSON.stringify(album), { status: 200 }));
    vi.stubGlobal('fetch', mockFetch);

    const result = await getAlbumDetail(1);

    expect(result).toEqual(album);
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining('/albums/1'),
      expect.any(Object)
    );
  });
});
