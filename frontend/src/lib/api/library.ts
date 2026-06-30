import { apiFetch } from './client';
import type { AlbumListResponse, ContentListResponse } from './types';

export interface LibraryResponse {
  enrolled_albums: AlbumListResponse[];
  saved_snippets: ContentListResponse[];
}

export interface ContentSearchResult {
  id: number;
  title: string;
  body: string;
  content_type: string;
}

export interface MentorResponse {
  answer: string;
  sources: ContentSearchResult[];
}

export async function getLibrary(): Promise<LibraryResponse> {
  return apiFetch<LibraryResponse>('/library/');
}

export async function searchLibrary(query: string): Promise<ContentSearchResult[]> {
  return apiFetch<ContentSearchResult[]>(`/library/search?q=${encodeURIComponent(query)}`);
}

export async function mentorQuery(query: string): Promise<MentorResponse> {
  return apiFetch<MentorResponse>('/library/mentor', {
    method: 'POST',
    body: JSON.stringify({ query }),
  });
}

export async function saveSnippet(contentId: number): Promise<void> {
  await apiFetch<void>(`/library/snippets/${contentId}`, { method: 'POST' });
}

export async function unsaveSnippet(contentId: number): Promise<void> {
  await apiFetch<void>(`/library/snippets/${contentId}`, { method: 'DELETE' });
}
