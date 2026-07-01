import { describe, it, expect, vi, beforeEach } from 'vitest';
import { TOKEN_KEY, ApiError } from './client';

describe('chat api client', () => {
  beforeEach(() => {
    localStorage.clear();
    localStorage.setItem(TOKEN_KEY, 'test-token');
    vi.restoreAllMocks();
  });

  it('listChatSessions calls GET /library/chats and returns parsed JSON', async () => {
    const mockSessions = [{ id: 1, title: 'Hello', updated_at: '2026-07-01T00:00:00Z' }];
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => mockSessions,
      })
    );

    const { listChatSessions } = await import('./chat');
    const result = await listChatSessions();

    expect(result).toEqual(mockSessions);
    const [url, init] = (fetch as ReturnType<typeof vi.fn>).mock.calls[0];
    expect(url).toContain('/library/chats');
    expect((init.headers as Record<string, string>).Authorization).toBe('Bearer test-token');
  });

  it('createChatSession POSTs to /library/chats and returns the new session', async () => {
    const mockSession = { id: 2, title: 'New chat', updated_at: '2026-07-01T00:00:00Z' };
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => mockSession,
      })
    );

    const { createChatSession } = await import('./chat');
    const result = await createChatSession();

    expect(result).toEqual(mockSession);
    const [, init] = (fetch as ReturnType<typeof vi.fn>).mock.calls[0];
    expect(init.method).toBe('POST');
  });

  it('getChatSession fetches full message history for one session', async () => {
    const mockDetail = {
      id: 3,
      title: 'Hi',
      messages: [{ id: 1, role: 'user', text: 'Hi', sources: null, created_at: '2026-07-01T00:00:00Z' }],
    };
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => mockDetail,
      })
    );

    const { getChatSession } = await import('./chat');
    const result = await getChatSession(3);

    expect(result).toEqual(mockDetail);
    const [url] = (fetch as ReturnType<typeof vi.fn>).mock.calls[0];
    expect(url).toContain('/library/chats/3');
  });

  it('sendChatMessage streams SSE chunks and calls onDelta for each one', async () => {
    const encoder = new TextEncoder();
    const frames = [
      'data: {"delta":"Hello "}\n\n',
      'data: {"delta":"world."}\n\n',
      'data: {"done":true,"message_id":42}\n\n',
    ];
    let frameIndex = 0;
    const reader = {
      read: async () => {
        if (frameIndex >= frames.length) return { done: true, value: undefined };
        const value = encoder.encode(frames[frameIndex]);
        frameIndex++;
        return { done: false, value };
      },
    };
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: true,
        body: { getReader: () => reader },
      })
    );

    const { sendChatMessage } = await import('./chat');
    const deltas: string[] = [];
    const result = await sendChatMessage(3, 'What is networking?', (delta) => deltas.push(delta));

    expect(deltas).toEqual(['Hello ', 'world.']);
    expect(result).toEqual({ messageId: 42 });
    const [url, init] = (fetch as ReturnType<typeof vi.fn>).mock.calls[0];
    expect(url).toContain('/library/chats/3/messages');
    expect(JSON.parse(init.body as string)).toEqual({ message: 'What is networking?' });
  });

  it('sendChatMessage throws ApiError on a non-ok response', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: false,
        status: 500,
      })
    );

    const { sendChatMessage } = await import('./chat');
    await expect(sendChatMessage(3, 'hi', () => {})).rejects.toBeInstanceOf(ApiError);
  });
});
