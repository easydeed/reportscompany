"""
D-099 — `compute_color_roles` must achieve what its docstrings claim.

THE DEFECT
----------
`_ensure_readable_on_dark`'s docstring read *"Target: WCAG AA (contrast ratio
>= 4.5) or at minimum 3.0 for large text."* Its code checked `>= 3.0` on entry
and `>= 3.0` in the loop. The string "4.5" appeared in neither function.

Everything about these read as a guarantee — the names, the docstrings, the fact
that they run on every PDF — and only the number was wrong. Measured on the
values the five property themes ship:

    teal     on_light  3.32        modern   on_light 3.05, text 2.80
    classic  on_dark   3.35        bold     on_dark  3.08
    elegant  on_dark   3.27

Every theme failed at least one role, and `theme_color_on_dark` cleared 4.5 on
**no theme at all**, because it could not: 3.0 was the exit condition.

Two more faults in the same twenty lines. Both helpers ran a bounded loop and
then returned whatever it last produced **without re-testing**, so a caller
could not distinguish "readable" from "gave up" and nothing was logged either
way. And `_ensure_readable_on_dark` shed 0.02 of saturation on every step while
brightening, so its escape from an unreadable brand colour was to stop it being
the brand colour.

WHAT THESE TESTS ARE SHAPED AROUND
----------------------------------
The property is easy to satisfy dishonestly: `on_light = "#000000"` and
`on_dark = "#ffffff"` clear AA for every input on every surface. So the contrast
assertions come paired with guards a degenerate implementation fails — the
result keeps the brand's hue, a colour that already passes is returned
untouched, and distinct brands stay distinct.
"""
from __future__ import annotations

import colorsys
import json
import os
import random
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
os.environ.setdefault("DATABASE_URL", "postgresql://fake/fake")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

import worker.property_builder as pb  # noqa: E402
from worker.property_builder import (  # noqa: E402
    AA_NORMAL, _brighten, _ensure_readable_on_dark, _ensure_readable_on_light,
    _text_on_accent, compute_color_roles,
)
from worker.themes import contrast, normalize_hex  # noqa: E402

GOLDEN = Path(__file__).resolve().parent / "golden" / "color_roles.json"
WHITE = "#ffffff"
SEED = 20260923

#: The dark surfaces the five property themes actually use, from
#: PropertyReportBuilder._THEME_DARK_BG. Duplicated here on purpose — if the
#: builder's map changes, `test_the_dark_surfaces_match_the_builder` says so
#: rather than this file quietly testing a surface nobody renders on.
THEME_DARK_BG = {
    "teal": "#18235c", "modern": "#1A1F36", "classic": "#1B365D",
    "bold": "#15216E", "elegant": "#1a1a1a",
}


def random_hexes(n, seed=SEED):
    rng = random.Random(seed)
    return ["#%06x" % rng.randrange(0x1000000) for _ in range(n)]


def hue_of(v):
    h = normalize_hex(v)[1:]
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    return colorsys.rgb_to_hls(r, g, b)[0] * 360.0


def hue_gap(a, b):
    d = abs(a - b) % 360.0
    return min(d, 360.0 - d)


def chroma_of(v):
    h = normalize_hex(v)[1:]
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return max(r, g, b) - min(r, g, b)


def golden():
    return json.loads(GOLDEN.read_text())


# ---------------------------------------------------------------------------
# The property, on every surface that actually renders
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("theme,dark", sorted(THEME_DARK_BG.items()))
def test_every_role_clears_aa_on_the_surface_it_renders_on(theme, dark):
    entry = golden()["property_themes"][theme]
    roles = compute_color_roles(entry["brand"], dark)
    assert contrast(roles["theme_color_on_light"], WHITE) >= AA_NORMAL
    assert contrast(roles["theme_color_on_dark"], dark) >= AA_NORMAL
    assert contrast(roles["theme_color_text"], entry["brand"]) >= AA_NORMAL


def test_the_dark_surfaces_match_the_builder():
    """
    The map above is a copy. If the builder's diverges, these tests guarantee
    contrast against a background nothing renders on — which is exactly the
    mistake the email was making before Workstream C (deriving against
    `primary_color`, rendering on `accent_color`).
    """
    from worker.property_builder import PropertyReportBuilder
    assert {k: v.lower() for k, v in PropertyReportBuilder._THEME_DARK_BG.items()} == \
           {k: v.lower() for k, v in THEME_DARK_BG.items()}


#: The ceiling on `theme_color_text`. NOT a design choice — see D-098. White and
#: near-black are fixed, their contrast curves against a fill cross at luminance
#: 0.196, and both score 4.27:1 there.
TEXT_ACHIEVABLE = 4.25

#: §0.6's two-way link. D-098 already gates the token layer's version of this;
#: it gates the PDF path's too, because both make the same binary choice against
#: a fill that has been decided must not move.
_D098_GATED = pytest.mark.xfail(
    strict=True,
    reason="D-098 — `theme_color_text` picks white or near-black against a fill "
           "that may not be adjusted, so 4.5:1 is unreachable for ~5% of sRGB; "
           "measured 278 of 5000 (5.6%), worst 4.27:1",
)


def test_the_two_surface_roles_hold_for_5000_random_brands():
    """
    `on_light` and `on_dark` can always be reached, because the VALUE moves. The
    third role cannot — see below.
    """
    bad = []
    for hexv in random_hexes(5000):
        for dark in ("#18235c", "#1a1a1a", "#0b0f1a"):
            r = compute_color_roles(hexv, dark)
            if contrast(r["theme_color_on_light"], WHITE) < AA_NORMAL:
                bad.append(("on_light", hexv, dark))
            if contrast(r["theme_color_on_dark"], dark) < AA_NORMAL:
                bad.append(("on_dark", hexv, dark))
    assert not bad, f"{len(bad)} failures, first five: {bad[:5]}"


@_D098_GATED
def test_text_on_accent_clears_aa_for_5000_random_brands():
    """
    The same ceiling as the token layer's `on_primary`, arrived at independently
    on the PDF path — which is worth stating, because D-098 reads like a fact
    about `themes.py` and is actually a fact about any binary choice of text
    against a fill that may not be adjusted. Both derivations have it.

    Left strict rather than relaxed to 4.27, for the reason on the entry: the
    fill is the affiliate's colour and does not move, so this is unreachable BY
    DESIGN and the build should say so the day that changes.
    """
    bad = [h for h in random_hexes(5000)
           if contrast(_text_on_accent(h), h) < AA_NORMAL]
    assert not bad, f"{len(bad)} of 5000 fills cannot carry readable text"


def test_text_on_accent_always_reaches_the_achievable_ceiling():
    """What the specified derivation DOES guarantee. Catches it getting worse."""
    bad = [(h, round(contrast(_text_on_accent(h), h), 3))
           for h in random_hexes(5000)
           if contrast(_text_on_accent(h), h) < TEXT_ACHIEVABLE]
    assert not bad, f"below the measured floor: {bad[:5]}"


# ---------------------------------------------------------------------------
# The guards. Every assertion above is satisfied by black-and-white.
# ---------------------------------------------------------------------------

def test_a_colour_that_already_passes_is_returned_untouched():
    """
    Nudging a passing colour is a visible change with no defect behind it, and
    it is what an implementation that always steps at least once would do.
    """
    # .lower() because `normalize_hex_color` preserves the case it was given
    # while the derived values are always lowercase — a cosmetic inconsistency,
    # pinned here rather than changed, since these strings reach `style`
    # attributes and comparisons elsewhere.
    assert _ensure_readable_on_light("#1B365D").lower() == "#1b365d"   # 12.12 on white
    assert _ensure_readable_on_dark("#34D1C3", "#18235c").lower() == "#34d1c3"   # 7.71
    assert _ensure_readable_on_light("#7C3AED").lower() == "#7c3aed"


def test_the_roles_keep_the_brands_hue():
    """
    THE GUARD. `on_light = black` and `on_dark = white` satisfy every contrast
    assertion in this file for every input.

    Tolerance measured, not guessed: `_darken` scales all three channels so its
    drift is pure 8-bit rounding, and `_brighten` raises HSV value which is
    hue-exact until saturation has to be spent. 4 degrees covers both above
    chroma 64; below that the input's own hue is rounding noise.
    """
    off = []
    for hexv in random_hexes(600):
        if chroma_of(hexv) < 64:
            continue
        light = _ensure_readable_on_light(hexv)
        if hue_gap(hue_of(light), hue_of(hexv)) > 4.0:
            off.append(("on_light", hexv, light))
    assert not off, f"the readable value is no longer the brand: {off[:5]}"


def test_on_dark_spends_saturation_last_not_first():
    """
    The old version reduced saturation on EVERY brightening step — thirty steps
    removed 0.6 of it — so a navy brand asked to be readable on a navy panel
    came back a grey. Measured on the three themes where the brand IS the dark
    surface, which is the worst case for this:

        classic  old #5f88c3 chroma 100 at 3.35   new #639fff chroma 156 at 4.58
    """
    for theme in ("classic", "bold"):
        dark = THEME_DARK_BG[theme]
        brand = golden()["property_themes"][theme]["brand"]
        on_dark = _ensure_readable_on_dark(brand, dark)
        assert contrast(on_dark, dark) >= AA_NORMAL
        assert chroma_of(on_dark) > 100, (
            f"{theme}: {on_dark} has chroma {chroma_of(on_dark)} — brightening "
            f"washed the brand out instead of raising its value"
        )


def test_brighten_raises_value_before_touching_saturation():
    import colorsys as cs
    r, g, b = (0x1B / 255, 0x36 / 255, 0x5D / 255)
    h0, s0, v0 = cs.rgb_to_hsv(r, g, b)
    nxt = _brighten("#1B365D")
    hn = normalize_hex(nxt)[1:]
    h1, s1, v1 = cs.rgb_to_hsv(*(int(hn[i:i + 2], 16) / 255 for i in (0, 2, 4)))
    assert v1 > v0, "value did not rise"
    assert s1 >= s0 - 0.01, "saturation was spent while value still had room"


def test_distinct_brands_stay_distinct():
    seen = {}
    for hexv in random_hexes(1200):
        key = tuple(compute_color_roles(hexv, "#18235c").values())
        seen.setdefault(key, set()).add(normalize_hex(hexv))
    collisions = {k: v for k, v in seen.items() if len(v) > 1}
    assert not collisions, f"distinct brands produced identical roles: {list(collisions.values())[:3]}"


# ---------------------------------------------------------------------------
# Never return a value you have not checked
# ---------------------------------------------------------------------------

def test_an_unreachable_target_is_reported_rather_than_returned_quietly():
    """
    The market report's header runs `linear-gradient(135deg, header-bg 0%,
    header-bg 50%, primary-color 100%)` — a very dark navy to a mid-tone brand.
    **No single text colour clears 4.5:1 against both ends**, because they are
    too far apart in luminance: brightening runs to white, which fails on the
    accent; darkening runs to near-black, which fails on the navy.

    That is a defect in the band, not in this function. What this function owes
    is to say so. It returns the best worst-case available and increments a
    counter, rather than returning a number nobody measured — which is what the
    old code did on every call that ran out of iterations.
    """
    before = pb.UNREACHABLE_CONTRAST_COUNT
    value = _ensure_readable_on_dark("#0d9488", ("#18235c", "#0d9488"))
    assert pb.UNREACHABLE_CONTRAST_COUNT == before + 1, "the shortfall was silent"
    # and it still returns the best of the two candidates, not an arbitrary one
    assert value == "#ffffff"
    assert min(contrast(value, "#18235c"), contrast(value, "#0d9488")) == \
        pytest.approx(3.74, abs=0.01)


def test_the_counter_stays_at_zero_for_every_surface_we_actually_render():
    """
    The corollary. A counter that ticks on normal traffic is noise nobody reads.
    """
    before = pb.UNREACHABLE_CONTRAST_COUNT
    for theme, dark in THEME_DARK_BG.items():
        compute_color_roles(golden()["property_themes"][theme]["brand"], dark)
    for name, e in golden()["picker_themes"].items():
        compute_color_roles(e["brand"], e["dark_surface"])
    assert pb.UNREACHABLE_CONTRAST_COUNT == before


@pytest.mark.parametrize("junk", [None, 123, [], (), "nope", {"a": 1}, ["#18235c", None]])
def test_a_dark_surface_that_is_not_a_colour_falls_back_rather_than_raising(junk):
    """
    These values arrive from three write paths that accept any string, which is
    why `test_compute_color_roles_never_raises` exists. Widening `dark_bg` to
    accept a sequence removed the coercion that used to handle them and made
    `_surfaces(None)` a TypeError — caught by that test on the first full-suite
    run, after this module alone had been green.
    """
    roles = compute_color_roles("#0d9488", junk)
    assert roles["theme_color_on_dark"] == compute_color_roles("#0d9488", "#18235c")["theme_color_on_dark"]


def test_a_gradient_is_guaranteed_against_every_stop():
    """
    A single-colour `dark_bg` must keep working, and a sequence must bind on the
    worst stop — not the first one, which is how the market label measured
    9.90:1 where it started and 2.53:1 where it ended.
    """
    one = _ensure_readable_on_dark("#7C3AED", "#18235c")
    assert contrast(one, "#18235c") >= AA_NORMAL
    both = _ensure_readable_on_dark("#7C3AED", ("#18235c", "#0f1a45"))
    assert min(contrast(both, "#18235c"), contrast(both, "#0f1a45")) >= AA_NORMAL


# ---------------------------------------------------------------------------
# _text_on_accent was a threshold, not a comparison
# ---------------------------------------------------------------------------

def test_text_on_accent_picks_the_better_candidate():
    """
    It was `'#ffffff' if luminance < 0.35 else '#1a1a1a'`. The crossover for a
    white/near-black pair is at luminance 0.196, so a whole band of mid-tone
    brands got white when near-black wins — the modern theme's coral at 2.80:1.
    """
    seen = set()
    for hexv in random_hexes(2000):
        got = _text_on_accent(hexv)
        best = max(("#ffffff", "#14151a"), key=lambda c: contrast(c, hexv))
        assert got == best, f"{hexv}: chose {got}, {best} scores higher"
        seen.add(got)
    assert seen == {"#ffffff", "#14151a"}, "one branch is dead"


def test_the_modern_themes_coral_no_longer_carries_white():
    assert contrast("#ffffff", "#FF6B5B") == pytest.approx(2.80, abs=0.01)
    assert _text_on_accent("#FF6B5B") == "#14151a"


# ---------------------------------------------------------------------------
# Golden lock
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("group,name", [
    (g, n) for g in ("property_themes", "picker_themes") for n in golden()[g]
])
def test_golden_lock(group, name):
    want = golden()[group][name]
    got = compute_color_roles(want["brand"], want["dark_surface"])
    for role in ("theme_color", "theme_color_light", "theme_color_dark",
                 "theme_color_on_light", "theme_color_on_dark", "theme_color_text"):
        assert got[role].lower() == want[role].lower(), (
            f"{name}.{role}: {got[role]} now, {want[role]} locked")
    a = want["achieved"]
    assert round(contrast(got["theme_color_on_light"], WHITE), 2) == a["on_light_vs_white"]
    assert round(contrast(got["theme_color_on_dark"], want["dark_surface"]), 2) == a["on_dark_vs_surface"]
    assert round(contrast(got["theme_color_text"], want["brand"]), 2) == a["text_vs_brand"]


def test_the_golden_file_records_a_passing_ratio_for_every_role():
    """
    The file is the record D-099 says was missing: the achieved number, written
    down. A lock that stored only the hexes could hold a failing value forever.
    """
    for group in ("property_themes", "picker_themes"):
        for name, e in golden()[group].items():
            a = e["achieved"]
            for role in ("on_light_vs_white", "on_dark_vs_surface", "text_vs_brand"):
                assert a[role] >= AA_NORMAL, f"{name}.{role} is locked at {a[role]}"


def test_the_golden_file_covers_every_theme():
    assert set(golden()["property_themes"]) == set(THEME_DARK_BG)
    assert set(golden()["picker_themes"]) == {
        "demo_title", "luxury_estates", "coastal", "amber", "lime", "violet"}
