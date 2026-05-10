import { writable } from 'svelte/store';
import type { ProgressResponse } from '$lib/api/types';

/** User's in-progress content items (progress_pct < 100). Powers the "Continue Reading" section. */
export const continueReading = writable<ProgressResponse[]>([]);
