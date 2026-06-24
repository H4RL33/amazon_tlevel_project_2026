import { existsSync } from 'node:fs';
import { describe, it, expect } from 'vitest';

describe('AppShell removal', () => {
	it('AppShell.svelte no longer exists', () => {
		expect(existsSync('src/lib/components/AppShell.svelte')).toBe(false);
	});
});
