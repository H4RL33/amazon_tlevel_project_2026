import { apiFetch, TOKEN_KEY, ApiError } from './client';

export interface ChatSessionSummary {
  id: number;
  title: string;
  updated_at: string;
}

export interface ChatMessageSource {
  content_id: number;
  title: string;
}

export interface ChatMessageRecord {
  id: number;
  role: 'user' | 'mentor';
  text: string;
  sources: ChatMessageSource[] | null;
  created_at: string;
}

export interface ChatSessionDetail {
  id: number;
  title: string;
  messages: ChatMessageRecord[];
}

export async function listChatSessions(): Promise<ChatSessionSummary[]> {
  return apiFetch<ChatSessionSummary[]>('/library/chats');
}

export async function createChatSession(): Promise<ChatSessionSummary> {
  return apiFetch<ChatSessionSummary>('/library/chats', { method: 'POST' });
}

export async function getChatSession(sessionId: number): Promise<ChatSessionDetail> {
  return apiFetch<ChatSessionDetail>(`/library/chats/${sessionId}`);
}

export interface SendChatMessageResult {
  messageId: number;
}

/**
 * Streams a mentor reply via SSE. Deliberately does NOT use the native
 * EventSource API — it can't send an Authorization header, and every other
 * authenticated call in this app relies on one. fetch() + a ReadableStream
 * reader gets the same auth story as apiFetch() while still streaming.
 */
export async function sendChatMessage(
  sessionId: number,
  message: string,
  onDelta: (text: string) => void
): Promise<SendChatMessageResult> {
  const baseUrl = import.meta.env.VITE_API_BASE_URL ?? '';
  const token = localStorage.getItem(TOKEN_KEY);
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  if (token) headers.Authorization = `Bearer ${token}`;

  const response = await fetch(`${baseUrl}/library/chats/${sessionId}/messages`, {
    method: 'POST',
    headers,
    body: JSON.stringify({ message }),
  });

  if (!response.ok || !response.body) {
    throw new ApiError(response.status, `Streaming request failed with status ${response.status}`);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  let messageId: number | null = null;

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    // SSE frames are separated by a blank line; a chunk boundary from the
    // network doesn't necessarily land on a frame boundary, so buffer
    // partial data and only process complete "data: ...\n\n" frames.
    let boundary = buffer.indexOf('\n\n');
    while (boundary !== -1) {
      const frame = buffer.slice(0, boundary);
      buffer = buffer.slice(boundary + 2);
      if (frame.startsWith('data: ')) {
        const payload = JSON.parse(frame.slice('data: '.length));
        if (payload.done) {
          messageId = payload.message_id;
        } else if (typeof payload.delta === 'string') {
          onDelta(payload.delta);
        }
      }
      boundary = buffer.indexOf('\n\n');
    }
  }

  return { messageId: messageId ?? -1 };
}
