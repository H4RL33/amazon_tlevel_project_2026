import { apiFetch } from './client';
import type { ContentDetailResponse, ContentListResponse } from './types';

export interface ContentFilters {
  topic?: string;
  t_level_id?: number;
  content_type?: 'article' | 'audio' | 'video';
  tag?: string;
}

export async function listContent(filters: ContentFilters = {}): Promise<ContentListResponse[]> {
  const params = new URLSearchParams();
  if (filters.topic) params.set('topic', filters.topic);
  if (filters.t_level_id) params.set('t_level_id', String(filters.t_level_id));
  if (filters.content_type) params.set('content_type', filters.content_type);
  if (filters.tag) params.set('tag', filters.tag);
  const qs = params.toString();
  return apiFetch<ContentListResponse[]>(`/content/${qs ? `?${qs}` : ''}`);
}

export async function getContent(id: number): Promise<ContentDetailResponse> {
  return apiFetch<ContentDetailResponse>(`/content/${id}`);
}

export async function getAudioUrl(id: number): Promise<string> {
  const result = await apiFetch<{ url: string }>(`/content/${id}/audio-url`);
  return result.url;
}
