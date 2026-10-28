/**
 * The web's brand tokens are the worker's, value for value.
 *
 * `fixtures/brand-tokens.json` is generated from `themes.derive_theme` over 25
 * named brands (the corpus samples, the amber and lime that fail as raw text,
 * black, white, greys) and 175 random ones; `tests/test_brand_tokens_fixture.py`
 * keeps the fixture equal to Python. A story whose hero number came out one
 * step off the report it shares would be the drift this stops.
 */
import { deriveBrandTokens, contrast } from "@/lib/brand-tokens";
import fixture from "./fixtures/brand-tokens.json";

type Row = { input: string; primary: string; primaryInk: string; onPrimary: string; tint: string; primaryOnDark: string };

describe("deriveBrandTokens matches themes.derive_theme", () => {
  it.each((fixture as Row[]).map((r) => [r.input, r]))("%s", (_input, row) => {
    const t = deriveBrandTokens((row as Row).input);
    expect(t).toEqual({
      primary: (row as Row).primary,
      primaryInk: (row as Row).primaryInk,
      onPrimary: (row as Row).onPrimary,
      tint: (row as Row).tint,
      primaryOnDark: (row as Row).primaryOnDark,
    });
  });
});

describe("the inks clear AA where the stories put them", () => {
  it.each((fixture as Row[]).map((r) => [r.input]))("%s", (input) => {
    const t = deriveBrandTokens(input as string);
    // The band's text is 24–34px at 600–800 weight: large text, AA 3.0. The
    // better of white and near-black never falls below 4.27 on any sRGB colour
    // (measured over every 997th colour), so this has room.
    expect(contrast(t.onPrimary, t.primary)).toBeGreaterThanOrEqual(3.0);
    expect(contrast(t.primaryInk, "#ffffff")).toBeGreaterThanOrEqual(4.5);
    expect(contrast(t.primaryInk, t.tint)).toBeGreaterThanOrEqual(4.5);
  });
});
