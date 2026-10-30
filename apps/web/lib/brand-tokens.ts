/**
 * Brand tokens for the social stories — a port of the part of
 * `apps/worker/src/worker/themes.py` the stories use, so a story and the
 * report it shares derive the same colours from one brand value.
 *
 * THE RULE, the same on every surface: the brand colour is a FILL and never
 * moves; text on the fill is `onPrimary`; brand as text on white or the tint is
 * `primaryInk`; the panel is `tint`; brand on the dark footer is
 * `primaryOnDark`. The raw brand as text fails on light brands (amber
 * `#F59E0B` on white is 2.15:1), which is why these exist.
 *
 * KEPT IN STEP WITH PYTHON BY A FIXTURE, not by care:
 * `__tests__/fixtures/brand-tokens.json` is generated from `derive_theme` and
 * `__tests__/BrandTokens.test.ts` asserts this module reproduces every value;
 * `tests/test_brand_tokens_fixture.py` asserts the fixture still matches Python.
 * Python's `round()` rounds half to even and `Math.round` does not, so the
 * port rounds half to even too — a one-step difference would be invisible
 * until a brand landed exactly on .5.
 */

const WHITE = "#ffffff";
const NEAR_BLACK = "#14151a";
// The third candidate, used only where neither white nor near-black clears
// AA on the fill (D-098, D-210) — `themes.text_on` in Python.
const BLACK = "#000000";
const DARK_SURFACE = "#0f172a";
const AA_NORMAL = 4.5;
const STEP = 0.94;
const MAX_STEPS = 64;
const TINT_ALPHA = 0.06;

export type BrandTokens = {
  primary: string;
  primaryInk: string;
  onPrimary: string;
  tint: string;
  primaryOnDark: string;
};

export function normalizeHex(value: string): string {
  const m = /^#?([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$/.exec(String(value ?? "").trim());
  if (!m) throw new Error(`not a hex colour: ${value}`);
  let h = m[1].toLowerCase();
  if (h.length === 3) h = h.split("").map((c) => c + c).join("");
  return "#" + h;
}

function toRgb(value: string): [number, number, number] {
  const h = normalizeHex(value).slice(1);
  return [parseInt(h.slice(0, 2), 16), parseInt(h.slice(2, 4), 16), parseInt(h.slice(4, 6), 16)];
}

/** Python's round(): half to even. */
function pyRound(x: number): number {
  const f = Math.floor(x);
  const d = x - f;
  if (Math.abs(d - 0.5) < 1e-9) return f % 2 === 0 ? f : f + 1;
  return Math.round(x);
}

function toHex(r: number, g: number, b: number): string {
  const c = (v: number) => Math.max(0, Math.min(255, Math.trunc(pyRound(v))));
  return "#" + [r, g, b].map((v) => c(v).toString(16).padStart(2, "0")).join("");
}

function linearize(ch: number): number {
  const c = ch / 255;
  return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
}

export function relativeLuminance(value: string): number {
  const [r, g, b] = toRgb(value);
  return 0.2126 * linearize(r) + 0.7152 * linearize(g) + 0.0722 * linearize(b);
}

export function contrast(a: string, b: string): number {
  const la = relativeLuminance(a);
  const lb = relativeLuminance(b);
  return (Math.max(la, lb) + 0.05) / (Math.min(la, lb) + 0.05);
}

function scale(value: string, factor: number): string {
  const [r, g, b] = toRgb(value);
  return toHex(r * factor, g * factor, b * factor);
}

function flattenOverWhite(value: string, alpha: number): string {
  const [r, g, b] = toRgb(value);
  const mix = (c: number) => c * alpha + 255 * (1 - alpha);
  return toHex(mix(r), mix(g), mix(b));
}

// colorsys.rgb_to_hsv / hsv_to_rgb, as Python implements them.
function rgbToHsv(r: number, g: number, b: number): [number, number, number] {
  const maxc = Math.max(r, g, b);
  const minc = Math.min(r, g, b);
  const v = maxc;
  if (minc === maxc) return [0, 0, v];
  const s = (maxc - minc) / maxc;
  const rc = (maxc - r) / (maxc - minc);
  const gc = (maxc - g) / (maxc - minc);
  const bc = (maxc - b) / (maxc - minc);
  let h: number;
  if (r === maxc) h = bc - gc;
  else if (g === maxc) h = 2 + rc - bc;
  else h = 4 + gc - rc;
  h = ((h / 6) % 1 + 1) % 1;
  return [h, s, v];
}

function hsvToRgb(h: number, s: number, v: number): [number, number, number] {
  if (s === 0) return [v, v, v];
  let i = Math.trunc(h * 6);
  const f = h * 6 - i;
  const p = v * (1 - s);
  const q = v * (1 - s * f);
  const t = v * (1 - s * (1 - f));
  i = i % 6;
  if (i === 0) return [v, t, p];
  if (i === 1) return [q, v, p];
  if (i === 2) return [p, v, t];
  if (i === 3) return [p, q, v];
  if (i === 4) return [t, p, v];
  return [v, p, q];
}

function brighten(value: string): string {
  const [r, g, b] = toRgb(value).map((c) => c / 255) as [number, number, number];
  let [h, s, v] = rgbToHsv(r, g, b);
  if (v >= 1) s = Math.max(0, s - 0.04);
  else v = Math.min(1, v + 0.04);
  const [rr, gg, bb] = hsvToRgb(h, s, v);
  return toHex(rr * 255, gg * 255, bb * 255);
}

function onDark(value: string): string {
  let current = normalizeHex(value);
  for (let i = 0; i < MAX_STEPS; i++) {
    if (contrast(current, DARK_SURFACE) >= AA_NORMAL) return current;
    const stepped = brighten(current);
    if (stepped === current) break;
    current = stepped;
  }
  return WHITE;
}

function ink(value: string): string {
  let current = normalizeHex(value);
  const tint = flattenOverWhite(current, TINT_ALPHA);
  for (let i = 0; i < MAX_STEPS; i++) {
    if (contrast(current, WHITE) >= AA_NORMAL && contrast(current, tint) >= AA_NORMAL) return current;
    const stepped = scale(current, STEP);
    if (stepped === current) break;
    current = stepped;
  }
  return NEAR_BLACK;
}

/** White or near-black, whichever scores higher; pure black only when neither
 * clears AA and black does better. The fill never moves. */
function textOn(fill: string): string {
  const best = contrast(WHITE, fill) >= contrast(NEAR_BLACK, fill) ? WHITE : NEAR_BLACK;
  if (contrast(best, fill) < AA_NORMAL && contrast(BLACK, fill) > contrast(best, fill)) return BLACK;
  return best;
}

export function deriveBrandTokens(primary: string): BrandTokens {
  const p = normalizeHex(primary);
  return {
    primary: p,
    primaryInk: ink(p),
    onPrimary: textOn(p),
    tint: flattenOverWhite(p, TINT_ALPHA),
    primaryOnDark: onDark(p),
  };
}
