import type { TLevelResponse, TopicDetailResponse, TopicResponse } from './types';

export async function listTopics(): Promise<TopicResponse[]> {
  throw new Error('not implemented');
}

export async function getTopic(_slug: string): Promise<TopicDetailResponse> {
  throw new Error('not implemented');
}

export async function getTLevel(_slug: string, _tLevelId: number): Promise<TLevelResponse> {
  throw new Error('not implemented');
}

export async function getUserTopics(): Promise<TopicResponse[]> {
  throw new Error('not implemented');
}
