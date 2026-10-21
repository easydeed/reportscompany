"""The premises the per-ground inks rest on, asserted rather than assumed.

D-208 replaced an enumeration of grounds with an argument: `ink_on` returns a
DARKENED ink, so a dark ink's contrast only rises as the ground lightens, and
an ink that clears the darkest paper tone a template declares clears every
lighter one — including the ones nobody enumerated.

**That argument is load-bearing and nothing asserted it.** `linen` derives one
ink against `--cream-dark` and uses it on `--cream`, on white, and on the faint
brand tints some pages carry, and it never measures those. If `ink_on` ever
returned a LIGHTER ink for some brand, the monotonicity reverses, every one of
those sites loses its guarantee, and **the failure is invisible precisely
because the lighter grounds are deliberately unmeasured.** §0.6, 2026-10-21:
the rule only holds while nobody reverts to listing, and an ungated premise is
how the listing comes back.

So: the direction is asserted, and the consequence is asserted separately
against the real grounds rather than being left to follow from it. Two
assertions where one would do, because the argument and the thing the argument
is about can drift apart.

THE BRANDS ARE THE SWEEP'S, NOT A LIST HERE. `cover_brand_sweep.json` carries
38 — 32 spaced evenly in relative luminance plus the six presets — and reusing
them means a brand added there is tested here without anyone remembering to.
"""
import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "apps/worker/src"))

from worker.property_builder import (  # noqa: E402
    ink_on, _ensure_readable_on_dark, normalize_hex_color,
)

SWEEP = REPO / "apps/worker/tests/cover_brand_sweep.json"

#: The paper tones `linen` declares, darkest first. The monotonicity claim is
#: about THIS family: one ink derived against the first clears all of them.
#: `#fef4f4` is not declared anywhere — it is the faint brand tint a page
#: carried that cost 4.48:1 and prompted the whole argument, kept here because
#: the point of the claim is covering grounds nobody enumerated.
PAPER_DARKEST = "#F0EBE3"
PAPER_LIGHTER = ("#FAF7F2", "#FEF4F4", "#FFFFFF")

AA = 4.5


def _lum(hex_colour):
    def ch(c):
        c /= 255
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    h = normalize_hex_color(hex_colour).lstrip("#")
    r, g, b = (ch(int(h[i:i + 2], 16)) for i in (0, 2, 4))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _contrast(a, b):
    la, lb = _lum(a), _lum(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def brands():
    if not SWEEP.exists():
        pytest.skip(f"{SWEEP.name} is missing; run scripts/sweep_cover_brand_space.py")
    return [(b["name"], b["hex"]) for b in json.loads(SWEEP.read_text())["brands"]]


def test_there_are_brands_to_check():
    """The guard. An empty sweep makes every assertion below vacuous."""
    assert len(brands()) >= 30, f"only {len(brands())} brands in the sweep"


@pytest.mark.parametrize("ground", (PAPER_DARKEST,) + PAPER_LIGHTER + ("#E8D5A3", "#F1F5F9"))
def test_ink_on_never_returns_a_lighter_ink_than_it_was_given(ground):
    """THE PREMISE. `ink_on` darkens; it must never lighten.

    This is the sentence the monotonicity argument stands on, and the reason it
    is a test rather than a comment: if it ever stops being true the sites that
    depend on it do not fail, they go quiet.
    """
    for name, brand in brands():
        got = ink_on(brand, ground)
        assert _lum(got) <= _lum(brand) + 1e-9, (
            f"ink_on({brand}, {ground}) returned {got}, which is LIGHTER than "
            f"its input ({_lum(got):.4f} > {_lum(brand):.4f}) for brand {name}.\n"
            f"The monotonicity argument in §0.6 and on D-208 reverses if this "
            f"happens: every site using an ink derived against the darkest "
            f"ground silently loses its guarantee on the lighter ones, which "
            f"are not measured BECAUSE of that argument."
        )


def test_an_ink_derived_against_the_darkest_paper_clears_every_lighter_one():
    """THE CONSEQUENCE, asserted directly instead of being left to follow.

    `linen` derives `--burgundy-on-cream-dark` against `#F0EBE3` and uses it on
    cream, on white and on page tints it never measures. This is that claim,
    measured — so the templates are not relying on the argument alone.
    """
    failures = []
    for name, brand in brands():
        ink = ink_on(brand, PAPER_DARKEST)
        base = _contrast(ink, PAPER_DARKEST)
        assert base >= AA, f"{name}: ink_on does not clear its own ground ({base:.2f})"
        for lighter in PAPER_LIGHTER:
            got = _contrast(ink, lighter)
            if got < AA or got < base - 1e-9:
                failures.append(f"{name} {ink} on {lighter}: {got:.2f} "
                                f"(against {base:.2f} on {PAPER_DARKEST})")
    assert not failures, (
        "an ink derived against the darkest paper tone did not clear a lighter "
        "one:\n  " + "\n  ".join(failures)
    )


def test_ink_on_dark_never_returns_a_darker_ink_than_it_was_given():
    """The counterpart, for the one surface that needs it.

    `harbor`'s `.aerial-card h3` derives against `#2b3045` and is used only
    there, so no family claim rests on it — but the direction is asserted
    anyway, because the next template to need an on-dark ink will reach for
    this function and may well reach for the argument with it.
    """
    for name, brand in brands():
        got = _ensure_readable_on_dark(brand, "#2b3045")
        assert _lum(got) >= _lum(brand) - 1e-9, (
            f"_ensure_readable_on_dark({brand}) returned {got}, DARKER than its "
            f"input, for brand {name}"
        )


def test_the_claim_is_about_an_ordered_family_and_says_so():
    """The scope of the argument, which is the part that decays.

    `--gold-light` is DARKER than every paper tone and `#2b3045` is a dark
    ground entirely; neither is in the family, both have their own derivation,
    and an ink derived against the darkest paper does NOT serve them. Asserted
    so that "clear the darkest and the rest follow" cannot quietly widen into
    "one ink serves every ground".
    """
    outside = ink_on("#0D9488", PAPER_DARKEST)
    assert _contrast(outside, "#E8D5A3") < AA, (
        "an ink derived against the darkest PAPER tone now also clears "
        "--gold-light. If that is genuinely true the family has changed and "
        "this test should say so explicitly — it must not become true by "
        "accident, because the templates derive a separate ink for that ground "
        "on the strength of it not being true."
    )
