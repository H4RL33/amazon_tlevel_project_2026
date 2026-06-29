import { apiFetch } from '$lib/api/client';

export interface LibraryAlbum {
  id: number;
  t_level_id: number;
  topic_id: number;
  title: string;
  description: string;
  icon: string;
}

export interface LibrarySnippet {
  id: number;
  title: string;
  content_type: 'article' | 'audio' | 'video';
  media_url: string | null;
  topic_id: number;
  t_level_id: number | null;
}

export interface LibraryResponse {
  enrolled_albums: LibraryAlbum[];
  saved_snippets: LibrarySnippet[];
}

export interface ContentSearchResult {
  content_id: number;
  title: string;
  content_type: 'article' | 'audio' | 'video';
  album_title: string | null;
  similarity_score: number;
  is_saved: boolean;
}

export interface MentorSource {
  content_id: number;
  title: string;
}

export interface MentorResponse {
  reply: string;
  sources: MentorSource[];
}

export async function getLibrary(): Promise<LibraryResponse> {
  return apiFetch<LibraryResponse>('/library/');
}

export async function searchLibrary(query: string): Promise<ContentSearchResult[]> {
  return apiFetch<ContentSearchResult[]>(`/library/search?q=${encodeURIComponent(query)}`);
}

export async function mentorQuery(message: string): Promise<MentorResponse> {
  return apiFetch<MentorResponse>('/library/mentor', {
    method: 'POST',
    body: JSON.stringify({ message }),
  });
}

export async function saveSnippet(contentId: number): Promise<void> {
  await apiFetch<void>(`/snippets/${contentId}/save`, { method: 'POST' });
}

export async function unsaveSnippet(contentId: number): Promise<void> {
  await apiFetch<void>(`/snippets/${contentId}/save`, { method: 'DELETE' });
}
