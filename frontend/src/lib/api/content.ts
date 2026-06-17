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

export async function getContent(_id: number): Promise<ContentDetailResponse> {
  throw new Error('not implemented');
}

export async function getAudioUrl(_id: number): Promise<string> {
  throw new Error('not implemented');
}
