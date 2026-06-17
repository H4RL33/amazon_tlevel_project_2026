import type { ProgressResponse } from './types';

export async function getProgress(): Promise<ProgressResponse[]> {
  throw new Error('not implemented');
}

export async function updateProgress(_contentId: number, _progressPct: number): Promise<void> {
  throw new Error('not implemented');
}
