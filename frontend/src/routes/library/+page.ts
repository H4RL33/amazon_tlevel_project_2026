import { redirect } from '@sveltejs/kit';
import type { PageLoad } from './$types';
import { getLibrary } from '$lib/api/library';
import { ApiError } from '$lib/api/client';

export const load: PageLoad = async ({ url }) => {
  try {
    const library = await getLibrary();
    const q = url.searchParams.get('q') ?? '';
    return { library, initialQuery: q };
  } catch (err) {
    if (err instanceof ApiError && err.status === 401) {
      throw redirect(302, `/login?next=${encodeURIComponent(url.pathname)}`);
    }
    throw err;
  }
};
