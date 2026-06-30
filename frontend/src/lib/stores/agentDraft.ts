import { writable } from 'svelte/store';

export const agentDraft = writable<string | null>(null);
