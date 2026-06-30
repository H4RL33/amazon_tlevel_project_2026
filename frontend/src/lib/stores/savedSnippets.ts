import { writable } from 'svelte/store';

export const savedSnippetIds = writable<Set<number>>(new Set());
