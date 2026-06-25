import { apiFetch } from './client';
import type { AlbumDetailResponse, AlbumListResponse } from './types';

export async function listAlbums(): Promise<AlbumListResponse[]> {
  return apiFetch<AlbumListResponse[]>('/albums/');
}

export async function getAlbumDetail(id: number): Promise<AlbumDetailResponse> {
  return apiFetch<AlbumDetailResponse>(`/albums/${id}`);
}
