import { apiFetch } from './client';
import type { AlbumDetailResponse, AlbumListResponse } from './types';

export async function listAlbums(): Promise<AlbumListResponse[]> {
  return apiFetch<AlbumListResponse[]>('/albums/');
}

export async function getAlbumDetail(id: number): Promise<AlbumDetailResponse> {
  return apiFetch<AlbumDetailResponse>(`/albums/${id}`);
}

export async function enrolAlbum(albumId: number): Promise<void> {
  await apiFetch<void>(`/albums/${albumId}/enrol`, { method: 'POST' });
}

export async function unenrolAlbum(albumId: number): Promise<void> {
  await apiFetch<void>(`/albums/${albumId}/enrol`, { method: 'DELETE' });
}
