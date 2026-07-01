import { redirect } from '@sveltejs/kit';
import type { PageLoad } from './$types';
import { getLibrary } from '$lib/api/library';
import { listChatSessions, getChatSession } from '$lib/api/chat';
import { ApiError } from '$lib/api/client';

export const load: PageLoad = async ({ url }) => {
  try {
    const [library, sessions] = await Promise.all([getLibrary(), listChatSessions()]);

    const sessionParam = url.searchParams.get('session');
    const draft = url.searchParams.get('draft') ?? '';

    let activeSessionId: number | null = sessionParam ? Number(sessionParam) : null;
    if (activeSessionId === null && sessions.length > 0) {
      activeSessionId = sessions[0].id;
    }

    const activeSession = activeSessionId !== null ? await getChatSession(activeSessionId) : null;

    return { library, sessions, activeSession, draft };
  } catch (err) {
    if (err instanceof ApiError && err.status === 401) {
      throw redirect(302, `/login?next=${encodeURIComponent(url.pathname)}`);
    }
    throw err;
  }
};
