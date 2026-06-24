import { describe, it, expect } from 'vitest';

/** WCAG 2.x relative luminance + contrast ratio, no dependency. */
function hexToRgb(hex: string): [number, number, number] {
  const value = hex.replace('#', '');
  return [
    parseInt(value.slice(0, 2), 16),
    parseInt(value.slice(2, 4), 16),
    parseInt(value.slice(4, 6), 16),
  ];
}

function channelLuminance(value: number): number {
  const srgb = value / 255;
  return srgb <= 0.03928 ? srgb / 12.92 : Math.pow((srgb + 0.055) / 1.055, 2.4);
}

function relativeLuminance(hex: string): number {
  const [r, g, b] = hexToRgb(hex).map(channelLuminance);
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}

function contrastRatio(hexA: string, hexB: string): number {
  const lighter = Math.max(relativeLuminance(hexA), relativeLuminance(hexB));
  const darker = Math.min(relativeLuminance(hexA), relativeLuminance(hexB));
  return (lighter + 0.05) / (darker + 0.05);
}

const WHITE = '#ffffff';
const AA_NORMAL_TEXT = 4.5;

describe('floating-card redesign text contrast on white panels', () => {
  it('primary text (#232f3e) meets WCAG AA on white', () => {
    expect(contrastRatio('#232f3e', WHITE)).toBeGreaterThanOrEqual(AA_NORMAL_TEXT);
  });

  it('muted/secondary text (#5a6472) meets WCAG AA on white', () => {
    expect(contrastRatio('#5a6472', WHITE)).toBeGreaterThanOrEqual(AA_NORMAL_TEXT);
  });

  it("Footer's heading colour (#a35200) meets WCAG AA on white", () => {
    expect(contrastRatio('#a35200', WHITE)).toBeGreaterThanOrEqual(AA_NORMAL_TEXT);
  });
});
