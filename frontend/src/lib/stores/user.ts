import { writable } from 'svelte/store';
import type { TopicResponse, UserResponse } from '$lib/api/types';

/** Authenticated user. null when logged out. Set after /auth/sync succeeds. */
export const currentUser = writable<UserResponse | null>(null);

/** The user's chosen topic interests. Set after onboarding or on app load. */
export const userTopics = writable<TopicResponse[]>([]);
