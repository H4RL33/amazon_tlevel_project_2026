import { describe, it, expect } from 'vitest';
import { getPagePalette } from './gradient';

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
