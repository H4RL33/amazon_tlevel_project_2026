import { apiFetch } from './client';

export async function saveSnippet(contentId: number): Promise<void> {
  await apiFetch<void>(`/library/snippets/${contentId}`, { method: 'POST' });
}

export async function unsaveSnippet(contentId: number): Promise<void> {
  await apiFetch<void>(`/library/snippets/${contentId}`, { method: 'DELETE' });
}
