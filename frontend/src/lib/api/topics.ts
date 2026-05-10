import { apiFetch } from './client';
import type { TLevelResponse, TopicDetailResponse, TopicResponse } from './types';

export async function listTopics(): Promise<TopicResponse[]> {
  return apiFetch<TopicResponse[]>('/topics/');
}

export async function getTopic(slug: string): Promise<TopicDetailResponse> {
  return apiFetch<TopicDetailResponse>(`/topics/${slug}`);
}

export async function getTLevel(slug: string, tLevelId: number): Promise<TLevelResponse> {
  return apiFetch<TLevelResponse>(`/topics/${slug}/t-levels/${tLevelId}`);
}
