import { apiFetch } from './client';
import type { UserResponse } from './types';

export interface AvatarUploadUrlResponse {
  upload_url: string;
  key: string;
}

export interface UserStatsResponse {
  total_xp: number;
  level: number;
  snippets_completed: number;
  albums_completed: number;
}

export async function getMe(): Promise<UserResponse> {
  return apiFetch<UserResponse>('/users/me');
}

export async function getStats(): Promise<UserStatsResponse> {
  return apiFetch<UserStatsResponse>('/users/me/stats');
}

export async function requestAvatarUploadUrl(
  contentType: string
): Promise<AvatarUploadUrlResponse> {
  return apiFetch<AvatarUploadUrlResponse>('/users/me/avatar-upload-url', {
    method: 'POST',
    body: JSON.stringify({ content_type: contentType }),
  });
}

export async function updateAvatar(avatarS3Key: string): Promise<UserResponse> {
  return apiFetch<UserResponse>('/users/me/avatar', {
    method: 'PATCH',
    body: JSON.stringify({ avatar_s3_key: avatarS3Key }),
  });
}

export async function updateUsername(username: string): Promise<UserResponse> {
  return apiFetch<UserResponse>('/users/me/profile', {
    method: 'PATCH',
    body: JSON.stringify({ username }),
  });
}
