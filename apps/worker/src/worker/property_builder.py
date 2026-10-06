"""
Property Report Builder
=======================

Renders property reports (seller/buyer) using self-contained Jinja2 templates.
All 5 themes use the same unified data contract.

Themes:
- classic (1): Navy + Sky Blue, Merriweather + Source Sans Pro
- modern (2): Coral + Midnight, Space Grotesk + DM Sans
- elegant (3): Burgundy + Gold, Playfair Display + Montserrat
- teal (4): Teal + Navy, Montserrat
- bold (5): Navy + Gold, Oswald + Montserrat

Usage:
    builder = PropertyReportBuilder(report_data)
    html = builder.render_html()
"""

import os
import re
import logging
import colorsys
import math
from datetime import date
from typing import Dict, Any, List, Optional
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape
from worker import theme_registry as _registry
from worker.themes import derive_theme
from worker.template_filters import (
    format_currency as _fmt_currency,
    format_currency_short as _fmt_currency_short,
    format_measure as _fmt_measure,
    format_number as _fmt_number,
    truncate as _truncate_fn,
)

logger = logging.getLogger(__name__)

_BUILDER_VERSION = "2026-03-05-v1"
logger.warning("[DIAGNOSTIC] PropertyReportBuilder version: %s", _BUILDER_VERSION)


# =============================================================================
# Color Utility Functions — compute derived roles from a single accent hex
# =============================================================================

_HEX_COLOR_RE = re.compile(r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")

# Neutral indigo, matching the email template's own default. Used only when a
# stored colour cannot be parsed at all.
_FALLBACK_HEX = "#6366f1"


def normalize_hex_color(value, fallback: str = _FALLBACK_HEX) -> str:
    """
    Coerce a stored brand colour to a `#rrggbb` string that is safe to both
    parse and interpolate.

    Brand colours are user input. Two of the three write paths accept them as a
    bare `str` with no pattern, so a value like "red" — which is the natural
    thing for a person to type into a colour field — reaches this module. Before
    this function existed, that value crashed every render that touched it:
    `int("rr", 16)` raises ValueError, the exception propagated out of
    `schedule_email_html` into `send_schedule_email`, and the email was never
    sent. One settings save silently stopped all delivery on the account.

    Anything that is not a 3- or 6-digit hex triple becomes the fallback. That
    is deliberate over "pass it through and hope CSS understands it": these
    values are also interpolated straight into `style="…"` attributes, so a
    permissive path here would trade a crash for a CSS-injection.
    """
    if isinstance(value, str) and _HEX_COLOR_RE.match(value.strip()):
        return value.strip()
    return fallback


# Schemes that may appear in an href or src we build from stored data. Anything
# else — javascript:, data:, vbscript:, file: — is dropped.
_SAFE_URL_SCHEMES = ("http://", "https://", "//", "/")


def safe_url(value, fallback: str = "") -> str:
    """
    Allowlist the scheme of a URL that came from stored, user-supplied data.

    This is deliberately NOT the same problem as HTML escaping, and it lives
    here — beside `normalize_hex_color`, above all the render surfaces — rather
    than in the email module, because escaping does not touch it:

        html.escape("javascript:alert(1)")            -> unchanged
        Jinja autoescape of the same, inside href=""  -> unchanged, still live

    The PDF builders in this module and in market_builder.py run Jinja with
    autoescape on, which handles their HTML injection. It does nothing for a
    scheme, and a PDF is rendered by an actual browser — so for the URL fields
    this allowlist is the whole of the defence, not a second layer of it.

    Returns the fallback (empty by default, which collapses the surrounding
    markup) when the scheme is not allowlisted.

    A scheme check alone is NOT enough, and assuming it was is a mistake this
    function was written with and a test caught: an allowlisted scheme still
    lets the rest of the value break out of the attribute it lands in —

        https://cdn.example.test/a.jpg" onerror="alert(1)

    passes any scheme test and is a live event handler. So the value is also
    truncated at the first character that cannot legally appear in a URI
    (RFC 3986): quote, angle bracket, backtick, backslash, whitespace. That is
    lossless for a real URL and leaves a usable prefix rather than a mangled
    string. Truncation rather than deletion is deliberate — deleting the
    offending characters would splice the payload onto the end of the path.

    The result is NOT HTML-escaped, so this is safe to use in both the f-string
    surfaces here and inside an autoescaping Jinja template without producing
    `&amp;amp;` in a query string.
    """
    if not isinstance(value, str):
        return fallback
    candidate = value.strip()
    if not candidate:
        return fallback
    # Control characters first: "java\tscript:alert(1)" is read as a scheme by
    # some parsers, so they must go before the scheme is inspected.
    candidate = "".join(c for c in candidate if ord(c) >= 0x20 and c != "\x7f")
    for i, ch in enumerate(candidate):
        if ch in '"\'<>`\\ \t':
            candidate = candidate[:i]
            break
    if candidate.lower().startswith(_SAFE_URL_SCHEMES):
        return candidate
    return fallback


def sanitize_context_urls(value, _key: str = ""):
    """
    Sweep a Jinja render context and scheme-check every URL-shaped value.

    THIS EXISTS TO INVERT THE GUARANTEE. Applying `safe_url()` at each site
    that builds a context is only as complete as the search that found those
    sites — "I checked the ones I could see". Sweeping the finished context at
    the render boundary makes the property structural instead: an unchecked URL
    cannot reach a template, whatever new code path put it there.

    A key ending in `_url` is the trigger. That is the naming convention every
    URL in these contexts already follows (agent_photo_url, logo_url,
    map_image_url, hero_photo_url, chart_url, cover_image_url, …), and the
    sweep is recursive, so URLs nested inside listing and comparable dicts are
    covered too.

    It SANITISES rather than raising. Raising would convert an injection into
    an outage, which is the mistake D-059 was: a render that stops is worse for
    the account than a logo that fails to load. A dropped value becomes None so
    the surrounding markup collapses, and the drop is logged so it is visible.
    """
    if isinstance(value, dict):
        return {k: sanitize_context_urls(v, k) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        cleaned = [sanitize_context_urls(v, _key) for v in value]
        return type(value)(cleaned) if isinstance(value, tuple) else cleaned
    if _key.endswith("_url") and isinstance(value, str) and value:
        cleaned = safe_url(value)
        if cleaned != value:
            logger.warning(
                "sanitize_context_urls: dropped disallowed URL in %r (%.60s…)",
                _key, value,
            )
        return cleaned or None
    return value


def _hex_to_rgb(hex_color: str) -> tuple:
    """Convert '#RRGGBB' to (r, g, b) floats in 0-1. Never raises."""
    h = normalize_hex_color(hex_color).lstrip("#")
    if len(h) == 3:
        h = h[0]*2 + h[1]*2 + h[2]*2
    return tuple(int(h[i:i+2], 16) / 255.0 for i in (0, 2, 4))


def _rgb_to_hex(r: float, g: float, b: float) -> str:
    """Convert (r, g, b) floats in 0-1 to '#RRGGBB'."""
    return "#{:02x}{:02x}{:02x}".format(
        max(0, min(255, int(r * 255))),
        max(0, min(255, int(g * 255))),
        max(0, min(255, int(b * 255))),
    )


def _relative_luminance(r: float, g: float, b: float) -> float:
    """WCAG relative luminance (0 = black, 1 = white)."""
    def _lin(c):
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * _lin(r) + 0.7152 * _lin(g) + 0.0722 * _lin(b)


def _lighten(hex_color: str, amount: float = 0.3) -> str:
    """Lighten a color by mixing with white."""
    r, g, b = _hex_to_rgb(hex_color)
    return _rgb_to_hex(
        r + (1.0 - r) * amount,
        g + (1.0 - g) * amount,
        b + (1.0 - b) * amount,
    )


def _darken(hex_color: str, amount: float = 0.25) -> str:
    """Darken a color by mixing toward black."""
    r, g, b = _hex_to_rgb(hex_color)
    return _rgb_to_hex(r * (1 - amount), g * (1 - amount), b * (1 - amount))


# ═══════════════════════════════════════════════════════════════════════════
# D-099 — the readability helpers, made to mean what they say
# ═══════════════════════════════════════════════════════════════════════════
#
# WHAT THESE USED TO DO. `_ensure_readable_on_dark`'s docstring read *"Target:
# WCAG AA (contrast ratio >= 4.5) or at minimum 3.0 for large text."* Its code
# checked `>= 3.0` on entry and `>= 3.0` in the loop. 4.5 appeared in neither
# function. Everything about them read as a guarantee — the names, the
# docstrings, the fact that they run on every render — and the number was wrong.
#
# Measured before the fix, on the values the five property themes actually ship:
#
#     teal     on_light  3.32      modern   on_light 3.05, text 2.80
#     classic  on_dark   3.35      bold     on_dark  3.08
#     elegant  on_dark   3.27
#
# Every theme failed at least one role, and `theme_color_on_dark` never cleared
# 4.5 on ANY theme, because it stopped at 3.0 by construction.
#
# THREE THINGS CHANGE.
#
# 1. The target is 4.5, which is what the docstrings always claimed.
#
# 2. The ratio comes from `worker.themes.contrast` — the same instrument
#    Workstream A checked against the master plan's six independently measured
#    values — rather than from arithmetic inlined three times in this file.
#
# 3. **They never return a value they have not checked.** Both used to run a
#    bounded loop and then `return` whatever it last produced, without
#    re-testing. A caller could not tell "readable" from "gave up", and nothing
#    was logged either way. Now the exit is verified, the fallback is verified,
#    and a genuinely unreachable target increments a counter and logs once.
#
# 4. `_ensure_readable_on_dark` no longer trades away the brand to get bright.
#    It used to lose 0.02 of saturation on EVERY step while brightening — thirty
#    steps removed 0.6 of it — so its escape from an unreadable brand colour was
#    to stop it being the brand colour. It now raises value first and gives up
#    saturation only once value has maxed out, which for these themes is the
#    difference between a recognisable colour and a grey:
#
#        classic  mix-toward-white #929fb3 chroma 33   value-first #60a3ff chroma 159
#        bold     mix-toward-white #8d9199 chroma 12   value-first #6f89ff chroma 144
#        Luxury   mix-toward-white #2aa096 chroma 118  value-first #0fa89a chroma 153
#
#    Both clear 4.5. Only one is still the affiliate's colour.

AA_NORMAL = 4.5

#: One step. 6%, matching `worker.themes`, so the two derivations move a colour
#: at the same rate and a value can be reasoned about across both.
_READABILITY_STEP = 0.06

#: Enough steps to take any sRGB colour to the far end. Pure white needs 12 to
#: clear AA on white; the bound is generous and is asserted never to be reached.
_READABILITY_MAX_STEPS = 64

#: Incremented whenever a target could not be met. Exposed for the same reason
#: as D-094's Redis counter: a degraded path that is silent is a path nobody
#: knows they are on.
UNREACHABLE_CONTRAST_COUNT = 0


def _contrast(a: str, b: str) -> float:
    """WCAG 2.1 contrast ratio. Delegates to the token layer's implementation."""
    from .themes import contrast as _themes_contrast
    return _themes_contrast(a, b)


def _best_of(candidates, against: str) -> str:
    return max(candidates, key=lambda c: _contrast(c, against))


def _report_unreachable(role: str, colour: str, background: str, achieved: float) -> None:
    global UNREACHABLE_CONTRAST_COUNT
    UNREACHABLE_CONTRAST_COUNT += 1
    print(
        f"[CONTRAST] {role}: cannot reach {AA_NORMAL}:1 for {colour} on "
        f"{background}; best achievable {achieved:.2f}:1. Returning it anyway — "
        f"a value that is too low is still better than one nobody measured."
    )


def _brighten(hex_color: str) -> str:
    """
    One step brighter, spending saturation only as a last resort.

    Value first (+0.04), and saturation (-0.04) only once value is at 1.0. The
    old version did both on every step, which is why a navy brand asked to be
    readable on a navy panel came back as a grey.
    """
    r, g, b = _hex_to_rgb(hex_color)
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    if v >= 1.0:
        s = max(0.0, s - 0.04)
    else:
        v = min(1.0, v + 0.04)
    return _rgb_to_hex(*colorsys.hsv_to_rgb(h, s, v))


def _surfaces(dark_bg) -> tuple:
    """
    `dark_bg` may be one colour or several. Several means a GRADIENT, and text
    on a gradient has to survive the whole band — the market report's header is
    `linear-gradient(135deg, header-bg 0%, header-bg 50%, primary-color 100%)`
    and its label measured 9.90:1 at one end and 2.53:1 at the other (D-097). A
    value guaranteed against the first stop is not guaranteed against the band.
    """
    # Anything that is not a sequence of strings becomes the default. The
    # previous single-colour signature ran `normalize_hex_color(dark_bg, …)`,
    # which coerced None and any other junk — `test_compute_color_roles_never_raises`
    # exists because these values arrive from three write paths that accept any
    # string. Widening the parameter to accept a tuple removed that coercion and
    # made `_surfaces(None)` a TypeError; the test caught it on the first full
    # run. Restored here rather than in the caller, because the guarantee this
    # function is documented to make is "never raises on stored data".
    if isinstance(dark_bg, str):
        dark_bg = (dark_bg,)
    elif not isinstance(dark_bg, (list, tuple)):
        dark_bg = ()
    out = tuple(normalize_hex_color(b, "#18235c") for b in dark_bg
                if isinstance(b, str) and b)
    return out or ("#18235c",)


def _ensure_readable_on_dark(hex_color, dark_bg="#18235c") -> str:
    """
    A version of `hex_color` that clears 4.5:1 on `dark_bg`, brightened until it
    does. `dark_bg` may be several colours, in which case the result clears the
    bar against every one of them — see `_surfaces`.

    Returns the colour unchanged when it already clears the bar, so a brand that
    passes is never touched. Brightening raises HSV value and only reduces
    saturation once value has maxed out — saturation is what makes the colour
    recognisable as the brand, so it is spent last rather than first.

    When brightening cannot get there — which needs a `dark_bg` that is not
    actually dark — it falls back to whichever of white or near-black scores
    best, and if even that falls short it says so rather than returning a number
    it has not checked.
    """
    current = normalize_hex_color(hex_color)
    backgrounds = _surfaces(dark_bg)
    worst = lambda c: min(_contrast(c, b) for b in backgrounds)  # noqa: E731
    for _ in range(_READABILITY_MAX_STEPS):
        if worst(current) >= AA_NORMAL:
            return current
        stepped = _brighten(current)
        if stepped == current:
            break
        current = stepped
    fallback = max(("#ffffff", "#14151a"), key=worst)
    achieved = worst(fallback)
    if achieved < AA_NORMAL:
        _report_unreachable("on_dark", hex_color, "/".join(backgrounds), achieved)
    return fallback


def _ensure_readable_on_light(hex_color: str, light_bg: str = "#ffffff") -> str:
    """
    A version of `hex_color` that clears 4.5:1 on `light_bg`, by mixing toward
    black in 6% steps. The mirror of the above, with the same guarantees.
    """
    current = normalize_hex_color(hex_color)
    bg = normalize_hex_color(light_bg, "#ffffff")
    for _ in range(_READABILITY_MAX_STEPS):
        if _contrast(current, bg) >= AA_NORMAL:
            return current
        stepped = _darken(current, _READABILITY_STEP)
        if stepped == current:
            break
        current = stepped
    fallback = _best_of(("#14151a", "#ffffff"), bg)
    achieved = _contrast(fallback, bg)
    if achieved < AA_NORMAL:
        _report_unreachable("on_light", hex_color, bg, achieved)
    return fallback


def flatten_over(text: str, surface: str, alpha: float) -> str:
    """`text` at `alpha` over `surface` — the colour a reader actually sees."""
    tr, tg, tb = _hex_to_rgb(normalize_hex_color(text))
    sr, sg, sb = _hex_to_rgb(normalize_hex_color(surface))
    a = max(0.0, min(1.0, alpha))
    return _rgb_to_hex(tr * a + sr * (1 - a),
                       tg * a + sg * (1 - a),
                       tb * a + sb * (1 - a))


def darken_until_readable(surface: str, text: str = "#ffffff",
                          alpha: float = 1.0) -> str:
    """A version of `surface` dark enough that `text` clears AA on it.

    THE MIRROR OF `_ensure_readable_on_dark`, AND THE ONE THAT WAS MISSING.
    That function adjusts the TEXT to suit a surface. This adjusts the SURFACE
    to suit the text, which is the only thing that works for a band whose two
    ends are far apart in luminance.

    Measured on the market masthead (D-112): its gradient runs from the
    affiliate's brand to the platform accent, and for three of the six brands
    in the audit corpus **no single text colour clears 4.5:1 on both ends** —
    white fails on amber and lime, near-black fails on coastal and violet. The
    band itself is the defect, so the band is what this fixes. Once both stops
    are guaranteed, white is a measured consequence rather than a hardcode.

    Returns the colour unchanged when it already clears the bar, so a brand
    dark enough to carry white is never dulled, and it stops at the first step
    that works rather than darkening to a safe constant.
    """
    current = normalize_hex_color(surface)
    text = normalize_hex_color(text)
    # `alpha` because the thing that has to be readable is what the reader
    # SEES, and the masthead's subtitle is `rgba(255,255,255,0.7)`. A band
    # guaranteed for opaque white leaves the subtitle at 2.60:1 on the old
    # default accent; guaranteeing it for the translucent value instead makes
    # the opaque title safe by construction, and keeps the design's muted
    # subtitle rather than flattening it to the same white as the title.
    # The flatten is recomputed each step, because the backdrop is moving.
    seen = lambda c: flatten_over(text, c, alpha)  # noqa: E731
    for _ in range(_READABILITY_MAX_STEPS):
        if _contrast(seen(current), current) >= AA_NORMAL:
            return current
        stepped = _darken(current, _READABILITY_STEP)
        if stepped == current:
            break
        current = stepped
    achieved = _contrast(seen(current), current)
    if achieved < AA_NORMAL:
        _report_unreachable("surface", surface, text, achieved)
    return current


def mute_toward(text: str, surfaces, floor: float = AA_NORMAL) -> str:
    """`text` moved toward `surfaces` as far as AA allows, and no further.

    A muted subtitle is a real design intention and
    `rgba(255,255,255,0.7)` is the wrong way to express it: the alpha is
    chosen once and the surface varies per affiliate, so the flattened result
    measured 1.61:1 on lime and 2.60:1 on the default accent (D-112). This
    walks toward the surface while the worst stop still clears `floor` and
    returns the last value that did, so the muting is as much as is available
    and never more.

    Returns `text` itself when even one step would fail — muted and unreadable
    is not a trade this gets to make.
    """
    stops = _surfaces(surfaces)
    worst = lambda c: min(_contrast(c, b) for b in stops)  # noqa: E731
    best = normalize_hex_color(text)
    # Toward the surfaces means toward their luminance: darken a light text,
    # lighten a dark one. Comparing against the LIGHTEST stop, because that is
    # the end the text has least room on and therefore the one that decides
    # which direction is "toward".
    lum = lambda c: _relative_luminance(*_hex_to_rgb(c))  # noqa: E731
    lightest = max(stops, key=lum)
    step = _darken if lum(best) > lum(lightest) else _lighten
    current = best
    for _ in range(_READABILITY_MAX_STEPS):
        stepped = step(current, _READABILITY_STEP)
        if stepped == current or worst(stepped) < floor:
            break
        current = stepped
        best = current
    return best


def text_on_surfaces(surfaces) -> str:
    """Whichever of white or near-black is readable across EVERY stop.

    `_text_on_accent` for a band rather than a fill. The masthead's text sits
    on a gradient, and a colour chosen against one end is not chosen against
    the other — the mistake D-097 recorded for the email header and that the
    market PDF carried unfixed until D-112.
    """
    stops = _surfaces(surfaces)
    worst = lambda c: min(_contrast(c, b) for b in stops)  # noqa: E731
    best = max(("#ffffff", "#14151a"), key=worst)
    achieved = worst(best)
    if achieved < AA_NORMAL:
        _report_unreachable("on_band", best, "/".join(stops), achieved)
    return best


def ink_on(colour: str, background: str) -> str:
    """`colour` darkened until it clears AA on `background`.

    The public face of `_ensure_readable_on_light` with an arbitrary
    background. `theme_color_on_light` computes the same thing against
    `#ffffff` specifically, which is not the same answer on a tinted panel:
    the market report's accent stat block paints its value in the raw accent
    on a 35% tint of that same accent, which is two shades of one colour and
    measured 1.62:1 before this and 2.02:1 after the default changed (D-112).
    """
    return _ensure_readable_on_light(colour, background)


def _text_on_accent(hex_color: str) -> str:
    """
    What to put ON a fill of `hex_color`: whichever of white or near-black
    scores higher against it.

    This was `'#ffffff' if luminance < 0.35 else '#1a1a1a'` — a threshold, not a
    comparison, and it put white on the modern theme's coral at **2.80:1**. The
    crossover for a white/near-black pair is at luminance 0.196, not 0.35, so
    the old rule chose white across a whole band where near-black wins.

    #14151a rather than #1a1a1a: it is what `worker.themes` uses for the same
    role, and having one near-black in the product is worth the 0.4% of contrast.
    """
    return _best_of(("#ffffff", "#14151a"), normalize_hex_color(hex_color))


def _tri_state_bool(value):
    """True / False / None — never collapsing "unknown" into "no". (D-137)

    SimplyRETS and SiteX both express a boolean attribute as a string when
    they express it at all, and as nothing when they do not. `or False` and
    `.get(k, "No") == "Yes"` both turn the third case into the second, which
    is how a report came to tell people their home has no pool.
    """
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in ("yes", "y", "true", "1")


def compute_color_roles(hex_color: str, dark_bg="#18235c") -> Dict[str, str]:
    """
    From a single accent hex, compute a complete set of color roles:

      theme_color          – the raw user pick
      theme_color_light    – lighter tint for subtle backgrounds
      theme_color_dark     – darker shade for borders / hover states
      theme_color_on_dark  – guaranteed readable on dark backgrounds
      theme_color_on_light – guaranteed readable on light backgrounds
      theme_color_text     – white or dark text to overlay on the accent

    Both arguments are normalised up front rather than relying on _hex_to_rgb's
    own guard, so that `theme_color` agrees with the roles derived from it. If
    only the derived values were coerced, a bad stored colour would echo back
    unchanged in `theme_color` and land in a `style` attribute.
    """
    hex_color = normalize_hex_color(hex_color)
    # NOT normalised to a single colour here: `dark_bg` may name several
    # surfaces when the text sits on a gradient. `_ensure_readable_on_dark`
    # normalises each of them and guarantees against the worst.
    return {
        "theme_color":          hex_color,
        "theme_color_light":    _lighten(hex_color, 0.35),
        "theme_color_dark":     _darken(hex_color, 0.25),
        "theme_color_on_dark":  _ensure_readable_on_dark(hex_color, dark_bg),
        "theme_color_on_light": _ensure_readable_on_light(hex_color, "#ffffff"),
        "theme_color_text":     _text_on_accent(hex_color),
    }

# Template directory - points to property/ for Jinja2 inheritance to work
# This allows templates to use {% extends '_base/base.jinja2' %}
TEMPLATES_DIR = Path(__file__).parent / "templates" / "property"

# Theme template paths (relative to templates/property/)
# v3.0: Standalone self-contained templates (unique cover + CSS per theme)
#: THE ORDER PAGES APPEAR IN THE DOCUMENT, which is fixed by the templates and
#: is NOT the order of `page_set`. A caller can pass `selected_pages` in any
#: order and the rendered sequence does not change — every theme renders these
#: sections in this sequence, each wrapped in `{% if "<key>" in _pages %}`. So
#: page numbers are this list filtered by what renders, never `page_set`
#: enumerated.
PAGE_ORDER = [
    "cover", "overview", "contents", "aerial", "property",
    "analysis", "market_trends", "comparables", "comparables_all", "range",
]

#: THE COMPARABLE SET. ONE NUMBER, ONE PLACE (D-159).
#:
#: Before this there were eight caps and none of them knew about the others:
#: 60 and 15 in the API, 25 and 15 in the worker, 6 in the consumer builder, 6
#: in the cards context, `[:4]` in twenty-four template loops, and no cap at
#: all on the analysis table, the range and `total_comps`. The document said
#: "every one of the 15 appears on the Sales Comparables page" and showed
#: four, in every theme, with the range drawn over the eleven the reader could
#: not see.
#:
#: Everything downstream of the ladder now derives from this. `apps/api` is a
#: separate deployment and cannot import it, so `ComparablesRequest.limit`
#: carries the same number and `test_one_comp_set.py` asserts the two agree by
#: parsing both files — a cross-deployment constant has no other way to be one
#: number.
#:
#: 15 rather than another number because it is what the API already defaulted
#: to, so this changes no search. It was never chosen — `git log -S` puts it
#: in commit 202 of 202, the squashed base — but it is in production and
#: changing what the ladder returns is a different decision from making the
#: document honest about what it returned.
COMP_SET_MAX = 15

#: How many comp cards fit on the Sales Comparables page. MEASURED, NOT
#: CHOSEN: the card is 1.8in of map plus a body, four fill the page with 101px
#: to spare, and a fifth needs about 330px. Measured in Chromium at the real
#: page size rather than estimated.
#:
#: This is why `[:4]` was in every template and why nothing told the prose
#: that computes the analysis note about it. The rest of the set is not
#: dropped now — it carries over to `comparables_all`, which is a list and
#: fits fifteen on one page with 189px to spare at larger type than the
#: cards' own stat grid.
CARDS_PER_COMPARABLES_PAGE = 4

#: Not listed on the contents page: the cover (the reader is holding it) and
#: the contents page itself.
#:
#: `comparables_all` IS listed, deliberately. It is a page of the document a
#: reader may want to turn to — it is the evidence behind the range — and
#: omitting it from the contents would be the same omission D-159 is about,
#: one level up.
CONTENTS_OMITS = ("cover", "contents")


def _analysis_columns(sorted_by_price):
    """Low / Medium / High for the Area Sales Analysis table. (D-119)

    THREE FAILURES IN FOUR LINES, and they shared one cause: three fixed
    slots indexed into a list of any length, with nothing checking that the
    three came out distinct or that the reader was told how many there were.

    1. **It silently dropped comps.** For four comps the old code took index
       0, `len // 2` = 2, and -1 — so index 1 was in no column, while the
       chart directly above the table drew all four. Nothing on the page said
       three of four.
    2. **"Medium" was not a median.** `len // 2` on a price-sorted list of
       four is the THIRD-cheapest. The column labelled Medium sat at $631,500
       against a true median of $610,750.
    3. **It collapsed silently below three comps.** At n=2, `low` and `med`
       and `high` resolved to indices 0, 1, 1 — one listing filling two
       columns, presented as two. At n=1 the same listing filled all three.
       At n=0 `extract_comp_stats({})` returned a full row of zeros and the
       table rendered `0 0 0 0` throughout.

    THE RULE HERE, STATED SO IT CAN BE OVERRULED CHEAPLY. No listing appears
    in more than one column; a column with no distinct listing is blank; and
    the note says how many comps the summary was drawn from, so a reader can
    see that three columns is a summary rather than the set.

        n = 0   nothing, and the note says so
        n = 1   Medium only — the median of one element is that element, and
                a Low and a High imply a spread that does not exist
        n = 2   Low and High — that IS the spread; no median of two
        n >= 3  Low = cheapest, Medium = LOWER median, High = dearest

    Lower median, `(n - 1) // 2`, rather than nearest-to-the-true-median:
    on an even-length list the two middle listings are equidistant from the
    median price BY CONSTRUCTION, so "nearest" has no answer and would be
    decided by sort stability. `(n - 1) // 2` is the conventional lower
    median and is the same listing every time.
    """
    n = len(sorted_by_price)
    if n == 0:
        return {}, {}, {}, "No comparable sales were found for this property."
    if n == 1:
        return {}, sorted_by_price[0], {}, (
            "One comparable sale. A low/median/high spread needs at least two, "
            "so the single sale is shown under Median.")
    if n == 2:
        return sorted_by_price[0], {}, sorted_by_price[1], (
            "Two comparable sales, shown as the low and the high. Two sales "
            "have no median.")
    low, high = sorted_by_price[0], sorted_by_price[-1]
    med = sorted_by_price[(n - 1) // 2]
    return low, med, high, (
        f"Low, median and high of {n} comparable sales. The table summarises "
        f"the spread; every one of the {n} appears on the Sales Comparables "
        f"page.")


def paginate(page_set):
    """`(page_numbers, contents_keys)` for one report's final page set. (D-121)

    THE CONTENTS PAGE AND THE PAGE FOOTERS WERE BOTH HARDCODED, AND DISAGREED
    WITH EACH OTHER AND WITH THE DOCUMENT. Every theme printed `03` on both
    the overview page and the aerial page; contents claimed Market Trends at
    page 07 in reports that contain no Market Trends page; the literals skip
    `03` even when nothing is dropped. Three symptoms, one cause — two
    independent hand-maintained copies of a number that is a property of the
    render.

    Both now come from here, so they cannot drift from each other: a theme
    reads `page_numbers[key]` for its footer and loops `contents_keys` for its
    contents rows. The number is the physical sheet index, 1-based and
    counting the cover, because that is what a reader turning to page 7 is
    counting.

    `page_set` is membership, not sequence — see `PAGE_ORDER`.
    """
    rendered = [key for key in PAGE_ORDER if key in page_set]
    page_numbers = {key: n for n, key in enumerate(rendered, start=1)}
    contents_keys = [k for k in rendered if k not in CONTENTS_OMITS]
    return page_numbers, contents_keys


# Both re-exported from `theme_registry`, which reads `themes.json`. They were
# literals here until the cut to three themes; the pairing is stated once now
# because five copies of it existed and two disagreed on every id (D-163).
# Kept as module-level names because twelve test files and six scripts import
# them from here.
THEME_TEMPLATES = _registry.THEME_TEMPLATES
THEME_NUMBER_MAP = _registry.THEME_NUMBER_MAP
DEFAULT_THEME_ID = _registry.DEFAULT_THEME_ID
DEFAULT_THEME_NAME = _registry.DEFAULT_THEME_NAME

# Configuration from environment
ASSETS_BASE_URL = os.getenv("ASSETS_BASE_URL", "https://assets.trendyreports.com")
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
logger.warning("[DIAGNOSTIC] property_builder loaded at startup")
logger.warning("[DIAGNOSTIC] GOOGLE_MAPS_API_KEY present: %s, length: %d", bool(GOOGLE_MAPS_API_KEY), len(GOOGLE_MAPS_API_KEY))
logger.warning("[DIAGNOSTIC] OPENAI_API_KEY present: %s, length: %d", bool(OPENAI_API_KEY), len(OPENAI_API_KEY))
logger.warning("[DIAGNOSTIC] TEMPLATES_DIR: %s, exists: %s", TEMPLATES_DIR, TEMPLATES_DIR.exists())


#: What the report prints where it has no data. D-137: the alternative is a
#: DEFAULT, and a default in a property report is a claim. `pool or "No"` and
#: `tax_status or "Current"` asserted, with nothing behind either, that a
#: specific person's home has no pool and their taxes are paid — in the same
#: type and the same table as the APN and the legal description, which are
#: real. A dash says *we don't know*; those said *we checked*.
#:
#: Matches the spelling already used by zoning, garage, fireplace and the rest
#: of `_build_property_context`, so an unknown field looks the same wherever
#: it appears.
ABSENT = "-"


class PropertyReportBuilder:
    """
    Builds HTML property reports using the per-theme template system.

    The per-theme entry template (templates/property/<theme>/<theme>_report.jinja2,
    e.g. teal/teal_report.jinja2, extending _base/base.jinja2) handles:
    - Theme selection (numbers 1-5 mapped to bold/classic/elegant/modern/teal)
    - Page set configuration (default 7-page set, or custom via selected_pages)
    - Including all section templates
    
    Expected report_data structure:
    {
        "id": "uuid",
        "account_id": "uuid",
        "report_type": "seller" | "buyer",
        "theme": 1-5,
        "accent_color": "#0d294b",
        "language": "en" | "es",
        "page_set": "full" | "compact" | ["cover", "property_details", ...],
        
        # Property fields
        "property_address": "123 Main St",
        "property_city": "Los Angeles",
        "property_state": "CA",
        "property_zip": "90210",
        "property_county": "Los Angeles",
        "apn": "1234-567-890",
        "owner_name": "John Doe",
        "legal_description": "LOT 1 BLK 2...",
        "property_type": "Single Family",
        
        # SiteX data (full property details from property search)
        "sitex_data": { ... },
        
        # Comparables
        "comparables": [ ... ],
        
        # Agent info (from user join)
        "agent": {
            "name": "Jane Agent",
            "email": "jane@example.com",
            "phone": "555-1234",
            "photo_url": "https://...",
            "title": "Real Estate Agent",
            "license_number": "01234567",
            "company_name": "Acme Realty",
            "logo_url": "https://..."
        },
        
        # Branding (from affiliate_branding join, if applicable)
        "branding": {
            "display_name": "Acme Real Estate",
            "logo_url": "https://...",
            "primary_color": "#0d294b",
            "accent_color": "#2563eb"
        }
    }
    """
    
    def __init__(self, report_data: Dict[str, Any]):
        self.report_data = report_data
        self.report_type = report_data.get("report_type", "seller")
        self.accent_color = report_data.get("accent_color")
        self.language = report_data.get("language", "en")
        
        # Resolve theme: a name, an id, or the stringified id that
        # `report_generations.theme_id` (VARCHAR) hands back. The three-arm
        # if/elif this replaces did not accept the string form, so `"5"` fell
        # through to the default while looking like a choice (D-164).
        self.theme_name, self.theme_number = _registry.resolve(
            report_data.get("theme", DEFAULT_THEME_ID)
        )
        
        # Legacy compatibility: keep self.theme as the number
        self.theme = self.theme_number
        
        # Use selected_pages if provided, otherwise use default 7-page set
        # All unified templates use the same 7-page layout
        selected_pages = report_data.get("selected_pages")
        if selected_pages and isinstance(selected_pages, list) and len(selected_pages) > 0:
            self.page_set = selected_pages
        elif self.theme_name in self.V2_THEMES:
            # Six pages, not nine. `notes` is new and is NOT conditional —
            # it carries the agent panel and the disclaimers, so a report
            # without it is a report with no one to call and no statement
            # that it is not an appraisal.
            self.page_set = [p for p in self.V2_PAGE_ORDER]
        else:
            self.page_set = list(self.DEFAULT_PAGE_SET)

        #: D-142: pages the caller asked for that the render could not produce.
        #: Set by `render_html`; empty until then, never `None`, so a caller
        #: reading it does not have to know whether a render has happened.
        self.pages_dropped: List[str] = []
        
        # Initialize Jinja2 environment - single directory for all templates
        self.env = Environment(
            loader=FileSystemLoader(str(TEMPLATES_DIR)),
            autoescape=select_autoescape(['html', 'xml', 'jinja2']),
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # Add custom filters (shared with MarketReportBuilder via template_filters.py)
        self.env.filters['format_currency'] = _fmt_currency
        self.env.filters['format_currency_short'] = _fmt_currency_short
        self.env.filters['format_number'] = _fmt_number
        self.env.filters['format_measure'] = _fmt_measure
        self.env.filters['truncate'] = _truncate_fn
        
    @staticmethod
    def _format_currency(value: Any) -> str:
        """Format number as currency."""
        if value is None:
            return "N/A"
        try:
            return f"${int(float(value)):,}"
        except (ValueError, TypeError):
            return str(value)
    
    @staticmethod
    def _format_number(value: Any) -> str:
        """Format number with commas."""
        if value is None:
            return "N/A"
        try:
            return f"{int(float(value)):,}"
        except (ValueError, TypeError):
            return str(value)
    
    @staticmethod
    def _format_currency_short(value: Any) -> str:
        """Format as short currency: 470000 -> $470k, 1200000 -> $1.2M"""
        if value is None:
            return "-"
        try:
            val = float(value)
            if val >= 1_000_000:
                return f"${val/1_000_000:.1f}M"
            elif val >= 1_000:
                return f"${val/1_000:.0f}k"
            else:
                return f"${val:.0f}"
        except (ValueError, TypeError):
            return str(value)
    
    @staticmethod
    def _truncate(value: Any, length: int = 40, suffix: str = "...") -> str:
        """Truncate string to specified length."""
        if value is None:
            return ""
        text = str(value)
        if len(text) <= length:
            return text
        return text[:length - len(suffix)] + suffix
    
    def _build_property_context(self) -> Dict[str, Any]:
        """
        Build property context matching template requirements.
        
        Maps report_data fields to the expected 'property' object structure.
        Supports both old-style (street) and new V0 template (street_address) naming.
        """
        sitex_data = self.report_data.get("sitex_data") or {}
        
        # D-090. `or ""`, not `.get(k, "")`: these four are interpolated into
        # `full_address` below, so a NULL column does not stay invisible — it
        # becomes the string "None" in the middle of the address on the cover
        # of every theme. Measured: with `property_address=None`, all five
        # render "None, Test City, CA 90210".
        street = self.report_data.get("property_address") or ""
        city = self.report_data.get("property_city") or ""
        state = self.report_data.get("property_state") or ""
        zip_code = self.report_data.get("property_zip") or ""
        
        # Build full address string
        full_address = f"{street}, {city}, {state} {zip_code}".strip(", ")
        
        return {
            # Address (required) - both naming conventions for compatibility
            "street": street,
            "street_address": street,  # V0 template naming
            "city": city,
            "state": state,
            "zip_code": zip_code,
            "full_address": full_address,
            
            # Location for maps
            "latitude": sitex_data.get("latitude") or sitex_data.get("lat"),
            "longitude": sitex_data.get("longitude") or sitex_data.get("lng"),
            
            # Owner info
            # D-090: the trailing `.get(k, "")` in each of these `or` chains is
            # the last term, so when it returns None — key present, value NULL —
            # None is the result of the whole expression.
            # OWNER OF RECORD — AGENT PATH ONLY. D-116 removed this block from
            # every theme because it printed an assessor-roll name under a
            # heading calling the reader a "prospect", on a report anyone can
            # request for any address. It is back for the agent path only: an
            # agent running a report on a property knowingly is a different
            # context from a stranger who typed an address into a lead page.
            #
            # The templates gate on `audience`, and a rendered-output test
            # asserts these names appear in no consumer document. `audience`
            # defaults to "agent" because the agent path does not set it and a
            # new caller that forgets should get the OLD behaviour, not the
            # unguarded one — a default of "consumer" would silently strip the
            # block from a surface that is meant to have it.
            "owner_name": self.report_data.get("owner_name") or sitex_data.get("owner_name") or "",
            "secondary_owner": sitex_data.get("secondary_owner") or "-",
            "county": self.report_data.get("property_county") or sitex_data.get("county") or "",
            "apn": self.report_data.get("apn") or sitex_data.get("apn") or "",
            
            # Property details (numeric fields default to 0 for safe template arithmetic)
            "bedrooms": sitex_data.get("bedrooms") or 0,
            "bathrooms": sitex_data.get("bathrooms") or 0,
            "sqft": sitex_data.get("sqft") or 0,
            "lot_size": sitex_data.get("lot_size") or 0,
            "year_built": sitex_data.get("year_built") or 0,
            "garage": sitex_data.get("garage") or "-",
            "fireplace": sitex_data.get("fireplace") or "-",
            # D-137. Was `or "No"`. `pool` is produced by NEITHER SiteX's
            # model nor the wizard's payload (D-135), so the default was the
            # only path and every report stated the home has no pool.
            "pool": sitex_data.get("pool") or ABSENT,
            "total_rooms": sitex_data.get("total_rooms") or "-",
            "num_units": sitex_data.get("num_units") or "-",
            "units": sitex_data.get("num_units") or "-",  # V0 template naming
            "zoning": sitex_data.get("zoning") or "-",
            "property_type": self.report_data.get("property_type") or sitex_data.get("property_type") or "",
            "use_code": sitex_data.get("use_code") or "-",
            
            # Last recorded sale (D-118). Kept as raw values here; the
            # analysis table's preformatted cell is built in
            # _build_stats_context, which is where the comps' cells are built.
            "last_sale_price": sitex_data.get("last_sale_price"),
            "last_sale_date": sitex_data.get("last_sale_date"),
            "last_sale_price_per_sqft": sitex_data.get("last_sale_price_per_sqft"),

            # Tax/Assessment
            #
            # D-135/D-137: `or 0` ON MONEY. Every one of these is printed
            # `| format_currency`, and `format_currency(0)` is **"$0"** — a
            # number, not a gap. The same house rendered `$337,378` of land
            # when the worker looked it up through SiteX and **$0** when the
            # wizard supplied the data, because `land_value` and
            # `improvement_value` are in SiteX's 28 keys and not in the
            # wizard's 25. Same property, two reports, different numbers,
            # decided by which code path created it.
            #
            # `$0` of land is a claim about a parcel. `0%` improved is a claim
            # about a building. `None` renders "N/A" through the same filter,
            # which is D-118's precedent for exactly this — an unknown figure
            # says it is unknown.
            #
            # NOTE, not silently unified: this document now spells absence two
            # ways, "N/A" from `format_currency(None)` and "-" from `ABSENT`.
            # Both are honest; they are not the same word. One for the design
            # handover rather than a change made in passing.
            "assessed_value": sitex_data.get("assessed_value"),
            "tax_amount": sitex_data.get("tax_amount"),
            "land_value": sitex_data.get("land_value"),
            "improvement_value": sitex_data.get("improvement_value"),
            "percent_improved": sitex_data.get("percent_improved") or ABSENT,
            "improvement_pct": sitex_data.get("percent_improved") or ABSENT,  # V0 template naming
            # D-137. Was `or "Current"` — an assertion about a stranger's
            # property taxes, on a field no producer writes.
            "tax_status": sitex_data.get("tax_status") or ABSENT,
            "tax_rate_area": sitex_data.get("tax_rate_area") or "-",
            "tax_year": sitex_data.get("tax_year") or "-",
            
            # Legal
            "legal_description": self.report_data.get("legal_description") or sitex_data.get("legal_description") or "",
            "mailing_address": sitex_data.get("mailing_address") or "",
            "census_tract": sitex_data.get("census_tract") or "-",
            "housing_tract": sitex_data.get("housing_tract") or "-",
            "lot_number": sitex_data.get("lot_number") or "-",
            "page_grid": sitex_data.get("page_grid") or "-",
            "partial_bath": sitex_data.get("partial_bath") or 0,
            "notes": sitex_data.get("notes") or "",
        }
    
    def _build_agent_context(self) -> Dict[str, Any]:
        """
        Build agent context matching template requirements.
        Supports both old-style and new V0 template naming conventions.
        """
        agent = self.report_data.get("agent") or {}
        branding = self.report_data.get("branding") or {}
        
        # Build full agent address
        agent_street = agent.get("company_address") or agent.get("street") or ""
        agent_city = agent.get("company_city") or agent.get("city") or ""
        agent_state = agent.get("company_state") or agent.get("state") or ""
        agent_zip = agent.get("company_zip") or agent.get("zip_code") or ""
        agent_address = f"{agent_street}, {agent_city}, {agent_state} {agent_zip}".strip(", ")
        
        # Format license number for display
        license_num = agent.get("license_number")
        license_display = f"CA BRE#{license_num}" if license_num else ""
        
        # D-090 — THE SAME CONSTRUCT THE COMMENT BELOW DESCRIBES, ON FIVE LINES
        # THAT DID NOT GET IT.
        #
        # `agent.get(k, "")` returns None when the key EXISTS holding None,
        # because the default only applies to a missing key. These values come
        # from a database row, where a nullable column with no value is exactly
        # that case. `title` was hardened for it (D-066/D-067) and the lines
        # around it were left alone, so with a NULL phone the teal, classic and
        # modern reports rendered
        #
        #     ☎ None     ✉ None
        #
        # in the agent block of a customer-facing PDF. §0.6 says to grep for the
        # CONSTRUCT rather than the symptom and re-run the check after the fix;
        # this is what that rule is for, found two tickets later by a test that
        # passed None instead of omitting the key.
        #
        # `or ""` rather than `.get(k, "")` throughout: it collapses missing,
        # None and empty-string to one renderable value, which is what every
        # template's `{% if agent.phone %}` already assumes.
        return {
            "name": agent.get("name") or "",
            # `or` rather than a .get() default: the key can exist holding None,
            # which .get() happily returns and which rendered as the literal
            # string "None" in the PDF. Not "Realtor®" — see D-066.
            #
            # `.strip()` before the `or`, because a whitespace-only title is
            # truthy and sailed straight through: every theme rendered a blank
            # line in cover-sized type where the agent's role belongs. That was
            # the one part of D-067 that turned out to be reachable — the "None"
            # leak it was filed for is not, because this line runs first.
            "title": (agent.get("title") or "").strip() or "Real Estate Agent",
            "license_number": license_num,
            "license": license_display,  # V0 template naming (formatted)
            "phone": agent.get("phone") or "",
            "email": agent.get("email") or "",
            "company_name": agent.get("company_name") or branding.get("display_name") or "",
            "street": agent_street,
            "city": agent_city,
            "state": agent_state,
            "zip_code": agent_zip,
            "address": agent_address,  # V0 template expects full address string
            "photo_url": safe_url(agent.get("photo_url")) or None,
            "logo_url": safe_url(agent.get("logo_url") or branding.get("logo_url")) or None,
            # Standalone template fields (with safe defaults in templates)
            "company_short": agent.get("company_short") or (
                (agent.get("company_name") or "TR")[:2].upper()
            ),
            "company_tagline": agent.get("company_tagline") or "",
        }
    
    def _build_comparables_context(self) -> List[Dict[str, Any]]:
        """
        Build comparables list matching template requirements.
        
        Each comparable should have:
        - address, latitude, longitude
        - image_url, map_image_url (optional)
        - price/sale_price, days_on_market, distance/distance_miles
        - sqft, price_per_sqft
        - bedrooms, bathrooms, year_built
        - lot_size, pool, sold_date
        
        Handles field name variations from different sources:
        - Frontend sends: lat/lng, photo_url, distance_miles
        - SimplyRETS sends: latitude/longitude, photos, etc.
        """
        raw_comps = self.report_data.get("comparables") or []
        logger.info("_build_comparables_context: %d raw comps received", len(raw_comps))

        comparables = []
        # D-159: was `[:6]`, with a comment saying "3 rows of 2" — a layout
        # that had not existed for as long as the templates had said `[:4]`,
        # so the cap was dead and the four the reader saw were chosen by the
        # templates. The whole set is built now; the SPLIT across pages is the
        # templates' business, the SIZE of the set is this constant's.
        for comp in raw_comps[:COMP_SET_MAX]:
            # Handle field name variations from different sources
            # Frontend: lat/lng, Backend: latitude/longitude
            latitude = comp.get("latitude") or comp.get("lat")
            longitude = comp.get("longitude") or comp.get("lng")
            
            # Frontend: photo_url, Backend: image_url or photos array
            image_url = (
                comp.get("image_url") or 
                comp.get("photo_url") or 
                (comp.get("photos", [None])[0] if comp.get("photos") else None)
            )
            logger.warning(
                "[DIAGNOSTIC] Comp %s: photo_url=%s, map_image_url=%s, resolved_image=%s",
                comp.get("address", "?")[:30],
                bool(comp.get("photo_url")),
                bool(comp.get("map_image_url")),
                bool(image_url),
            )

            # Frontend: distance_miles, Backend: distance
            distance_raw = comp.get("distance") or comp.get("distance_miles", "")
            distance_formatted = distance_raw
            if distance_raw and isinstance(distance_raw, (int, float)):
                distance_formatted = f"{distance_raw:.1f} mi"
            
            # Get raw price for stats calculations
            raw_price = comp.get("price") or comp.get("close_price") or comp.get("sale_price") or comp.get("list_price")
            
            # Generate map URL if we have coordinates
            map_image_url = comp.get("map_image_url")
            if not map_image_url and latitude and longitude and GOOGLE_MAPS_API_KEY:
                map_image_url = (
                    f"https://maps.googleapis.com/maps/api/staticmap"
                    f"?center={latitude},{longitude}"
                    f"&zoom=16&size=400x200&maptype=roadmap"
                    f"&markers={latitude},{longitude}"
                    f"&key={GOOGLE_MAPS_API_KEY}"
                )
            
            # Ensure raw_price is numeric
            try:
                raw_price_num = float(raw_price) if raw_price else 0
            except (ValueError, TypeError):
                raw_price_num = 0

            comp_sqft = comp.get("sqft") or comp.get("area") or 0
            try:
                comp_sqft = float(comp_sqft)
            except (ValueError, TypeError):
                comp_sqft = 0

            # ── Status & dates ──────────────────────────────────────────────
            status = comp.get("status") or "Active"
            list_date_raw = comp.get("list_date") or ""
            sold_date_raw = comp.get("sold_date") or comp.get("close_date") or ""

            # Display date: active/pending → list_date; closed → sold/close_date
            is_active = status.lower() in ("active", "pending")
            display_date = self._fmt_date(list_date_raw if is_active else sold_date_raw)
            display_date_label = "Listed" if is_active else "Sold"
            # D-118, per comp rather than per report: a card headed "Sale
            # Price" over an active listing is showing the asking price.
            # `_extract_price` returns list_price for those. Sits beside
            # `sold_date_label` because it is the same distinction.
            price_label = "List Price" if is_active else "Sale Price"

            resolved_addr = comp.get("address") or comp.get("full_address", "")

            comparables.append({
                "address": resolved_addr,
                "latitude": latitude,
                "longitude": longitude,
                "image_url": safe_url(image_url) or None,
                "photo_url": safe_url(image_url) or None,  # V0 template field (prefer property photo)
                "map_image_url": safe_url(map_image_url) or None,  # Fallback satellite thumbnail
                "price": self._format_price(raw_price),  # Formatted string
                "sale_price": raw_price_num,  # V0 template (raw number for filter/arithmetic)
                "list_price": float(comp.get("list_price") or 0),
                # Dates
                "sold_date": display_date,           # Formatted display date (may be list_date for active)
                "sold_date_label": display_date_label,  # "Listed" or "Sold"
                "price_label": price_label,            # "Sale Price" or "List Price"
                "list_date": self._fmt_date(list_date_raw),
                "status": status,
                "days_on_market": comp.get("days_on_market") or comp.get("dom") or 0,
                "distance": distance_formatted,
                "distance_miles": float(distance_raw) if isinstance(distance_raw, (int, float)) else 0,
                "sqft": comp_sqft,
                "price_per_sqft": self._calc_price_per_sqft(raw_price, comp_sqft) or 0,
                "bedrooms": comp.get("bedrooms") or 0,
                "bathrooms": comp.get("bathrooms") or 0,
                "year_built": comp.get("year_built") or 0,
                "lot_size": comp.get("lot_size") or 0,
                "lot_display": comp.get("lot_display") or "",
                "hoa_fee": comp.get("hoa_fee"),
                "hoa_frequency": comp.get("hoa_frequency") or "",
                # D-137, tri-state: True / False / None. The old expression
                # collapsed absent into False via `comp.get("pool", "No")`,
                # so every comp card read "Pool: No". No producer writes
                # `pool` on a comp — not the API's projection, not the
                # wizard's payload — so that was every card, always.
                "pool": _tri_state_bool(comp.get("pool")),
            })
        
        logger.info("_build_comparables_context: returning %d processed comps", len(comparables))
        return comparables
    
    #: The comparable-sale window, in days. Jerry, 2026-09-29: six months.
    #: The API sends `minclosedate` for the same number
    #: (routes/property.COMP_CLOSE_WINDOW_DAYS) and re-filters client-side.
    #: Two deployments, so the constant cannot be shared; a test asserts the
    #: two agree, because a query window and a printed window that drift apart
    #: IS D-117.
    COMP_CLOSE_WINDOW_DAYS = 180

    #: The windows the API's comp ladder can search, smallest first
    #: (routes/property.COMP_CLOSE_WINDOW_DAYS and COMP_FALLBACK_WINDOW_DAYS).
    COMP_WINDOW_BUCKETS_MONTHS = (6, 12)

    @classmethod
    def _window_months(cls, comps) -> int:
        """The window that actually covers these comps, not the one hoped for.

        D-132 gives the API a seventh ladder level that widens the search to
        twelve months when six returns under three sales. The page must then
        say twelve, or it is D-117 again one level up — a stated window the
        query did not use.

        It is DERIVED from the comps rather than plumbed through, and that is
        deliberate. The alternative is carrying the window from the API
        response through the wizard, the create payload, the
        `property_reports` row and into `report_data` — four hops, each of
        which can drop it, for a number that is already implied by the data.
        Deriving it also survives a report being regenerated later or its
        comps being edited by hand, where a stored window would go stale.

        Rounded UP to the ladder's own buckets rather than reported exactly,
        because "sales in the past 7 months" invites the question of why
        seven, and the honest answer is that six is the window and this is the
        fallback.
        """
        oldest = 0
        today = date.today()
        for c in comps:
            raw = c.get("close_date") or c.get("sold_date") or ""
            try:
                closed = date.fromisoformat(str(raw)[:10])
            except (ValueError, TypeError):
                continue
            oldest = max(oldest, (today - closed).days)
        for bucket in cls.COMP_WINDOW_BUCKETS_MONTHS:
            if oldest <= bucket * 31:
                return bucket
        # Older than any window the ladder searches — legacy rows, or comps
        # edited by hand. Report what is actually there rather than a bucket
        # that would understate it.
        return max(cls.COMP_WINDOW_BUCKETS_MONTHS[-1], -(-oldest // 31))

    def _comps_window(self) -> Dict[str, str]:
        """What the report may truthfully say about the comps it is carrying.

        D-117 was two failures, not one. The query filtered on no date while
        every theme printed "the last 12 months" — and separately, the wizard
        defaults to ACTIVE listings (property-wizard.tsx:53), so a report could
        head a list of homes currently for sale with "SALES IN THE PAST 12
        MONTHS". Correcting 12 to 6 fixes the first and makes the second worse,
        by stating a wrong thing more precisely.

        So the copy is derived from what the comps actually are, using the same
        active/closed distinction `_build_comparables_context` already applies
        per comp. The page describes its contents rather than asserting a
        window somebody hoped for.

        `price_row` is the analysis table's price-row heading, and it is here
        for the same reason: over active listings, `_extract_price` returns
        `list_price`, so a row headed "Sale Price" is showing what sellers are
        asking. Same defect as the subtitle, one row lower down. (D-118.)
        """
        comps = self.report_data.get("comparables") or []
        months = self._window_months(comps)

        def _closed(c):
            status = str(c.get("status") or "Active").lower()
            return status not in ("active", "pending")

        closed = sum(1 for c in comps if _closed(c))
        active = len(comps) - closed

        if not comps:
            # D-108's empty state, on this surface. Falling through to the
            # mixed wording would head an empty table "RECENT SALES AND
            # CURRENT LISTINGS", which is a claim about nothing.
            return {
                "label": "No comparable properties found",
                "subtitle": "NO COMPARABLE PROPERTIES FOUND",
                "pill": "No results",
                "price_row": "Price",
                "note": (
                    "No comparable properties matched this home's "
                    "characteristics in the search area. Widening the radius or "
                    "the square-footage tolerance may return results."
                ),
            }

        if comps and not active:
            return {
                "label": f"Sales in the past {months} months",
                "subtitle": f"SALES IN THE PAST {months} MONTHS",
                "pill": f"Last {months} months",
                "price_row": "Sale Price",
                "note": (
                    f"The above statistics represent average property details for "
                    f"comparable homes sold within the last {months} months. The price "
                    f"range indicates the low and high sale prices for properties "
                    f"matching your home's characteristics."
                ),
            }
        if comps and not closed:
            return {
                "label": "Comparable homes currently for sale",
                "subtitle": "COMPARABLE HOMES CURRENTLY FOR SALE",
                "pill": "Active listings",
                "price_row": "List Price",
                "note": (
                    "The above statistics represent average property details for "
                    "comparable homes currently listed for sale. The price range "
                    "indicates the low and high asking prices for properties "
                    "matching your home's characteristics. These homes have not sold, "
                    "so the figures are what sellers are asking rather than what "
                    "buyers have paid."
                ),
            }
        return {
            "label": f"Recent sales and current listings",
            "subtitle": "RECENT SALES AND CURRENT LISTINGS",
            "pill": f"Last {months} months",
            "price_row": "Price",
            "note": (
                f"The above statistics combine comparable homes sold within the last "
                f"{months} months with comparable homes currently listed for sale. "
                f"The price range therefore mixes sale prices with asking prices."
            ),
        }

    def _price_with_date(self, price, iso_date=None) -> str:
        """`$369,000 · Dec 2015`, or `$470,000`, or `N/A`. (D-118)"""
        if price is None:
            return "N/A"
        shown = _fmt_currency(price)
        when = self._fmt_date(iso_date) if iso_date else ""
        # A literal middle dot, not `&middot;`. These templates render with
        # autoescape ON, so an entity would print as `&amp;middot;`.
        return f"{shown} \u00b7 {when}" if when else shown

    def _format_price(self, price: Any) -> str:
        """Format price for display."""
        if price is None:
            return "N/A"
        try:
            return f"${int(float(price)):,}"
        except (ValueError, TypeError):
            return str(price)
    
    def _calc_price_per_sqft(self, price: Any, sqft: Any) -> Optional[int]:
        """Calculate price per square foot."""
        try:
            if price and sqft:
                return int(float(price) / float(sqft))
        except (ValueError, TypeError, ZeroDivisionError):
            pass
        return None

    def _fmt_date(self, date_str: Any) -> str:
        """
        Format an ISO date string for display on comparable cards.

        Examples:
          '2024-03-15T00:00:00Z'  →  'Mar 2024'
          '2024-03-15'            →  'Mar 2024'
          None / ''               →  ''
        """
        if not date_str:
            return ""
        try:
            from datetime import datetime as _dt
            raw = str(date_str).split("T")[0]   # strip time component
            return _dt.strptime(raw, "%Y-%m-%d").strftime("%b %Y")
        except (ValueError, AttributeError):
            # Graceful fallback: return first 10 chars (keeps YYYY-MM-DD readable)
            return str(date_str)[:10]

    # D-136 — `_build_neighborhood_context` and `_build_area_analysis_context`
    # WERE HERE, AND THEY INVENTED DEMOGRAPHICS. Deleted 2026-10-01.
    #
    #     "female_ratio": neighborhood.get("female_ratio", "51.5"),
    #     "male_ratio":   neighborhood.get("male_ratio",   "48.5"),
    #     "avg_beds":     neighborhood.get("avg_beds",     "3"),
    #     "area_min_radius": area.get("area_min_radius", "0.1 mi"),
    #
    # They read `sitex_data["neighborhood"]` and `sitex_data["area_analysis"]`,
    # and neither key is written by either producer of that blob (D-135) — so
    # the defaults were not defaults, they were the only path. Forty-one
    # fields of made-up figures, built on every render.
    #
    # NO REPORT EVER PRINTED ONE, which is why this was FRAGILE and not WRONG,
    # and checked again before deleting rather than taken from the entry: no
    # template in the repository references `neighborhood.<field>` or
    # `area_analysis.<field>`. Every "neighborhood" in the templates is prose
    # about an aerial photograph.
    #
    # Deleted rather than sourced because the gun was loaded and pointed at a
    # page nobody has written yet: the contexts sat in `render_html`'s dict
    # under plausible names, and the first person to add a "Neighborhood" page
    # would have wired up `51.5% female / 48.5% male` for a census tract
    # nobody looked at. Sourcing them is a feature with a data supplier behind
    # it; keeping them until then is a trap with a default value in it.
    #
    # `test_no_invented_demographics.py` fails if either name comes back.

    @staticmethod
    def _extract_price(comp: Dict) -> Optional[float]:
        """Extract a numeric price from a comp dict, checking all known field names."""
        for key in ("price", "close_price", "sale_price", "list_price", "sold_price"):
            val = comp.get(key)
            if val is not None and val != "" and val != "-":
                try:
                    fval = float(val)
                    if fval > 0:
                        return fval
                except (ValueError, TypeError):
                    continue
        return None

    def _build_range_of_sales_context(self) -> Dict[str, Any]:
        """
        Build range of sales context from comparables.
        """
        comparables = self.report_data.get("comparables") or []
        
        if not comparables:
            return {}
        
        prices = []
        sqfts = []
        beds = []
        baths = []
        
        for comp in comparables:
            price_val = self._extract_price(comp)
            if price_val is not None:
                prices.append(price_val)
            if comp.get("sqft"):
                try:
                    sqfts.append(float(comp.get("sqft")))
                except (ValueError, TypeError):
                    pass
            if comp.get("bedrooms"):
                try:
                    beds.append(int(comp.get("bedrooms")))
                except (ValueError, TypeError):
                    pass
            if comp.get("bathrooms"):
                try:
                    baths.append(float(comp.get("bathrooms")))
                except (ValueError, TypeError):
                    pass
        
        return {
            "total_comps": len(comparables),
            "avg_sqft": f"{int(sum(sqfts)/len(sqfts)):,}" if sqfts else "",
            "avg_beds": round(sum(beds)/len(beds)) if beds else "",
            "avg_baths": round(sum(baths)/len(baths)) if baths else "",
            "price_min": str(int(min(prices)/1000)) if prices else "",
            "price_max": str(int(max(prices)/1000)) if prices else "",
        }
    
    def _build_stats_context(self) -> Dict[str, Any]:
        """
        Build stats context for V0 Teal template.
        
        Creates the stats object with piq (property in question), low, medium, high
        sub-objects for the Area Sales Analysis table.
        """
        comparables = self.report_data.get("comparables") or []
        sitex_data = self.report_data.get("sitex_data") or {}
        
        # Calculate statistics from comparables
        prices = []
        sqfts = []
        beds = []
        baths = []
        years = []
        lots = []
        distances = []
        
        days_on_market = []
        
        for comp in comparables:
            price_val = self._extract_price(comp)
            if price_val is not None:
                prices.append(price_val)
            sqft_val = comp.get("sqft") or comp.get("living_area") or comp.get("area")
            if sqft_val:
                try:
                    sqfts.append(float(sqft_val))
                except (ValueError, TypeError):
                    pass
            if comp.get("bedrooms"):
                try:
                    beds.append(int(comp.get("bedrooms")))
                except (ValueError, TypeError):
                    pass
            if comp.get("bathrooms"):
                try:
                    baths.append(float(comp.get("bathrooms")))
                except (ValueError, TypeError):
                    pass
            if comp.get("year_built"):
                try:
                    years.append(int(comp.get("year_built")))
                except (ValueError, TypeError):
                    pass
            if comp.get("lot_size"):
                try:
                    lots.append(float(comp.get("lot_size")))
                except (ValueError, TypeError):
                    pass
            dist = comp.get("distance_miles") or comp.get("distance")
            if dist and isinstance(dist, (int, float)):
                distances.append(float(dist))
            dom = comp.get("days_on_market")
            if dom is not None:
                try:
                    days_on_market.append(int(dom))
                except (ValueError, TypeError):
                    pass

        logger.info("_build_stats_context: %d prices, %d sqfts from %d comps", len(prices), len(sqfts), len(comparables))
        
        # Sort comparables by price to get low/medium/high
        sorted_by_price = sorted(
            [c for c in comparables if self._extract_price(c) is not None],
            key=lambda x: self._extract_price(x) or 0
        )
        
        low_comp, med_comp, high_comp, analysis_note = _analysis_columns(sorted_by_price)
        
        def _safe_num(val, default=0):
            """Convert value to a number, returning default for None/'-'/non-numeric."""
            if val is None or val == "-" or val == "":
                return default
            try:
                return float(val)
            except (ValueError, TypeError):
                return default

        def extract_comp_stats(comp):
            # D-119: an EMPTY column is empty, not a row of zeros. `{}` is
            # what `_analysis_columns` returns for a column with no distinct
            # listing behind it — two comps have no median, one has no
            # spread — and the old code ran it through `_safe_num(..., 0)`
            # field by field, so the table printed `0` for the distance,
            # `$0` for the price and `0` for the year built of a property
            # that does not exist. Same rule as D-137: absent is absent.
            # `format_currency` and `format_number` both pass `-` through
            # unchanged, checked rather than assumed.
            if not comp:
                return {k: ABSENT for k in (
                    "distance", "sqft", "price_per_sqft", "year_built",
                    "lot_size", "bedrooms", "bathrooms", "stories", "pools",
                    "price", "price_display")}
            raw_price = self._extract_price(comp) or 0
            sqft = comp.get("sqft") or comp.get("living_area") or comp.get("area")
            # D-125: THE NUMBERS STAY NUMBERS HERE. `format_measure` is applied
            # in the templates, which is where presentation belongs — and,
            # more to the point, formatting them here made an audit quieter.
            # `numeric_leaf_names()` walks these contexts to derive which
            # fields are numeric, and a field whose value is the STRING
            # "1949" is not numeric, so seven names dropped out and the
            # zero-conditional audit silently stopped covering them. That is
            # D-119's own postmortem, repeated two entries later, in the
            # function that postmortem is written inside.
            return {
                "distance": _safe_num(comp.get("distance_miles") or comp.get("distance"), 0),
                "sqft": _safe_num(sqft, 0),
                "price_per_sqft": _safe_num(self._calc_price_per_sqft(raw_price, sqft), 0),
                "year_built": _safe_num(comp.get("year_built"), 0),
                "lot_size": _safe_num(comp.get("lot_size"), 0),
                "bedrooms": _safe_num(comp.get("bedrooms"), 0),
                "bathrooms": _safe_num(comp.get("bathrooms"), 0),
                # D-120/D-137: a house with zero storeys is not a thing, and
                # a pool count of 0 on an unwritten field is the same claim as
                # "No" one table up. Display strings, because the template
                # prints these raw and Jinja's `default` does not fire on None.
                "stories": _safe_num(comp.get("stories"), 0)
                           if comp.get("stories") is not None else ABSENT,
                "pools": ABSENT if _tri_state_bool(comp.get("pool")) is None
                         else int(_tri_state_bool(comp.get("pool"))),
                "price": _safe_num(raw_price, 0),
                # Same key as the subject so the template is one expression.
                # No date: the comps' dates are already a column on the Sales
                # Comparables page, and repeating four of them here would
                # crowd a row whose point is the price spread.
                "price_display": self._price_with_date(_safe_num(raw_price, 0), None),
            }
        
        # Property in question stats (from sitex_data)
        #
        # D-118. THIS ROW USED TO SHOW THE COUNTY'S PROP 13 ASSESSMENT:
        #
        #     est_value = (sitex_data.get("estimated_value")
        #                  or sitex_data.get("assessed_value") or 0)
        #
        # `estimated_value` is written by nothing anywhere in the repository,
        # so the fallback was not a fallback — it was the only path, and every
        # report printed a 1970s-reassessment figure in a row headed "Sale
        # Price" beside real closed sales 50% higher. A seller reading that
        # anchors low.
        #
        # Jerry, 2026-09-29: the row carries the LAST ACTUAL SALE, and where
        # the feed has none it shows nothing rather than a substitute. Whether
        # any feed carries one is open (D-118 / D-134, settled by
        # scripts/probe_sitex_sale_history.py). The removal is correct under
        # every outcome of that probe, so it does not wait for it.
        #
        # `None`, not `0`: zero is a price. `format_currency(None)` renders
        # "N/A", which is what an unknown sale price is.
        #
        # RESOLVED 2026-09-30: the probe found SiteX carries it after all, in
        # `SaleLoanInfo`, and the parser had never read it. The row now shows
        # the LAST RECORDED SALE — for the measurement's subject, $369,000 in
        # December 2015. That is also the $369,000 nobody could account for in
        # Group A of the six reviewed PDFs: real data, by a path the current
        # code stopped taking.
        #
        # `estimated_value` stays in the chain and stays first. It is still
        # written by nothing (D-133), and D-134 will decide what computes it;
        # when it does, a derived estimate should outrank a ten-year-old sale.
        last_sale = sitex_data.get("last_sale_price")
        vendor_ppsf = sitex_data.get("last_sale_price_per_sqft")
        est_value = sitex_data.get("estimated_value")

        if est_value is not None:
            # A value we computed. Its ratio has to be computed too — SiteX's
            # PricePerSQFT belongs to SiteX's sale price, not to ours.
            piq_price, piq_ppsf = est_value, _safe_num(
                self._calc_price_per_sqft(est_value, sitex_data.get("sqft")), 0)
        elif last_sale is not None:
            # SiteX's own figure. Use SiteX's own ratio rather than dividing:
            # theirs is computed against the sqft recorded with the SALE, which
            # can differ from PropertyCharacteristics after an addition, and a
            # row that disagrees with itself is worse than one that is a little
            # stale.
            piq_price = _safe_num(last_sale, 0)
            piq_ppsf = (_safe_num(vendor_ppsf, 0) if vendor_ppsf is not None
                        else _safe_num(self._calc_price_per_sqft(
                            last_sale, sitex_data.get("sqft")), 0))
        else:
            piq_price, piq_ppsf = None, None

        piq = {
            "distance": 0,
            "sqft": _safe_num(sitex_data.get("sqft"), 0),
            "price_per_sqft": piq_ppsf,
            "year_built": _safe_num(sitex_data.get("year_built"), 0),
            "lot_size": _safe_num(sitex_data.get("lot_size"), 0),
            "bedrooms": _safe_num(sitex_data.get("bedrooms"), 0),
            "bathrooms": _safe_num(sitex_data.get("bathrooms"), 0),
            "stories": _safe_num(sitex_data.get("stories"), 0)
                       if sitex_data.get("stories") is not None else ABSENT,
            "pools": ABSENT if _tri_state_bool(sitex_data.get("pool")) is None
                     else int(_tri_state_bool(sitex_data.get("pool"))),
            "price": piq_price,
            # The subject's cell carries the sale's DATE as well as its figure.
            # Without it a 2015 sale reads as a current valuation sitting 25%
            # below four recent comps, which is the same anchoring harm the
            # assessment did — a true number presented as answering a question
            # it does not answer.
            "price_display": self._price_with_date(
                piq_price,
                sitex_data.get("last_sale_date") if est_value is None else None,
            ),
        }
        
        # Calculate avg price per sqft across all comps
        avg_price_per_sqft = 0
        if prices and sqfts and len(prices) == len(sqfts):
            ppsf_values = [p / s for p, s in zip(prices, sqfts) if s > 0]
            avg_price_per_sqft = int(sum(ppsf_values) / len(ppsf_values)) if ppsf_values else 0
        elif prices and sqfts:
            avg_price_per_sqft = int((sum(prices) / len(prices)) / (sum(sqfts) / len(sqfts))) if sqfts else 0
        
        return {
            "total_comps": len(comparables),
            "avg_sqft": int(sum(sqfts)/len(sqfts)) if sqfts else 0,
            "avg_beds": round(sum(beds)/len(beds)) if beds else 0,
            "avg_baths": round(sum(baths)/len(baths)) if baths else 0,
            "avg_price_per_sqft": avg_price_per_sqft,
            "avg_days_on_market": int(sum(days_on_market)/len(days_on_market)) if days_on_market else None,
            "active_listings": None,  # Populated if available from MLS data
            "max_distance": round(max(distances), 1) if distances else None,
            "price_low": min(prices) if prices else 0,
            "price_high": max(prices) if prices else 0,
            "piq": piq,
            "low": extract_comp_stats(low_comp),
            "medium": extract_comp_stats(med_comp),
            "high": extract_comp_stats(high_comp),
            # D-119: what this table is a summary OF. A three-column table
            # beside a four-bar chart, with nothing saying three of four are
            # shown, reads as the whole set.
            "analysis_note": analysis_note,
        }
    
    @staticmethod
    def _geocode_address(address: str) -> tuple:
        """
        Geocode an address via Google Maps Geocoding API.
        Returns (lat, lng) or (None, None) on failure.
        """
        if not address or not GOOGLE_MAPS_API_KEY:
            return None, None
        try:
            import httpx
            resp = httpx.get(
                "https://maps.googleapis.com/maps/api/geocode/json",
                params={"address": address, "key": GOOGLE_MAPS_API_KEY},
                timeout=10.0,
            )
            data = resp.json()
            if data.get("status") == "OK" and data.get("results"):
                loc = data["results"][0]["geometry"]["location"]
                logger.warning("[DIAGNOSTIC] Geocoded '%s' → %s, %s", address[:50], loc["lat"], loc["lng"])
                return loc["lat"], loc["lng"]
            logger.warning("[DIAGNOSTIC] Geocode failed for '%s': %s", address[:50], data.get("status"))
        except Exception as e:
            logger.warning("[DIAGNOSTIC] Geocode error: %s", e)
        return None, None

    def _build_images_context(self) -> Dict[str, Any]:
        """
        Build images context for V0 Teal template.

        Hero image priority:
          1. Explicitly stored cover_image_url (user-uploaded or pre-set)
          2. Google Street View static image based on lat/lng (auto fallback)
          3. None → template shows placeholder gradient

        Aerial map: Google Static Maps roadmap with property pin.
        """
        sitex_data = self.report_data.get("sitex_data") or {}
        lat = sitex_data.get("latitude") or sitex_data.get("lat") or None
        lng = sitex_data.get("longitude") or sitex_data.get("lng") or None

        # SiteX often returns 0/0 when it has no coordinates — treat as missing
        if lat is not None and lng is not None and float(lat) == 0 and float(lng) == 0:
            lat, lng = None, None

        # Fallback: geocode the address if we have no coordinates
        if (lat is None or lng is None) and GOOGLE_MAPS_API_KEY:
            prop = self._build_property_context()
            full_addr = prop.get("full_address") or ""
            if full_addr:
                lat, lng = self._geocode_address(full_addr)

        logger.warning("[DIAGNOSTIC] _build_images_context: lat=%s, lng=%s", lat, lng)
        logger.warning("[DIAGNOSTIC] GOOGLE_MAPS_API_KEY truthy: %s", bool(GOOGLE_MAPS_API_KEY))

        # --- Hero / Cover image -------------------------------------------
        hero = self.report_data.get("cover_image_url")
        if not hero and lat and lng and GOOGLE_MAPS_API_KEY:
            hero = (
                f"https://maps.googleapis.com/maps/api/streetview"
                f"?size=1200x800"
                f"&location={lat},{lng}"
                f"&fov=90&pitch=0"
                f"&key={GOOGLE_MAPS_API_KEY}"
            )

        # --- Aerial / neighbourhood map -----------------------------------
        aerial_map = None
        if lat and lng and GOOGLE_MAPS_API_KEY:
            aerial_map = (
                f"https://maps.googleapis.com/maps/api/staticmap"
                f"?center={lat},{lng}"
                f"&zoom=15&size=800x600&maptype=roadmap"
                f"&markers={lat},{lng}"
                f"&key={GOOGLE_MAPS_API_KEY}"
            )
            logger.warning("[DIAGNOSTIC] aerial_map URL generated: %s", aerial_map[:80])
        else:
            logger.warning(
                "[DIAGNOSTIC] aerial_map SKIPPED — lat:%s lng:%s key:%s",
                bool(lat), bool(lng), bool(GOOGLE_MAPS_API_KEY),
            )

        logger.warning("[DIAGNOSTIC] hero image: %s", "SET" if hero else "NONE")
        return {
            "hero": hero,
            "aerial_map": aerial_map,
        }
    
    # Per-theme default accent colours (must match the CSS defaults inside
    # each standalone *_report.jinja2 template).
    #: One entry per live theme. `teal` (#34d1c3) and `classic` (#1B365D)
    #: left with the cut. Teal's is still the platform default accent in
    #: `consumer_report_data.DEFAULT_THEME_ACCENT`, where it is a colour
    #: rather than a theme — a lead page with no brand colour needs one, and
    #: changing what strangers see was not part of the theme cut.
    _THEME_DEFAULT_COLORS = {
        "modern":  "#FF6B5B",
        "bold":    "#15216E",
        "elegant": "#1a1a1a",
    }

    # Per-theme dark background colour — used by compute_color_roles() to
    # guarantee the "on_dark" variant has enough contrast.
    #: The dark surface each theme's own templates paint. One entry per live
    #: theme; `teal` (#18235c) and `classic` (#1B365D) left with the cut.
    #:
    #: The `.get(..., "#18235c")` fallback below still names teal's navy. It
    #: is kept on purpose: `theme_registry.resolve` guarantees `theme_name` is
    #: a live theme, so the fallback is unreachable, and the colour is the
    #: platform default dark that the market reports and the six picker
    #: presets are all measured against — not a theme's private value.
    _THEME_DARK_BG = {
        "modern":  "#1A1F36",  # --midnight
        "bold":    "#15216E",  # --navy
        "elegant": "#1a1a1a",  # --charcoal
    }

    def _get_theme_color(self) -> str:
        """
        Get the theme color, preferring wizard accent over branding primary.
        Falls back to the theme's built-in default so CSS variables are
        never rendered as the literal string ``None``.
        """
        branding = self.report_data.get("branding") or {}
        accent = self.accent_color
        branding_primary = branding.get("primary_color")
        theme_default = self._THEME_DEFAULT_COLORS.get(self.theme_name, "#34d1c3")

        logger.warning(
            "[DIAGNOSTIC] _get_theme_color: accent_color=%s, branding_primary=%s, theme_default=%s",
            accent, branding_primary, theme_default,
        )

        result = accent or branding_primary or theme_default
        logger.warning("[DIAGNOSTIC] _get_theme_color result: %s", result)
        return result
    
    def _build_default_content_sections(self) -> Dict[str, Any]:
        """
        Build default content sections for text-heavy pages.
        Templates have built-in defaults, but we can override here if needed.
        """
        return {
            # Use template defaults for these sections
            "introduction": {},
            "roadmap": {
                "points": [{"title": None, "sub_title": None}] * 7  # 7 points required
            },
            "promise": {
                "points": [{"title": None, "content": None}] * 6  # 6 points required
            },
            "how_buyers_find": {},
            "pricing": {},
            "avg_days": {},
            "marketing_online": {},
            "marketing_print": {},
            "marketing_social": {},
            "analyze_optimize": {},
            "negotiating": {},
            "transaction": {},
        }
    

    # ── The redesigned document (Design's 2026-10-05 package) ─────────────
    #
    # Everything below serves `_v2/report.jinja2`, the one page architecture
    # that replaces the per-theme templates. It is ADDITIVE: elegant and modern
    # still render their old self-contained files and never see these keys, so
    # one theme can go end to end without the other two moving.
    #
    # The design's own logic class (`Property Report.dc.html`) computes these
    # values in JavaScript. Every number here is the same computation; where it
    # differs it is because the design was working from invented sample data
    # and the real context has an absence the sample did not.

    #: Pages, in order. `market_trends` is conditional and `notes` is new.
    #: `overview`, `contents`, `aerial` and `analysis` are gone — aerial is a
    #: photo plate on page 2 and analysis folded into the range page.
    V2_PAGE_ORDER = ("cover", "property", "comparables", "range",
                     "market_trends", "notes")

    #: THE MIGRATION SEAM, and it is temporary by construction.
    #:
    #: Design's package replaces nine pages with six. That is a BUILDER-level
    #: change — the page set is shared — so migrating one theme at a time
    #: means the default page set has to depend on which architecture the
    #: theme renders. A theme in this set gets `V2_PAGE_ORDER`; a theme
    #: outside it keeps `DEFAULT_PAGE_SET` and its own self-contained
    #: template.
    #:
    #: Without this, wiring bold would have silently taken `contents`,
    #: `aerial` and `analysis` away from elegant and modern — three pages
    #: those two templates still render and three gates still assert on.
    #:
    #: DELETE THIS, and the branch below it, when the set is all three
    #: themes. `test_the_migration_seam_is_still_needed` fails when it is,
    #: so the seam cannot outlive its reason the way an excuse in an
    #: allowed-list does.
    V2_THEMES = frozenset({"bold"})

    #: The nine-page set the un-migrated themes render.
    DEFAULT_PAGE_SET = ["cover", "contents", "aerial", "property", "analysis",
                        "comparables", "range"]

    #: The two conditional pages of the nine-page architecture. The agent
    #: wizard's default leaves them out — an agent picks pages — and the
    #: consumer path includes them, because a stranger picks nothing and
    #: should get everything the data supports.
    CONDITIONAL_PAGES = ["market_trends", "overview"]

    @classmethod
    def default_page_set(cls, theme, consumer: bool = False) -> List[str]:
        """The pages this theme's architecture renders, as a MAXIMUM.

        The one producer. `consumer_report_data.CONSUMER_PAGES` was a second
        copy of the nine-page list, written before the architecture could
        differ by theme — so the consumer path handed bold a `selected_pages`
        containing `contents`, `aerial`, `analysis` and `overview`, which the
        six-page architecture does not render, and NOT containing `notes`,
        which it always does.

        The visible failure was a four-page consumer report with no agent
        panel and no disclaimer. It was caught by a test asserting the page
        COUNT, not by anything looking at the list — and the list is where
        the mistake was.

        `consumer` exists because the two paths have DIFFERENT maxima on the
        nine-page architecture: 7 for the agent, 9 for the consumer. Writing
        one function and discovering that was the second half of the same
        mistake — the first version returned the agent's set for both and
        reported "7 pages, expected 9". The six-page architecture has one
        maximum for both, because `overview` is a panel on the cover rather
        than a page and `market_trends` is in the order already.
        """
        name, _ = _registry.resolve(theme)
        if name in cls.V2_THEMES:
            return list(cls.V2_PAGE_ORDER)
        pages = list(cls.DEFAULT_PAGE_SET)
        if consumer:
            pages += list(cls.CONDITIONAL_PAGES)
        return pages

    #: The nearest N comps get a photo. All of them appear in "Each sale".
    V2_COMPS_PICTURED = 6

    #: Cover title size by street-address length. The box is a fixed 78px with
    #: `overflow: hidden`, so the ladder is what keeps a long address inside it
    #: rather than silently clipping (§3.3, and the same failure the market
    #: masthead had).
    V2_TITLE_LADDER = ((18, 64), (24, 54), (30, 46), (38, 38))
    V2_TITLE_MIN_PX = 32

    #: The one dark surface on the document. `primary_on_dark` is guaranteed
    #: against this and nothing else, which is why there is only one.
    V2_DARK = "#0f172a"

    #: Fields with no producer anywhere in the pipeline. They are named in the
    #: "Not on record" strip rather than shown as empty rows — the owner's
    #: choice on the nineteen orphans (JERRY_PROPERTY_FIELDS_DECISION.md).
    V2_NO_PRODUCER = ("Fireplace", "Total rooms", "Use code", "Census tract",
                      "Neighborhood", "School district", "Elementary",
                      "Middle", "High school")

    #: Comp fields where `0` cannot be a real value, so a zero IS an absence.
    #:
    #: `_build_comparables_context` writes `comp.get(k) or 0` for seven numeric
    #: fields, so by the time a template sees them an absent bedroom count and
    #: a zero bedroom count are the same number (D-168). For these five the
    #: distinction is recoverable, because no house has zero bedrooms, zero
    #: bathrooms, zero living area, year built zero or a zero price per sq ft.
    #:
    #: `days_on_market` is NOT on this list and cannot be: 0 days on market is
    #: a real value and the design renders it "New". A comp with no DOM is
    #: indistinguishable from one that sold the day it listed, and nothing
    #: downstream can recover it. That is the half of D-168 this cannot fix.
    #: `distance_miles` is on the list because `_build_comparables_context`
    #: writes `float(distance_raw) if isinstance(...) else 0` — a comp with no
    #: distance becomes one at the subject's own address. 0 is not a real
    #: distance for a comparable: the subject is not its own comp.
    V2_ZERO_IS_ABSENT = ("bedrooms", "bathrooms", "sqft", "year_built",
                         "price_per_sqft", "lot_size", "distance_miles")

    @classmethod
    def _v2_comp_value(cls, comp: Dict[str, Any], key: str):
        """A comp field, with a recoverable zero read back as absence."""
        value = comp.get(key)
        if key in cls.V2_ZERO_IS_ABSENT:
            try:
                if value is not None and float(value) == 0:
                    return None
            except (TypeError, ValueError):
                return None
        return value

    @staticmethod
    def _v2_dash(value: Any) -> bool:
        """Is this value absent, in the sense the document means by a dash?

        `0` IS present — a studio has zero bedrooms, a new listing has zero
        days on market, and an HOA-free home has a zero fee. The absence rules
        turn on exactly this distinction (§3.6), so it is one function rather
        than a `{% if %}` repeated per row, which is how the zero-conditional
        sweep found the first batch.
        """
        return value is None or value == "" or value == ABSENT

    #: Rows whose value is too long for one nowrap line.
    V2_WRAPPING_ROWS = ("Legal description",)

    def _v2_row(self, label: str, value: Any, fmt=None) -> Dict[str, Any]:
        """One label/value row, carrying its own absence state.

        The weight and colour travel with the row because the design makes the
        dash visually quieter than a value (400 / #5E636B against 600 /
        #14161A). Deciding that in the template would need the same
        `_v2_dash` test in three places.
        """
        absent = self._v2_dash(value)
        return {
            "label": label,
            "value": ABSENT if absent else (fmt(value) if fmt else str(value)),
            "absent": absent,
            "wrap": label in self.V2_WRAPPING_ROWS and not absent,
        }

    def _v2_title_size(self, street: str) -> int:
        for limit, size in self.V2_TITLE_LADDER:
            if len(street or "") <= limit:
                return size
        return self.V2_TITLE_MIN_PX

    @staticmethod
    def _v2_short_money(value: Any) -> str:
        """`$641K` / `$1.24M`. The range headline is 60px and must not wrap."""
        try:
            v = float(value)
        except (TypeError, ValueError):
            return ABSENT
        if abs(v) >= 1_000_000:
            return f"${v / 1_000_000:.2f}".rstrip("0").rstrip(".") + "M"
        return f"${round(v / 1000):,.0f}K"

    def _v2_closed_prices(self, comps: List[Dict[str, Any]]) -> List[float]:
        """Closed sales only, ascending.

        THE RANGE IS CLOSED-ONLY AND THE OLD ONE WAS NOT. `stats.price_low` /
        `price_high` are computed over every comp the builder returns,
        including pending and active listings — an asking price, which is a
        hope, sitting in a range the document calls "what recent sales
        support". Design made this explicit (§4) and it is a behaviour change,
        not a layout one, so it is computed separately here and the old keys
        are left alone for the two themes still rendering them.
        """
        out = []
        for c in comps:
            if str(c.get("status") or "").strip().lower() not in ("closed", "sold"):
                continue
            price = c.get("sale_price") if c.get("sale_price") else c.get("price")
            try:
                out.append(float(price))
            except (TypeError, ValueError):
                continue
        return sorted(out)

    @staticmethod
    def _v2_median(values: List[float]) -> Optional[float]:
        """Upper median, matching the design's `a[floor(len/2)]`.

        NOT the mean of the two middle values: on an even-length set that
        produces a price no comparable sold at, in a cell the reader can check
        against the list below it.
        """
        return values[len(values) // 2] if values else None

    def _build_v2_context(self, context: Dict[str, Any], page_set: List[str]) -> Dict[str, Any]:
        """The redesigned document's own context, computed from the shared one.

        Takes the already-built `context` rather than rebuilding anything, so
        there is exactly one producer for every property fact and this layer
        can only ever re-present them. That is the D-139 lesson: a second
        assembly of the same data is a second place for a field to go missing.
        """
        prop = context["property"]
        agent = context["agent"]
        stats = context["stats"]
        comps = list(context["comparables"])
        consumer = context["audience"] != "agent"

        street = prop.get("street_address") or prop.get("street") or ""
        city = prop.get("city") or ""
        state = prop.get("state") or ""
        zip_code = prop.get("zip_code") or ""
        city_line = ", ".join(x for x in (city, " ".join(
            y for y in (state, zip_code) if y)) if x)

        # ── the cover's four stat cells ──────────────────────────────────
        # Candidates in priority order; the first four that are KNOWN render.
        # Bathrooms is absent on a real market's rows often enough that the
        # design made the row drop and backfill rather than show a dash in
        # 30px type on the brand band.
        # `_fmt_measure` ON BATHROOMS, NOT `_fmt_number`. `format_number`
        # truncates to an integer, so 1.5 baths rendered "1" — a real half
        # bath erased on the cover of the document. That is D-125 exactly, in
        # new code, and the gate that caught it
        # (`test_numbers_read_as_numbers::test_a_genuine_half_survives`) is
        # the one D-125 left behind. `format_measure` keeps a genuine
        # fraction and drops a trailing `.0`.
        #
        # Bedrooms and year keep the integer formatter because a half bedroom
        # is not a thing and a fractional year is a parse error; sq ft and lot
        # keep it for the thousands separator, which `format_measure` does
        # not add.
        candidates = [
            ("Bedrooms", prop.get("bedrooms"),
             lambda v: "Studio" if float(v) == 0 else _fmt_number(v)),
            ("Bathrooms", prop.get("bathrooms"), _fmt_measure),
            ("Sq ft", prop.get("sqft"), _fmt_number),
            ("Built", prop.get("year_built"), lambda v: str(int(float(v)))),
            ("Lot sq ft", prop.get("lot_size"), _fmt_number),
        ]
        hero_stats = []
        for label, value, fmt in candidates:
            if self._v2_dash(value):
                continue
            try:
                hero_stats.append({"label": label, "value": fmt(value)})
            except (TypeError, ValueError):
                continue
            if len(hero_stats) == 4:
                break

        # ── page 2, the two detail groups ───────────────────────────────
        home_rows = [
            self._v2_row("Bedrooms", prop.get("bedrooms"),
                         lambda v: "Studio" if float(v) == 0 else _fmt_number(v)),
            self._v2_row("Bathrooms", prop.get("bathrooms"), _fmt_measure),
            self._v2_row("Living area", prop.get("sqft"),
                         lambda v: f"{_fmt_number(v)} sq ft"),
            self._v2_row("Lot size", prop.get("lot_size"),
                         lambda v: f"{_fmt_number(v)} sq ft"),
            self._v2_row("Year built", prop.get("year_built"),
                         lambda v: str(int(float(v)))),
            self._v2_row("Property type", prop.get("property_type")),
            self._v2_row("Stories", prop.get("stories")),
            # SiteX writes the STRING "None" for a house without one, and
            # writes nothing at all when it does not know — the distinction
            # D-137 is about. `_tri_state_bool` already keeps the three apart;
            # rendering `prop["pool"]` straight put the word "None" in a value
            # cell, which the design forbids because a reader cannot tell it
            # from a missing answer. That was the first render's output.
            self._v2_row(
                "Pool / spa",
                _tri_state_bool(prop.get("pool")),
                lambda v: "Yes" if v else "No",
            ),
        ]
        record_rows = []
        # D-116 / D-157: the owner of record is on the AGENT path only. Built
        # by not appending it, not by hiding it — the consumer context must not
        # carry the name at all, so a template edit cannot reveal it.
        if not consumer:
            owner = prop.get("owner_name")
            second = prop.get("secondary_owner")
            both = " & ".join(x for x in (owner, second)
                              if x and not self._v2_dash(x))
            record_rows.append(self._v2_row("Owner of record", both or None))
        record_rows += [
            self._v2_row("APN", prop.get("apn")),
            self._v2_row("County", prop.get("county")),
            # D-116: Jerry kept APN, county, LEGAL DESCRIPTION, tax and
            # assessment when the owner block came out. Design's table does
            # not list it, and leaving it off dropped a field the owner
            # decided to keep — caught by
            # `test_the_kept_parcel_fields_are_still_there`, which renders and
            # looks for the value rather than reading the template.
            self._v2_row("Legal description", prop.get("legal_description")),
            # `_fmt_date` on the date half: SiteX returns `2015-12-23` and
            # the row rendered it verbatim beside a formatted currency, which
            # is the one cell on the page carrying two different conventions.
            self._v2_row(
                "Last sale",
                None if self._v2_dash(prop.get("last_sale_price")) else (
                    prop.get("last_sale_price"), prop.get("last_sale_date")),
                lambda v: " · ".join(
                    x for x in (_fmt_currency(v[0]), self._fmt_date(v[1]))
                    if x and not self._v2_dash(x))),
            self._v2_row("Assessed value", prop.get("assessed_value"), _fmt_currency),
            self._v2_row(
                "Land / improvements",
                None if self._v2_dash(prop.get("land_value")) else (
                    prop.get("land_value"), prop.get("improvement_value")),
                lambda v: " / ".join(_fmt_currency(x) for x in v)),
            self._v2_row(
                "Annual tax",
                None if self._v2_dash(prop.get("tax_amount")) else (
                    prop.get("tax_amount"), prop.get("tax_year")),
                lambda v: " · ".join(
                    x for x in (_fmt_currency(v[0]), str(v[1]) if v[1] else "")
                    if x and not self._v2_dash(x))),
            self._v2_row("Tax status", prop.get("tax_status")),
            self._v2_row("Zoning", prop.get("zoning")),
            self._v2_row("Garage", prop.get("garage")),
        ]
        detail_groups = [
            {"title": "The home", "rows": home_rows},
            {"title": "Record & taxes", "rows": record_rows},
        ]
        unknown = [r["label"] for g in detail_groups for r in g["rows"] if r["absent"]]
        unknown += list(self.V2_NO_PRODUCER)

        # ── page 3, the pictured comps ──────────────────────────────────
        def _dist(c):
            try:
                return float(c.get("distance_miles"))
            except (TypeError, ValueError):
                return float("inf")

        pictured = sorted(comps, key=_dist)[: self.V2_COMPS_PICTURED]
        for c in pictured:
            # The bathrooms SEGMENT is omitted, not dashed: "3 bd · — ba ·
            # 1,590 sq ft" reads as a measurement of nothing. 301 rows of a
            # real market had no bathroom count.
            _beds = self._v2_comp_value(c, "bedrooms")
            _baths = self._v2_comp_value(c, "bathrooms")
            _sqft = self._v2_comp_value(c, "sqft")
            c["v2_specs"] = " · ".join(x for x in (
                None if self._v2_dash(_beds) else f"{_fmt_number(_beds)} bd",
                None if self._v2_dash(_baths) else f"{_fmt_measure(_baths)} ba",
                None if self._v2_dash(_sqft) else f"{_fmt_number(_sqft)} sq ft",
            ) if x)
            # THE MEASURED DISTANCE, not the producer's one-decimal display
            # string. `_build_comparables_context` writes
            # `f"{distance_raw:.1f} mi"`, so a comp 0.58 miles away renders
            # "0.6 mi" — and on the nine-page themes the exact value survives
            # in the analysis table's Distance row. Design's compare table has
            # no Distance row, so rounding here would be the only copy of the
            # number and 0.58 would be gone from the document.
            #
            # Caught by `test_numbers_read_as_numbers::test_a_genuine_half
            # _survives`, which asserts "0.58" appears SOMEWHERE — a gate on
            # the document rather than on a cell, which is why it survived the
            # table being replaced.
            _dist_raw = self._v2_comp_value(c, "distance_miles")
            c["v2_dist"] = (
                c.get("distance") or ABSENT if self._v2_dash(_dist_raw)
                else f"{_fmt_measure(_dist_raw)} mi"
            )
            _ppsf = self._v2_comp_value(c, "price_per_sqft")
            c["v2_ppsf"] = (
                ABSENT if self._v2_dash(_ppsf) else f"{_fmt_currency(_ppsf)} /sq ft")
            # `lot_display` is "" when absent and `lot_size` is 0, so both
            # halves of this need the absence test rather than a `or`.
            _lot = c.get("lot_display") or None
            if not _lot:
                _raw = self._v2_comp_value(c, "lot_size")
                _lot = None if self._v2_dash(_raw) else f"{_fmt_number(_raw)} sq ft"
            c["v2_lot"] = f"Lot {_lot}" if _lot else f"Lot {ABSENT}"
            c["v2_hoa"] = (
                "HOA —" if self._v2_dash(c.get("hoa_fee"))
                else "No HOA" if float(c["hoa_fee"]) == 0
                else f"HOA {_fmt_currency(c['hoa_fee'])}/{c.get('hoa_frequency') or 'mo'}"
            )
            closed = str(c.get("status") or "").strip().lower() in ("closed", "sold")
            c["v2_closed"] = closed
            # `sold_date_label` is the WORD ("Sold" / "Listed") and
            # `sold_date` is the formatted date — set as a pair by
            # `_build_comparables_context`. Reading the label as the date
            # rendered "Sold Sold" on every closed comp, which is what the
            # first render of this page actually produced.
            c["v2_when"] = (
                f"{c['sold_date_label']} {c['sold_date']}"
                if closed and c.get("sold_date") and c.get("sold_date_label")
                else f"{c.get('status') or 'Listed'} · listed {c.get('list_date')}"
                if c.get("list_date")
                else (c.get("status") or ABSENT)
            )

        closed_prices = self._v2_closed_prices(comps)
        low = closed_prices[0] if closed_prices else None
        high = closed_prices[-1] if closed_prices else None
        mid = self._v2_median(closed_prices)

        # ── page 4, the range band's fixed axis ─────────────────────────
        # THE AXIS MUST CONTAIN THE MARKER IT DRAWS, which the spec\'s
        # `floor(low x 0.92) .. ceil(high x 1.06)` does not guarantee.
        #
        # Design\'s sample has the subject\'s last sale ($612K in 2019) inside
        # the comp range. The production fixture does not: a 2015 sale at
        # $369,000 against closed comps of $470K-$635K puts the marker at
        # **-26%** of the axis — off the left edge of a band whose own label
        # says "your home\'s last recorded sale". A marker outside its own
        # axis is not a small visual defect; it is a value the document claims
        # to be showing and is not.
        #
        # Widened to include it rather than clamped, because clamping would
        # put the marker AT the low end and read as "your home sold at the
        # bottom of the range" — a false statement rather than a missing one.
        # This is a deliberate deviation from the written spec; see the report.
        axis_low = axis_high = None
        if low is not None and high is not None:
            axis_low = math.floor(low * 0.92 / 1000) * 1000
            axis_high = math.ceil(high * 1.06 / 1000) * 1000
            if not self._v2_dash(last_sale_in := prop.get("last_sale_price")):
                try:
                    subject = float(last_sale_in)
                    axis_low = min(axis_low, math.floor(subject * 0.98 / 1000) * 1000)
                    axis_high = max(axis_high, math.ceil(subject * 1.02 / 1000) * 1000)
                except (TypeError, ValueError):
                    pass

        def _pct(value):
            """Position on the fixed axis, as a CSS percentage.

            Returns None rather than 0 when the axis could not be computed, so
            a template cannot render a marker at the left edge and have it read
            as a real position.
            """
            if axis_low is None or value is None or axis_high == axis_low:
                return None
            return round((float(value) - axis_low) / (axis_high - axis_low) * 1000) / 10

        last_sale = prop.get("last_sale_price")
        last_sale_year = None
        if not self._v2_dash(prop.get("last_sale_date")):
            found = re.search(r"(19|20)\d{2}", str(prop["last_sale_date"]))
            last_sale_year = found.group(0) if found else None

        def _closed(key, cast=float):
            """Closed comps' values for one field, ascending, absences out.

            THROUGH `_v2_comp_value`, not `c.get(key)`. The producer collapses
            seven numeric comp fields to 0, so reading them raw put a column
            of 0/0/0 in the compare table for a field no comp carried — "every
            comparable was built in year zero". Caught by this file's own new
            gate on the first run, which is the half of writing a gate that
            usually gets skipped.
            """
            out = []
            for c in comps:
                if str(c.get("status") or "").strip().lower() not in ("closed", "sold"):
                    continue
                value = self._v2_comp_value(c, key)
                if self._v2_dash(value):
                    continue
                try:
                    out.append(cast(value))
                except (TypeError, ValueError):
                    continue
            return sorted(out)

        # `_v2_comp_value` on the sqft half for the same reason as `_closed`:
        # a comp with no living area has `sqft == 0`, and `p / 0` would raise
        # rather than be excluded. `if p and sq` happened to guard the raise
        # and not the absence.
        ppsf = sorted(
            p / sq for p, sq in (
                (c.get("sale_price") or c.get("price"),
                 self._v2_comp_value(c, "sqft")) for c in comps
                if str(c.get("status") or "").strip().lower() in ("closed", "sold"))
            if p and sq
        )
        subject_ppsf = None
        if not self._v2_dash(last_sale) and not self._v2_dash(prop.get("sqft")):
            try:
                subject_ppsf = float(last_sale) / float(prop["sqft"])
            except (TypeError, ValueError, ZeroDivisionError):
                subject_ppsf = None

        def _triple(values, fmt):
            if not values:
                return {"low": ABSENT, "mid": ABSENT, "high": ABSENT}
            return {"low": fmt(values[0]), "mid": fmt(self._v2_median(values)),
                    "high": fmt(values[-1])}

        _year = lambda v: str(int(float(v)))
        subject_sale = ABSENT
        if not self._v2_dash(last_sale):
            subject_sale = _fmt_currency(last_sale) + (
                f" ({last_sale_year})" if last_sale_year else "")
        compare_rows = [
            {"label": "Sale price", "subject": subject_sale,
             **_triple(closed_prices, _fmt_currency)},
            {"label": "Price per sq ft",
             "subject": ABSENT if subject_ppsf is None else (
                 _fmt_currency(subject_ppsf) + (f" ({last_sale_year})" if last_sale_year else "")),
             **_triple(ppsf, _fmt_currency)},
            {"label": "Living area",
             "subject": ABSENT if self._v2_dash(prop.get("sqft"))
                        else f"{_fmt_number(prop['sqft'])} sq ft",
             **_triple(_closed("sqft"), _fmt_number)},
            {"label": "Year built",
             "subject": ABSENT if self._v2_dash(prop.get("year_built"))
                        else _year(prop["year_built"]),
             **_triple(_closed("year_built"), _year)},
            {"label": "Bedrooms",
             "subject": ABSENT if self._v2_dash(prop.get("bedrooms"))
                        else _fmt_number(prop["bedrooms"]),
             **_triple(_closed("bedrooms"), _fmt_number)},
        ]

        bars = []
        bar_max = max((float(c.get("sale_price") or c.get("price") or 0)
                       for c in comps), default=0)
        for c in sorted(comps, key=lambda c: -float(c.get("sale_price") or c.get("price") or 0)):
            price = c.get("sale_price") or c.get("price")
            if self._v2_dash(price):
                continue
            closed = str(c.get("status") or "").strip().lower() in ("closed", "sold")
            bars.append({
                "address": (c.get("address") or ABSENT) + ("" if closed else " · pending"),
                "width": round(float(price) / bar_max * 100, 1) if bar_max else 0,
                "price": _fmt_currency(price),
            })

        # ── page 6, the agent panel ─────────────────────────────────────
        initials = "".join(w[0] for w in (agent.get("name") or "").split() if w)[:2].upper()

        grade = (context.get("comp_confidence_grade")
                 or self.report_data.get("comp_confidence_grade") or "A")
        reason = (context.get("comp_confidence_reason")
                  or self.report_data.get("comp_confidence_reason") or "")
        default_labels = {"A": "Strict match", "B": "Relaxed match",
                          "C": "Broad match", "D": "Thin market"}
        conf_label = reason if (grade in ("B", "C") and reason) else default_labels.get(grade, "")

        pictured_note = (
            f"nearest {self.V2_COMPS_PICTURED} pictured, all {len(comps)} on the next page"
            if len(comps) > self.V2_COMPS_PICTURED else "all pictured"
        )

        return {
            # type and radius come from the theme's own entry file
            "dark": self.V2_DARK,
            "pages": [p for p in self.V2_PAGE_ORDER if p in page_set],
            "consumer": consumer,
            "report_kind": "Home value report" if consumer else "Seller's report",
            "street": street,
            "city_line": city_line,
            "city_name": city,
            "title_size": self._v2_title_size(street),
            "hero_stats": hero_stats,
            "detail_groups": detail_groups,
            "unknown_list": " · ".join(unknown),
            "has_unknowns": bool(unknown),
            "pictured": pictured,
            "pictured_note": pictured_note,
            "comp_count": len(comps),
            # `stats.max_distance` is a bare number (0.6) and `_comps_window`
            # returns a DICT. The first render put `within 0.6` and the
            # repr of a five-key dict into the page — both because the
            # template reached for the context value rather than a sentence.
            "comp_radius": (
                ABSENT if self._v2_dash(stats.get("max_distance"))
                else f"{stats['max_distance']} mi"),
            "comp_window": (context.get("comps_window") or {}).get("pill") or ABSENT,
            "closed_count": len(closed_prices),
            "conf_grade": grade,
            "conf_label": conf_label,
            "range_low": self._v2_short_money(low),
            "range_high": self._v2_short_money(high),
            "range_mid": self._v2_short_money(mid),
            "axis_low": self._v2_short_money(axis_low),
            "axis_high": self._v2_short_money(axis_high),
            "band_left": _pct(low),
            "band_right": None if _pct(high) is None else round(100 - _pct(high), 1),
            "subject_x": _pct(last_sale),
            "last_sale_label": (
                ABSENT if self._v2_dash(last_sale) else
                _fmt_currency(last_sale) + (f" in {last_sale_year}" if last_sale_year else "")
            ),
            "compare_rows": compare_rows,
            "bars": bars,
            "bar_height": 14 if len(bars) > 8 else 22,
            "bar_gap": 5 if len(bars) > 8 else 10,
            "initials": initials,
            # `context["prepared_for"]`, NOT `report_data["requester_name"]`.
            # `build_consumer_report_data` reads the row's `requester_name`
            # and writes it out as `prepared_for`; reaching past that for the
            # raw key found nothing on the consumer path, and the cover
            # rendered the label over an empty name. Two producers for one
            # value is D-139's shape, and this is the version where the
            # second one is simply wrong.
            "prepared_for": (
                (context.get("prepared_for") or "").strip() if consumer
                else (context.get("prepared_for") or "").strip()
                     or (f"The owners of {street}" if street else "")
            ),
            "prepared_note": (
                f"Requested from {agent.get('company_name') or 'our'} home-value page"
                if consumer else
                f"Prepared at the request of {agent.get('name') or 'your agent'}"
            ),
            "agent_blurb": (
                "You asked what your home is worth. Here's what nearby sales say. "
                "When you're ready, I'll walk you through what a listing could look like."
                if consumer else
                "Happy to walk through this with you and talk about timing, pricing "
                f"and what buyers in {city or 'your area'} are looking for right now."
            ),
            "consumer_disclosure": (
                "Prepared for the person who requested it and addressed to them by "
                "name; it does not contain owner-of-record information."
                if consumer else ""
            ),
            "next_steps": [
                {"n": "1", "title": "A walkthrough",
                 "body": "20 minutes at the house so the range reflects your home, "
                         "not just the record."},
                {"n": "2", "title": "A pricing plan",
                 "body": "Where to list, and what the first two weeks should look like."},
                {"n": "3", "title": "A timeline",
                 "body": "When to prepare, when to go live, and what to expect at "
                         "each step."},
            ],
        }


    #: What a metric cell says when the metric has no producer or no data.
    #: Design §3.6: "Metric with no data -> 'no data'". NOT a dash, which this
    #: document uses for a property fact the public record is silent about —
    #: two different absences, and collapsing them would tell a reader the
    #: assessor does not know the city's median sale price.
    V2_NO_DATA = "no data"

    @staticmethod
    def _v2_delta(metric: Optional[Dict[str, Any]], suffix: str = "") -> str:
        """`▲ 4.2%` / `▼ 3`, or "" when the move is under 1%.

        Arrows are TEXT, never colour: a red number on a market page reads as
        a warning about the reader's house. Design §5 is explicit, and the
        existing market templates were already doing it this way.

        `change_pct` is signed and `direction` is the factual movement;
        `sentiment` is deliberately NOT read here — a falling days-on-market
        is good for a seller and still an arrow pointing down.
        """
        if not metric or metric.get("change_pct") is None:
            return ""
        change = metric["change_pct"]
        if abs(change) < 1:
            return ""
        arrow = "▲" if change > 0 else "▼"
        if suffix == "%":
            return f" · {arrow} {abs(change)}%"
        delta = metric.get("current")
        prior = metric.get("prior")
        if delta is None or prior is None:
            return f" · {arrow} {abs(change)}%"
        return f" · {arrow} {abs(round(delta - prior))}"

    def _build_v2_market(self, trends: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Design's page 5, from `fetch_and_compute_market_trends`.

        THREE OF THE FOUR STAT CELLS HAVE NO PRODUCER. `market_trends.py`
        imports `compute_price_cut_stats`, `compute_dom_distribution` and
        `compute_timeline_metrics` from `worker.report_builders`, where none of
        them is defined — the import raises every time and is swallowed by a
        bare `except (ImportError, Exception)` logging at `info`. So
        `price_cut_stats`, `dom_distribution` and `timeline_metrics` are
        always None, and have been since they were written. D-167.

        They are rendered as "no data" rather than omitted, because a cell
        that disappears is indistinguishable from a page that never had it —
        and a reader comparing two reports would see a different number of
        cells with nothing saying why.
        """
        if not trends:
            return None

        median = trends.get("median_sale_price") or {}
        timeline = trends.get("timeline_metrics") or {}
        dom = trends.get("dom_distribution") or {}
        cuts = trends.get("price_cut_stats") or {}

        def _cell(value, label):
            return {"value": self.V2_NO_DATA if value in (None, "") else value,
                    "label": label}

        marketing_days = timeline.get("avg_marketing_days")
        under_30 = dom.get("under_30")
        cut_rate = cuts.get("rate")
        median_cut = cuts.get("median_cut")

        stats = [
            # `_v2_short_money`, not `formatted_current`: the cell is 44px
            # display type in a four-column grid and "$660,000" is nine
            # glyphs. Design's own sample reads "$660K".
            _cell(None if median.get("current") is None
                  else self._v2_short_money(median["current"]),
                  "Median sale price" + self._v2_delta(median, "%")),
            _cell(None if marketing_days is None else str(round(marketing_days)),
                  "Days to contract" + self._v2_delta(trends.get("avg_days_on_market"))),
            _cell(None if under_30 is None else f"{round(under_30)}%",
                  "Sold in 30 days or less"),
            _cell(None if cut_rate is None else f"{round(cut_rate)}%",
                  "Took a price cut" + (
                      f" · median {_fmt_currency(median_cut)}" if median_cut else "")),
        ]

        # ── months of inventory ─────────────────────────────────────────
        moi = (trends.get("months_of_inventory") or {}).get("current")
        if moi is None:
            headline = "Inventory is not measurable here"
            note = ("There were not enough recent sales to work out how long "
                    "the homes for sale would take to sell.")
            cells = [False] * 8
        else:
            headline = ("It's a seller's market" if moi < 4
                        else "The market is balanced" if moi <= 6
                        else "Buyers have the edge")
            months = f"{moi:.1f}".rstrip("0").rstrip(".")
            note = (
                f"{months} months of inventory. At this pace every home for sale "
                f"in {self.report_data.get('property_city') or 'this area'} would "
                f"be gone in "
                + ("under three months." if moi < 3
                   else "under six months." if moi < 6
                   else "more than six months.")
            )
            # Eight cells, one a month. A market at 11 months fills all eight
            # rather than overflowing the grid — the cap is stated here
            # because the template cannot clamp what it is handed.
            filled = max(0, min(8, round(moi)))
            cells = [i < filled for i in range(8)]

        # ── the six-month chart ─────────────────────────────────────────
        series = trends.get("monthly_median")
        months_out, y_top, y_mid, y_bot = [], None, None, None
        if series:
            drawn = [p["value"] for p in series if p["value"] is not None]
            if drawn:
                top = max(drawn) * 1.06
                bottom = min(drawn) * 0.94
                # Rounded outward to a round $25K, so the axis labels are
                # numbers a person would write down.
                top = math.ceil(top / 25000) * 25000
                bottom = math.floor(bottom / 25000) * 25000
                span = top - bottom or 1
                y_top = self._v2_short_money(top)
                y_mid = self._v2_short_money((top + bottom) / 2)
                y_bot = self._v2_short_money(bottom)
                for point in series:
                    value = point["value"]
                    months_out.append({
                        "label": point["label"],
                        # A month with too few closings to have a median
                        # draws NO bar and says so, rather than a zero-height
                        # bar that reads as "nothing sold".
                        "value": self._v2_short_money(value) if value is not None
                                 else self.V2_NO_DATA,
                        "height": round((value - bottom) / span * 100, 1)
                                  if value is not None else 0,
                    })

        return {
            "window_label": trends.get("period_label") or "",
            "v2_stats": stats,
            "v2_moi_headline": headline,
            "v2_moi_note": note,
            "v2_moi_cells": cells,
            "v2_months": months_out,
            "v2_y_top": y_top,
            "v2_y_mid": y_mid,
            "v2_y_bot": y_bot,
        }

    def render_html(self) -> str:
        """
        Render the complete HTML report using the unified template system.
        
        All 5 themes use self-contained templates with the same data contract.
        
        Returns:
            Complete HTML string ready for PDF generation
        """
        # Determine theme color
        theme_color = self._get_theme_color()

        # ── Market Trends (optional page) ─────────────────────────────────
        # Only fetch if the page is actually selected — saves 3 API calls for
        # reports that don't include the Market Trends page.
        page_set = list(self.page_set)  # local copy so we can drop the page if data fails

        # D-142: WHAT WAS ASKED FOR, captured before the first drop.
        # `self.page_set` is the request; `page_set` below is what survives.
        # Taking the difference at the end needs the original, and the
        # original is destroyed one statement at a time by the two drops.
        requested_pages = list(page_set)

        # Allow callers (e.g. test scripts) to pre-inject data and skip the API call.
        market_trends_data = self.report_data.get("market_trends_data") or None

        if market_trends_data is None and "market_trends" in page_set:
            city     = self.report_data.get("property_city", "")
            zip_code = self.report_data.get("property_zip", "")
            state    = self.report_data.get("property_state", "")
            logger.info("market_trends: auto-fetching for city=%s, zip=%s, state=%s", city, zip_code, state)
            try:
                from worker.compute.market_trends import fetch_and_compute_market_trends
                market_trends_data = fetch_and_compute_market_trends(city, zip_code, state)
                logger.info("market_trends: fetch returned %s", "data" if market_trends_data else "None")
            except Exception as _mt_exc:
                logger.warning("market_trends: fetch FAILED — %s", _mt_exc)

        if market_trends_data is None and "market_trends" in page_set:
            page_set = [p for p in page_set if p != "market_trends"]
            logger.info("market_trends: page REMOVED from page_set (no data returned)")

        # ── Compute Color Roles ───────────────────────────────────────────
        dark_bg = self._THEME_DARK_BG.get(self.theme_name, "#18235c")
        color_roles = compute_color_roles(theme_color, dark_bg)

        # Build the unified context (same structure for all themes)
        context = {
            # Theme configuration
            "theme_number": self.theme_number,
            "theme_name": self.theme_name,
            "assets_base_url": ASSETS_BASE_URL,
            "google_maps_api_key": GOOGLE_MAPS_API_KEY,

            # Color roles (all templates can use any of these)
            **color_roles,
            
            # Page set (may have market_trends removed if data unavailable)
            "page_set": page_set,

            # WHO THIS DOCUMENT IS FOR, and it changes what may appear on it.
            # "agent" (the default, and what the agent path does not set) may
            # carry the owner of record; "consumer" may not, and is addressed
            # by the name the requester typed on the lead form instead.
            # Deliberate divergence between the two paths, which is new — the
            # last five (D-138…D-141) were all accidental convergence, so this
            # one is asserted on the rendered output rather than trusted.
            "audience": self.report_data.get("audience") or "agent",

            # D-159: the templates hold no comp-count literal any more. The
            # cards page takes this many and `comparables_all` takes the rest,
            # so the two cannot disagree about where the split is.
            "cards_per_comparables_page": CARDS_PER_COMPARABLES_PAGE,
            "prepared_for": (self.report_data.get("prepared_for") or "").strip(),

            # Market trends data (None when page was dropped)
            "market_trends": market_trends_data,
            
            # Property data
            "property": self._build_property_context(),
            
            # Agent data
            "agent": self._build_agent_context(),
            
            # Comparables
            "comparables": self._build_comparables_context(),

            # What the page may truthfully say about those comps (D-117)
            "comps_window": self._comps_window(),
            
            # Statistics (unified format for all themes)
            "stats": self._build_stats_context(),
            
            # Images
            "images": self._build_images_context(),
            
            # Legacy context (for any remaining old templates)
            "range_of_sales": self._build_range_of_sales_context(),
            
            # Content sections (use template defaults)
            **self._build_default_content_sections(),
            
            # Optional assets
            "cover_image_url": self.report_data.get("cover_image_url"),
        }

        # ── AI Executive Summary (optional page) ──────────────────────────
        overview_text = self.report_data.get("overview_text")  # allow pre-injection
        # THE NARRATIVE OUTLIVED THE PAGE IT WAS WRITTEN FOR.
        #
        # `overview` is a page in the nine-page set and a bounded panel on the
        # six-page one ("In short", four lines, `max-height: 81px`). Gating
        # generation on the PAGE being in the set left that panel empty on
        # every v2 render — the first bold render had `<p class="inshort-text">
        # </p>` and nothing failed, because an empty paragraph is valid HTML.
        #
        # `_wants_narrative` is the condition, not the page name.
        _wants_narrative = (
            "overview" in page_set or self.theme_name in self.V2_THEMES
        )
        if overview_text is None and _wants_narrative:
            try:
                from worker.ai_overview import generate_overview
                overview_text = generate_overview(
                    property_ctx=context["property"],
                    agent_ctx=context["agent"],
                    stats_ctx=context["stats"],
                    comparables=context["comparables"],
                    market_trends=market_trends_data,
                )
            except Exception as _ov_exc:
                logger.warning("ai_overview: generation failed — %s", _ov_exc)

        if overview_text is None and "overview" in page_set:
            page_set = [p for p in page_set if p != "overview"]
            context["page_set"] = page_set
            logger.info("ai_overview: page removed from page_set (no API key or generation failed)")
        elif overview_text is None and self.theme_name in self.V2_THEMES:
            # No page to drop — the panel is on the cover, and a cover is not
            # optional. It renders the one thing that is true without the
            # model, which is where the numbers came from. Said rather than
            # left blank: an empty panel reads as a rendering fault.
            logger.info("ai_overview: no narrative; the In short panel states the source")

        context["overview_text"] = overview_text or ""

        # ── The comparables continuation page (D-159) ─────────────────────
        # ADDED here, beside the two conditional drops and before `paginate`,
        # for the same reason they are here: the page set must be final before
        # a page number is computed from it. A report with four comps or fewer
        # does not get the page, because the cards already are the whole set.
        #
        # The DECISION lives here and only here. The templates render the page
        # when it is in the set and do not ask how many comps there are — one
        # place deciding, which is the whole of what D-159 was about.
        # NOT ON THE SHARED ARCHITECTURE. Design's page 4 lists every comp in
        # "Each sale" with a bar each, 15 of them at the compressed row height,
        # so there is nothing for a continuation page to continue. Adding it
        # anyway put `comparables_all` in the page set, then dropped it again
        # because `V2_PAGE_ORDER` has no such page — and the drop was reported
        # as a page the reader asked for and did not get (D-142), which is a
        # true statement about a page nobody asked for.
        _comps = context.get("comparables") or []
        _wants_continuation = (
            self.theme_name not in self.V2_THEMES
            and "comparables" in page_set
            and len(_comps) > CARDS_PER_COMPARABLES_PAGE
        )
        if _wants_continuation:
            page_set = page_set + ["comparables_all"]
            context["page_set"] = page_set
            logger.info(
                "comparables_all: page ADDED — %d comps, %d fit on the cards page",
                len(_comps), CARDS_PER_COMPARABLES_PAGE)

        # D-121: AFTER both conditional drops, never before. `market_trends`
        # and `overview` are removed above when their data did not arrive, and
        # a number computed before that is a number for a document that is not
        # the one being rendered — which is exactly how the hardcoded literals
        # came to claim Market Trends at page 07 of a report without one.
        page_numbers, contents_keys = paginate(page_set)
        context["page_numbers"] = page_numbers
        context["contents_keys"] = contents_keys

        # ── D-142: say that a page was dropped ────────────────────────────
        #
        # A report missing its market-trends page because SimplyRETS was down
        # was byte-for-byte the same document as one whose page set never
        # included it. Three readers, none of them served: the recipient saw
        # a shorter document with no explanation, the agent saw nothing at
        # all, and we had one `info` line per render in a log nobody reads
        # per-report.
        #
        # THIS IS THE HALF THAT NEEDS NO DECISION. Whether the document says
        # so, and whether the report row carries a column, are both open and
        # belong to Jerry and to Claude Design. What does not need deciding
        # is that the fact should be *computable in aggregate* — "market
        # trends failed on 40% of consumer reports last week" is the number
        # the entry says nobody can currently produce, and one structured
        # WARNING per affected render is enough to produce it.
        #
        # `warning`, not `info`: a page the customer asked for and did not
        # get is not routine, and the old line's level is half of why nobody
        # was reading it. Nothing is logged when nothing was dropped, so the
        # line's presence IS the signal.
        #
        # `pages_dropped` also goes in the context, so a theme can render it
        # the day that is decided, and on the builder, so `tasks.py` can
        # persist it the day a column exists. Neither is wired up here —
        # putting the value where both can reach it is the part that is
        # unambiguously ours.
        pages_dropped = [p for p in requested_pages if p not in page_set]
        context["pages_dropped"] = pages_dropped
        self.pages_dropped = pages_dropped
        if pages_dropped:
            logger.warning(
                "pages_dropped=%s requested=%d rendered=%d theme=%s — "
                "the reader is not told; D-142",
                ",".join(pages_dropped), len(requested_pages), len(page_set),
                self.theme_name,
            )

        # ── the redesigned document ──────────────────────────────────────
        # AFTER both conditional drops and the pagination, because `pages` is
        # derived from the final page set — the same reason D-121 put
        # `paginate` here. Additive: elegant and modern never read these keys.
        context.update(derive_theme(theme_color))
        context["doc"] = self._build_v2_context(context, page_set)
        # Merged onto the trends dict rather than nested beside it, so the
        # template reads one object and a page cannot render half of a market.
        _v2_market = self._build_v2_market(market_trends_data)
        if _v2_market and isinstance(context.get("market_trends"), dict):
            context["market_trends"] = {**context["market_trends"], **_v2_market}
        context["generated_label"] = date.today().strftime("%b %-d, %Y")

        logger.info("Final page_set: %s", page_set)
        logger.info("Pagination: %s", page_numbers)
        logger.info("Context comparables: %d, price_low: %s, price_high: %s",
            len(context.get("comparables", [])),
            context.get("stats", {}).get("price_low"),
            context.get("stats", {}).get("price_high"),
        )

        try:
            template_path = THEME_TEMPLATES.get(self.theme_name, THEME_TEMPLATES[DEFAULT_THEME_NAME])
            full_template_path = TEMPLATES_DIR / template_path
            logger.warning("[DIAGNOSTIC] Using template: %s, exists: %s", full_template_path, full_template_path.exists())

            # Verify the Jinja2 template contains the photo_url fix
            try:
                tmpl_content = full_template_path.read_text(encoding="utf-8")
                has_photo_fix = "comp.photo_url" in tmpl_content
                has_default_fallback = "default(comp.map_image_url)" in tmpl_content
                logger.warning(
                    "[DIAGNOSTIC] Template has photo_url ref: %s, has default(map) fallback: %s",
                    has_photo_fix, has_default_fallback,
                )
            except Exception as _tmpl_read_exc:
                logger.warning("[DIAGNOSTIC] Could not read template for inspection: %s", _tmpl_read_exc)

            # Log image context summary
            images_ctx = context.get("images", {})
            for key, val in images_ctx.items():
                logger.warning("[DIAGNOSTIC] Image %s: %s", key, str(val)[:100] if val else "NONE/EMPTY")

            template = self.env.get_template(template_path)
            # Every URL-shaped value is scheme-checked here, at the one place
            # a context can become HTML. See sanitize_context_urls.
            html = template.render(**sanitize_context_urls(context))
            
            logger.warning(
                "[DIAGNOSTIC] Rendered %s report: theme=%s (%s), pages=%s, html_len=%d",
                self.report_type, self.theme_name, self.theme_number, page_set, len(html),
            )
            return html
            
        except Exception as e:
            logger.error("Failed to render report with theme %s: %s", self.theme_name, e)
            raise
    
    def render_preview(self, pages: List[str] = None) -> str:
        """
        Render a preview with limited pages.
        
        Args:
            pages: List of page names to include (e.g., ["cover", "property_details"])
                   Defaults to first 3 pages.
        
        Returns:
            HTML string for preview
        """
        if pages is None:
            pages = ["cover", "property", "comparables"]
        
        # Temporarily override page_set
        original_page_set = self.page_set
        self.page_set = pages
        
        try:
            return self.render_html()
        finally:
            self.page_set = original_page_set
    
    def fetch_comparables(self) -> Optional[List[Dict[str, Any]]]:
        """
        Fetch comparables for the property if not already set.
        
        This method checks if comparables are already in report_data.
        If not, it could potentially fetch them from SimplyRETS based on
        the property address (but this is typically done at report creation time).
        
        Returns:
            List of comparable properties or None
        """
        # Check if comparables already exist in report data
        existing = self.report_data.get("comparables")
        if existing and isinstance(existing, list) and len(existing) > 0:
            logger.info(f"Using {len(existing)} existing comparables from report data")
            return existing
        
        # Comparables should be selected in the wizard and stored in the DB
        # If none exist, we can't fetch them here without the subject property coords
        logger.info("No comparables in report data - should be selected during report creation")
        return None
