import { describe, it, expect } from 'vitest';
import { getPagePalette, getShadowPalette } from './gradient';

describe('getPagePalette', () => {
  it('returns the same palette for the same pathname every time', () => {
    expect(getPagePalette('/learn')).toEqual(getPagePalette('/learn'));
  });

  it('returns a different palette for a different pathname', () => {
    expect(getPagePalette('/learn')).not.toEqual(getPagePalette('/topics'));
  });

  it('returns three distinct hsl colours', () => {
    const [a, b, c] = getPagePalette('/settings');
    expect(new Set([a, b, c]).size).toBe(3);
  });

  it('keeps every colour within the fixed pastel saturation/lightness band', () => {
    const palette = getPagePalette('/');
    for (const colour of palette) {
      expect(colour).toMatch(/^hsl\(\d+, 60%, 87%\)$/);
    }
  });
});

describe('getShadowPalette', () => {
  it('returns the same palette for the same pathname every time', () => {
    expect(getShadowPalette('/learn')).toEqual(getShadowPalette('/learn'));
  });

  it('returns three distinct colours with decreasing alpha', () => {
    const [a, b, c] = getShadowPalette('/settings');
    expect(new Set([a, b, c]).size).toBe(3);
    expect(a).toMatch(/0\.35\)$/);
    expect(b).toMatch(/0\.3\)$/);
    expect(c).toMatch(/0\.25\)$/);
  });

  it('uses a darker, more saturated band than the pastel backdrop palette', () => {
    const palette = getShadowPalette('/');
    for (const colour of palette) {
      expect(colour).toMatch(/^hsl\(\d+ 75% 60% \/ 0\.\d+\)$/);
    }
  });

  it('shares the same hue derivation as getPagePalette (same base hue)', () => {
    const [pageA] = getPagePalette('/library');
    const [shadowA] = getShadowPalette('/library');
    const pageHue = pageA.match(/^hsl\((\d+),/)?.[1];
    const shadowHue = shadowA.match(/^hsl\((\d+) /)?.[1];
    expect(shadowHue).toBe(pageHue);
  });
});
