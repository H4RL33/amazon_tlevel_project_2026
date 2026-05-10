import { writable } from 'svelte/store';
import type { TopicResponse } from '$lib/api/types';

/** All 5 platform topics. Loaded once on first authenticated page load. */
export const allTopics = writable<TopicResponse[]>([]);
