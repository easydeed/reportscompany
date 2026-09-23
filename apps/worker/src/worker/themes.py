"""
The token layer — Workstream A of the delivery-surfaces master plan (§04).

WHAT THIS IS FOR
----------------
An affiliate picks one colour. Everywhere that colour is *used* — a fill, a
price, a button label, a zebra row — needs a different value derived from it,
and the current build derives none of them: every template hardcodes a hand-
picked shade of the teal that shipped as the default. That is why

    Luxury Estates renders its price in #0D9488 at 3.74:1 on white,

below the 4.5:1 WCAG AA threshold, on every listing card in every PDF today.
It is not a template bug. It is the absence of this module.

`derive_theme()` takes the one colour and returns the five values the design
system names (master plan §3.1):

    primary       the colour as given — FILLS ONLY, never text on a light
                  surface, because nothing guarantees it is readable there
    primary_dark  primary x 0.78 — gradient ends, hovers, borders
    primary_ink   primary darkened in 6% steps until it clears 4.5:1 on white.
                  The only brand value permitted as text on a light surface.
    on_primary    whichever of white or #14151A scores higher against primary.
                  What you put ON a primary fill.
    tint          primary at 6% alpha, pre-flattened over white because
                  Outlook drops rgba(). Zebra rows, callout panels.
    primary_on_dark
                  the brand, brightened until it clears 4.5:1 on ONE FIXED dark
                  neutral. The counterpart to primary_ink, which only ever
                  guaranteed anything on white.

WHY NOT compute_color_roles(), WHICH ALREADY EXISTS
---------------------------------------------------
`property_builder.compute_color_roles` does a related job with six differently
named roles and different arithmetic, and it is live on every render today.
This module deliberately does NOT replace it yet, and the reason is measured
rather than cautious. Workstream A was specified to ship invisibly; substituting
these tokens for the values the templates hardcode moves 12 of 17 brand-role
values past a just-noticeable difference, two of them enormously — white label
text on the coral and teal fills becomes #14151a, because white on those fills
is 2.80:1 and 3.74:1 and cannot stay. **Those moves are the fix.** They are also
a visible change to every send, so they belong in a migration that is reviewed
one surface at a time, not in the commit that introduces the derivation. The
measurements are on D-097.

So the two coexist, with one guard: `tests/test_themes.py` asserts their shared
primitives (hex parsing, luminance) agree. They can diverge only deliberately.

DETERMINISM
-----------
Pure function of the input string. No clock, no randomness, no dict ordering,
no environment. The same hex yields byte-identical tokens in any process, which
is what makes the golden file below meaningful and what makes caching safe.
"""
from __future__ import annotations

import colorsys
import re
from functools import lru_cache
from typing import Dict, Tuple

__all__ = [
    "derive_theme",
    "TOKENS",
    "DARK_SURFACE",
    "contrast",
    "relative_luminance",
    "normalize_hex",
    "WHITE",
    "NEAR_BLACK",
    "AA_NORMAL",
]

# The two candidates for text on a primary fill. #14151A rather than #000000:
# pure black on a saturated fill vibrates, and the difference in contrast is
# under 4%.
WHITE = "#ffffff"
NEAR_BLACK = "#14151a"

#: WCAG 2.1 AA for normal-size text.
AA_NORMAL = 4.5

# ── The one fixed dark surface ─────────────────────────────────────────────
#
# Decided 2026-09-23 (Jerry): ONE fixed neutral for every theme, not a per-theme
# value the derivation takes as an argument. §3.2 already fixes the neutrals for
# this reason, and five surfaces would mean five things to guarantee against and
# five ways to drift. D-099 is evidence for it — widening `compute_color_roles`
# to accept several surfaces was necessary for the market band, and the first
# thing it produced was a pair no colour can satisfy.
#
# #0f172a because it is the dark neutral these templates already use most (15
# occurrences, more than any other), so the token converges on the design rather
# than adding to it. It is a neutral, not a brand navy: the current default
# `#18235c` has chroma 68 and is somebody's brand colour doing a neutral's job.
#
# **THE GUARANTEE IS AGAINST THIS SURFACE AND NO OTHER, AND THAT IS A CONDITION,
# NOT A DETAIL.** Six of the eight dark surfaces the templates paint today are
# lighter than it, so a value that clears 4.5:1 here does NOT clear it there:
#
#     on #0b0f1a  4.82 ok      on #0f1a45  4.22       on #15216e  3.59
#     on #0f1629  4.54 ok      on #111827  4.47       on #1b365d  3.06
#                              on #1a1a1a  4.39       on #18235c  3.69
#
# That is the migration this decision implies — the dark panels become this
# neutral — and until they do, `primary_on_dark` is correct about a surface the
# page does not yet have. Measured and stated rather than discovered later; the
# list above is the checklist. See D-097.
DARK_SURFACE = "#0f172a"

#: One darkening step. 6% per the design system; the loop below applies it
#: repeatedly rather than solving directly, because "darkened in 6% steps" is
#: the specified behaviour and a closed-form solution would give different
#: values for the same intent.
_STEP = 0.94

#: Enough steps to take pure white past 4.5:1 (which needs 12) with room to
#: spare. Reaching this bound means the loop failed to converge, which cannot
#: happen for any sRGB input — see test_the_step_bound_is_never_reached.
_MAX_STEPS = 64

#: Alpha for `tint`, flattened over white.
_TINT_ALPHA = 0.06

_HEX_RE = re.compile(r"\A#?([0-9a-fA-F]{3}|[0-9a-fA-F]{6})\Z")


def normalize_hex(value: str) -> str:
    """
    '#ABC' / 'abc' / '#AABBCC' -> '#aabbcc'.

    Raises ValueError on anything else. This module does not guess: a colour it
    cannot parse is a configuration error, and silently substituting a default
    here is how an affiliate ends up shipping somebody else's brand without a
    single log line. Callers that need a fallback choose it themselves.
    """
    if not isinstance(value, str):
        raise ValueError(f"not a hex colour: {value!r}")
    m = _HEX_RE.match(value.strip())
    if not m:
        raise ValueError(f"not a hex colour: {value!r}")
    h = m.group(1).lower()
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return "#" + h


def _to_rgb(value: str) -> Tuple[int, int, int]:
    h = normalize_hex(value)[1:]
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _to_hex(r: int, g: int, b: int) -> str:
    clamp = lambda c: max(0, min(255, int(round(c))))  # noqa: E731
    return "#{:02x}{:02x}{:02x}".format(clamp(r), clamp(g), clamp(b))


def _linearize(channel_0_255: int) -> float:
    c = channel_0_255 / 255.0
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4


def relative_luminance(value: str) -> float:
    """WCAG 2.1 relative luminance, 0.0 (black) to 1.0 (white)."""
    r, g, b = _to_rgb(value)
    return (
        0.2126 * _linearize(r)
        + 0.7152 * _linearize(g)
        + 0.0722 * _linearize(b)
    )


def contrast(a: str, b: str) -> float:
    """
    WCAG 2.1 contrast ratio between two colours, 1.0 to 21.0. Symmetric.

    The codebase had `_relative_luminance` but no contrast function, which is
    why the shipped palette was never checked against a threshold — you cannot
    accidentally measure something you have no instrument for.
    """
    la, lb = relative_luminance(a), relative_luminance(b)
    lighter, darker = max(la, lb), min(la, lb)
    return (lighter + 0.05) / (darker + 0.05)


def _scale(value: str, factor: float) -> str:
    r, g, b = _to_rgb(value)
    return _to_hex(r * factor, g * factor, b * factor)


def _flatten_over_white(value: str, alpha: float) -> str:
    r, g, b = _to_rgb(value)
    mix = lambda c: c * alpha + 255 * (1 - alpha)  # noqa: E731
    return _to_hex(mix(r), mix(g), mix(b))


def _brighten(value: str) -> str:
    """
    One step brighter, spending saturation only as a last resort.

    Value first (+0.04); saturation (-0.04) only once value has maxed out.
    Deliberately the same rule as `property_builder._brighten`, which D-099
    established by measurement: the previous version there reduced saturation on
    every step and turned a navy brand asked to be readable on a navy panel into
    a grey — chroma 33 where value-first gives 156.
    """
    r, g, b = (c / 255 for c in _to_rgb(value))
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    if v >= 1.0:
        s = max(0.0, s - 0.04)
    else:
        v = min(1.0, v + 0.04)
    return _to_hex(*(c * 255 for c in colorsys.hsv_to_rgb(h, s, v)))


def _on_dark(value: str) -> str:
    """
    Brighten until the colour clears AA on `DARK_SURFACE`.

    Returns it unchanged when it already does — most brands are lighter than
    #0f172a and need nothing. Terminates because brightening reaches white, and
    white on #0f172a is 17.85:1.
    """
    current = normalize_hex(value)
    for _ in range(_MAX_STEPS):
        if contrast(current, DARK_SURFACE) >= AA_NORMAL:
            return current
        stepped = _brighten(current)
        if stepped == current:
            break
        current = stepped
    return WHITE


def _ink(value: str) -> str:
    """
    Darken in 6% steps until the result clears AA on white.

    TERMINATION. Each step multiplies every channel by 0.94, so luminance is
    strictly decreasing toward black, whose contrast on white is 21:1 — the
    condition is reachable from every sRGB colour. Two inputs make that claim
    worth stating rather than assuming:

      #000000 exits on the first check having darkened nothing.
      #ffff00 is the slowest chromatic case at 12 steps, landing on #797900 —
              a dark olive that still reads as the colour it came from. It does
              NOT bottom out at black, which is the failure mode the spec calls
              "looping to the floor".

    Integer rounding means a step can fail to change a very dark colour at all.
    That is harmless (such a colour already passes) but it would be an infinite
    loop without the bound, so there is a bound.
    """
    current = normalize_hex(value)
    for _ in range(_MAX_STEPS):
        if contrast(current, WHITE) >= AA_NORMAL:
            return current
        stepped = _scale(current, _STEP)
        if stepped == current:
            break  # rounding floor: cannot darken further by scaling
        current = stepped
    # Unreachable for sRGB inputs (asserted by test). If it ever happens,
    # return a value that is certainly readable rather than one that is nearly.
    return NEAR_BLACK


@lru_cache(maxsize=512)
def _derive(primary: str) -> Tuple[Tuple[str, str], ...]:
    """
    The memoised derivation. Returns tuples rather than a dict so that what is
    held in the cache cannot be mutated by anyone who got a reference to it —
    see `derive_theme` below.
    """
    p = normalize_hex(primary)
    return (
        ("primary", p),
        ("primary_dark", _scale(p, 0.78)),
        ("primary_ink", _ink(p)),
        ("on_primary",
         WHITE if contrast(WHITE, p) >= contrast(NEAR_BLACK, p) else NEAR_BLACK),
        ("tint", _flatten_over_white(p, _TINT_ALPHA)),
        ("primary_on_dark", _on_dark(p)),
    )


def derive_theme(primary: str) -> Dict[str, str]:
    """
    The five tokens, from one brand colour.

    Cached on the colour, which is the same thing as cached per affiliate and
    strictly better: two affiliates who picked the same teal share the entry,
    and an affiliate who changes their colour gets a new one without an
    invalidation step. The function is pure, so a stale entry is impossible.

    A FRESH DICT EVERY CALL, over a memoised derivation. Handing out the cached
    object itself would be faster by one five-key copy and would mean that any
    caller who did `roles["primary"] = ...` — or merged the tokens into a render
    context and then adjusted one — silently rewrote the palette for every
    later caller in that process, including other affiliates' reports on the
    same worker. That is a cross-tenant bug hiding inside a performance
    micro-optimisation, and it would present as one account's colour appearing
    in another's PDF.
    """
    return dict(_derive(primary))


#: Cache controls, forwarded so callers and tests do not reach into `_derive`.
derive_theme.cache_info = _derive.cache_info
derive_theme.cache_clear = _derive.cache_clear


#: The five keys, in the order the design system lists them. Exported so a
#: consumer can assert it is handling all of them rather than the ones it
#: happened to know about when it was written.
TOKENS = ("primary", "primary_dark", "primary_ink", "on_primary", "tint",
          "primary_on_dark")
