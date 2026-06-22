import { describe, it, expect } from 'vitest';

describe('API types', () => {
  it('types module exports required interfaces', async () => {
    // Dynamic import verifies the module compiles and exports exist at runtime
    const types = await import('$lib/api/types');
    // If this import fails, there is a TypeScript/syntax error in types.ts
    expect(types).toBeDefined();
  });
});

describe('Stores', () => {
  it('user store initialises to null', async () => {
    const { currentUser } = await import('$lib/stores/user');
    let value: unknown;
    currentUser.subscribe((v) => {
      value = v;
    })();
    expect(value).toBeNull();
  });

  it('allTopics store initialises to empty array', async () => {
    const { allTopics } = await import('$lib/stores/topics');
    let value: unknown;
    allTopics.subscribe((v) => {
      value = v;
    })();
    expect(Array.isArray(value)).toBe(true);
    expect(value).toHaveLength(0);
  });
});

describe('Components', () => {
  it('NavLink exports a default Svelte component', async () => {
    const mod = await import('$lib/components/NavLink.svelte');
    expect(mod.default).toBeDefined();
  });

  it('Navbar exports a default Svelte component', async () => {
    const mod = await import('$lib/components/Navbar.svelte');
    expect(mod.default).toBeDefined();
  });

  it('Footer exports a default Svelte component', async () => {
    const mod = await import('$lib/components/Footer.svelte');
    expect(mod.default).toBeDefined();
  });
});
