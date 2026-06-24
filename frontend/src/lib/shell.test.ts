import { existsSync } from 'node:fs';
import { describe, it, expect } from 'vitest';

describe('AppShell removal', () => {
  it('AppShell.svelte no longer exists', () => {
    expect(existsSync('src/lib/components/AppShell.svelte')).toBe(false);
  });
});

describe('NavSidebar', () => {
  it('exports a default Svelte component', async () => {
    const mod = await import('$lib/components/NavSidebar.svelte');
    expect(mod.default).toBeDefined();
  });
});
