/**
 * Deterministic per-route pastel palette for the page backdrop. Same pathname always
 * yields the same three colours (stable across visits/refreshes); different pathnames
 * yield visually distinct palettes. Saturation/lightness are fixed so every page's
 * backdrop reads as the same soft "AWS console" pastel mood.
 */

const SATURATION = 60;
const LIGHTNESS = 87;
const HUE_OFFSET_B = 110;
const HUE_OFFSET_C = 220;

function hashString(input: string): number {
  let hash = 0;
  for (let i = 0; i < input.length; i++) {
    hash = (hash << 5) - hash + input.charCodeAt(i);
    hash |= 0;
  }
  return Math.abs(hash);
}

function hsl(hue: number): string {
  return `hsl(${hue}, ${SATURATION}%, ${LIGHTNESS}%)`;
}

export function getPagePalette(pathname: string): [string, string, string] {
  const baseHue = hashString(pathname) % 360;
  const hueB = (baseHue + HUE_OFFSET_B) % 360;
  const hueC = (baseHue + HUE_OFFSET_C) % 360;
  return [hsl(baseHue), hsl(hueB), hsl(hueC)];
}
