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

describe('NavBarAvatar', () => {
  it('exports a default Svelte component', async () => {
    const mod = await import('$lib/components/NavBarAvatar.svelte');
    expect(mod.default).toBeDefined();
  });
});

describe('Navbar', () => {
  it('exports a default Svelte component', async () => {
    const mod = await import('$lib/components/Navbar.svelte');
    expect(mod.default).toBeDefined();
  });
});

describe('HelpPanel', () => {
  it('exports a default Svelte component', async () => {
    const mod = await import('$lib/components/HelpPanel.svelte');
    expect(mod.default).toBeDefined();
  });
});

describe('/login page', () => {
  it('exports a default Svelte component', async () => {
    const mod = await import('../routes/login/+page.svelte');
    expect(mod.default).toBeDefined();
  });
});

describe('AlbumCard', () => {
  it('exports a default Svelte component', async () => {
    const mod = await import('$lib/components/AlbumCard.svelte');
    expect(mod.default).toBeDefined();
  });
});

describe('AlbumGrid', () => {
  it('exports a default Svelte component', async () => {
    const mod = await import('$lib/components/AlbumGrid.svelte');
    expect(mod.default).toBeDefined();
  });
});

describe('SideHeader', () => {
  it('exports a default Svelte component', async () => {
    const mod = await import('$lib/components/SideHeader.svelte');
    expect(mod.default).toBeDefined();
  });
});

describe('AlbumSidebar', () => {
  it('exports a default Svelte component', async () => {
    const mod = await import('$lib/components/AlbumSidebar.svelte');
    expect(mod.default).toBeDefined();
  });
});
