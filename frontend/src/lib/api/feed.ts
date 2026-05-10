import { apiFetch } from './client';
import type { ContentListResponse } from './types';

export async function getFeed(): Promise<ContentListResponse[]> {
  return apiFetch<ContentListResponse[]>('/feed');
}
