import { apiFetch } from './client';
import type { ContentDetailResponse, ContentListResponse, ContentType } from './types';

export interface ContentFilters {
  topic?: string;
  t_level_id?: number;
  content_type?: ContentType;
  tag?: string;
}

export async function listContent(_filters: ContentFilters = {}): Promise<ContentListResponse[]> {
  throw new Error('not implemented');
}

export async function getContent(id: number): Promise<ContentDetailResponse> {
  return apiFetch<ContentDetailResponse>(`/content/${id}`);
}

export async function getAudioUrl(_id: number): Promise<string> {
  throw new Error('not implemented');
}
