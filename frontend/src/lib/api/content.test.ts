import { afterEach, describe, expect, it, vi } from 'vitest';
import { getContent } from './content';
import type { ContentDetailResponse } from './types';

describe('getContent', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('calls GET /content/{id} and returns the parsed detail', async () => {
    const content: ContentDetailResponse = {
      id: 1,
      title: 'What is Cloud Computing?',
      content_type: 'article',
      topic_id: 1,
      t_level_id: 1,
      tags: [],
      created_at: '2026-06-25T00:00:00Z',
      body: 'Cloud computing means renting computing power...',
      media_url: null,
    };
    const mockFetch = vi
      .fn()
      .mockResolvedValue(new Response(JSON.stringify(content), { status: 200 }));
    vi.stubGlobal('fetch', mockFetch);

    const result = await getContent(1);

    expect(result).toEqual(content);
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining('/content/1'),
      expect.any(Object)
    );
  });
});
