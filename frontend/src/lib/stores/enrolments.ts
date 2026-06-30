import { writable } from 'svelte/store';

export const enrolledAlbumIds = writable<Set<number>>(new Set());
