import { apiFetch } from './client';
import type { ProgressResponse } from './types';

export async function getProgress(): Promise<ProgressResponse[]> {
  return apiFetch<ProgressResponse[]>('/progress');
}

export async function updateProgress(contentId: number, progressPct: number): Promise<void> {
  return apiFetch<void>(`/progress/${contentId}`, {
    method: 'POST',
    body: JSON.stringify({ progress_pct: progressPct }),
  });
}
