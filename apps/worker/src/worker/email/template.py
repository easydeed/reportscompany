"""HTML email template for scheduled report notifications.

V15: Premium V0-inspired redesign matching React email previews.
- BRANDED: Hero metric in tinted card with Outfit font and gold accent bar
- BRANDED: Section labels with accent bar prefix (V0 SectionLabel component)
- BRANDED: AI Insight paragraph with left border in brand color
- BRANDED: Quick Take callout in accent-colored card with $ icon
- BRANDED: CTA button area in tinted background container
- BRANDED: Agent footer with branded bg, serif name, pill contact buttons
- BRANDED: Core Indicators with accent dots and serif numbers
- LAYOUT: Property Types + Price Tiers side-by-side with progress bars
- LAYOUT: Gallery count badge with branded pill + line separator
- GALLERY: Brand-tinted detail badges (Bed/Bath/SF) and serif prices
- TABLE: Brand-colored header row with white text + summary stats
- NEW: KPI card helpers with trend indicators for analytics layouts
- NEW: Year-over-Year comparison table helper with brand header
- TYPOGRAPHY: Outfit for hero metrics, key numbers, prices (modern geometric feel)

V10: Corporate/Professional redesign for Market Snapshot.
- REMOVED: Emojis from Quick Take, preheaders, and CTAs
- REMOVED: "Conversation Starter" green callout box (too casual)
- REDESIGNED: Quick Take now a subtle italic insight line (no yellow box)
- REDESIGNED: Key Stats Bar - clean bordered cards instead of gradient
- REDESIGNED: Headline metric uses neutral dark color instead of brand color
- REFINED: Core Indicators, Property Types, Price Tiers - cleaner borders
- PROFESSIONAL: All language updated to be data-focused and corporate
- SINGLE CTA: "View Full Report" button using brand primary color

V8: Adaptive gallery layouts for professional appearance.
- 3, 6, 9 listings → 3-column grid
- 2, 4 listings → 2-column grid
- 1, 5, 7, 8, 10+ listings → Vertical list (image left, info right)

V4: PDF-aligned redesign - email now mirrors the PDF report structure.
- Title format "Market Snapshot – [Area]" (matches PDF header)
- Subline "Period: Last X days • Source: Live MLS Data"  
- Insight paragraph with 1-2 sentence market summary
- 4-metric Hero Row (Median Price, Closed Sales, DOM, MOI)
- Core Indicators section (New Listings, Pending, Sale-to-List)

V3: Professional styling refresh with enhanced Market Snapshot data.
- Table-based layout for maximum email client compatibility
- MSO/Outlook conditional comments for rounded buttons and circular photos
- VML fallback for Outlook gradient headers
- Dark mode support
- Mobile responsive (metrics stack on mobile)
- Full white-label branding support
"""
import html
import os
import re
from datetime import date
from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from typing import Dict, Optional, TypedDict, Tuple, List

from worker.property_builder import normalize_hex_color, safe_url
from worker.themes import _brighten, contrast as _contrast, derive_theme


class Brand(TypedDict, total=False):
    """Brand configuration for white-label emails."""
    display_name: str
    logo_url: Optional[str]
    email_logo_url: Optional[str]  # Separate logo for email headers (light version)
    primary_color: Optional[str]
    accent_color: Optional[str]
    rep_name: Optional[str]
    rep_title: Optional[str]
    rep_photo_url: Optional[str]
    rep_phone: Optional[str]
    rep_email: Optional[str]
    contact_line1: Optional[str]
    contact_line2: Optional[str]
    website_url: Optional[str]


# Report type display names and taglines
# V4: market_snapshot uses PDF-aligned structure with 4-metric hero + core indicators
REPORT_CONFIG = {
    "market_snapshot": {
        "label": "Market Snapshot",
        "tagline": None,  # V4: Uses "Market Snapshot – [Area]" instead of generic tagline
        "section": None,  # V4: No section label - structured sections instead
        "has_extra_stats": False,  # V4: MOI now in hero row
        "has_property_types": True,
        "has_price_tiers": True,
        "has_hero_4": True,  # V4: 4-metric hero row (Median, Closed, DOM, MOI)
        "has_core_indicators": True,  # V4: Core indicators section (New, Pending, CTL)
        "has_insight": True,  # V4: Insight paragraph
    },
    "new_listings": {
        "label": "New Listings",
        "tagline": None,  # V4: Uses PDF-aligned title
        "section": None,
        "has_extra_stats": False,
        "has_hero_4": True,  # V4: 4-metric hero row
        "has_insight": True,  # V4: Insight paragraph
    },
    "inventory": {
        "label": "Inventory Report",
        "tagline": None,  # V4: Uses PDF-aligned title
        "section": None,
        "has_extra_stats": False,
        "has_hero_4": True,  # V4: 4-metric hero row
        "has_insight": True,  # V4: Insight paragraph
        "has_listings_table": True,  # V5: Include listings table
    },
    "closed": {
        "label": "Closed Sales",
        "tagline": None,  # V4: Uses PDF-aligned title
        "section": None,
        "has_extra_stats": False,  # V4: Integrated into hero row
        "has_hero_4": True,  # V4: 4-metric hero row
        "has_insight": True,  # V4: Insight paragraph
        "has_listings_table": True,  # V6: Include listings table
    },
    "price_bands": {
        "label": "Price Analysis",
        "tagline": None,  # V4: Uses PDF-aligned title
        "section": None,
        "has_extra_stats": False,
        "has_price_bands": True,
        "has_hero_4": True,  # V4: 4-metric hero row
        "has_insight": True,  # V4: Insight paragraph
    },
    "open_houses": {
        "label": "Open Houses",
        "tagline": "Open This Weekend",
        "section": "Open Houses",
        "has_extra_stats": False,
    },
    "new_listings_gallery": {
        "label": "New Listings Gallery",
        "tagline": None,  # V6.1: Use report label in header for consistency
        "section": "New Listings",
        "has_extra_stats": False,
        "has_insight": True,  # V13: AI-powered insight for gallery emails
    },
    "featured_listings": {
        "label": "Featured Listings",
        "tagline": None,  # V6: Use report label in header for consistency
        "section": "Featured Properties",
        "has_extra_stats": False,
        "has_insight": True,  # V13: AI-powered insight for featured emails
    },
}


def _format_price(price: Optional[float]) -> str:
    """Format price for display."""
    if price is None:
        return "N/A"
    if price >= 1_000_000:
        # Format as millions, strip trailing zeros and decimal point
        formatted = f"${price / 1_000_000:.2f}".rstrip('0').rstrip('.')
        return f"{formatted}M"
    if price >= 1_000:
        return f"${price / 1_000:.0f}K"
    return f"${price:,.0f}"


def _format_price_clean(price: Optional[float]) -> str:
    """Format price for display - cleaner version."""
    if price is None:
        return "N/A"
    if price >= 1_000_000:
        m = price / 1_000_000
        if m == int(m):
            return f"${int(m)}M"
        return f"${m:.1f}M"
    if price >= 1_000:
        k = price / 1_000
        if k == int(k):
            return f"${int(k)}K"
        return f"${k:.0f}K"
    return f"${price:,.0f}"


def _format_number(value: Optional[int]) -> str:
    """Format number for display."""
    if value is None:
        return "N/A"
    return f"{value:,}"


def _format_percent(value: Optional[float]) -> str:
    """Format percentage for display."""
    if value is None:
        return "N/A"
    return f"{value:.1f}%"


# Sentinel substituted per recipient by send.py after the body is rendered once.
# It lives here rather than in send.py because the trust boundary below has to
# recognise it: it is not a URL, so scheme-allowlisting it would strip it, the
# per-recipient substitution would find nothing to replace, and send.py:229
# would refuse to send at all.
_UNSUB_URL_SENTINEL = "__TRENDYREPORTS_UNSUBSCRIBE_URL__"


# ═══════════════════════════════════════════════════════════════════════════
# The block environment — Workstream C's consolidation
# ═══════════════════════════════════════════════════════════════════════════
#
# §06 replaces eight per-report-type layouts assembled in Python with ONE set of
# named blocks selected per type. The blocks live in templates/email/blocks/ and
# are moved across verbatim: same HTML, different interpolation syntax. Whether
# that holds is not a matter of care — `tests/test_email_render_diff.py` compares
# what each of ten documents MEANS, before and after, and an empty diff is the
# acceptance criterion.
#
# ╔═══════════════════════════════════════════════════════════════════════╗
# ║  autoescape=False IS DELIBERATE. DO NOT TURN IT ON.                   ║
# ╚═══════════════════════════════════════════════════════════════════════╝
#
# A `.jinja2` file carries an implicit promise, and this one does not keep it.
# If you arrived here because you noticed a template engine configured not to
# escape and reached for the one-word fix: that instinct is right in general and
# wrong here, and the paragraph below is the reason.
#
# **Everything reaching a block has already been escaped, exactly once**, by the
# trust boundary near the top of `schedule_email_html()` — `_sanitize_brand()`,
# `_esc()`, `_sanitize_metrics()`, `_sanitize_listing()` and `safe_url()`, all
# applied before a single value is used. Read the comment above those calls; it
# explains why the escaping lives there and not at the ~460 interpolation sites.
#
# **Turning autoescape on breaks the document in two ways:**
#
#   1. Every already-escaped value is escaped a second time. An ampersand in a
#      street address renders as `&amp;amp;`.
#   2. Worse, and the reason per-site escaping was rejected in the first place:
#      roughly fifty of these interpolations insert HTML FRAGMENTS this module
#      built — `badge_html`, `phone_pill_html`, every `_build_*` return. Escaping
#      those renders the markup as visible text. The reader sees `<span
#      style="...">Sold</span>` printed in the middle of a table row.
#
# So the blocks have the same trust model as the f-strings they replace: safe
# because the inputs were cleaned once, not because the templating escapes. The
# migration is NEUTRAL on security, not an improvement — worth stating plainly,
# because the opposite is the natural assumption.
#
# `test_the_block_environment_does_not_escape` fails if this is flipped, and
# carries this reason in its assertion message so the failure explains itself.
_BLOCK_ENV = Environment(
    loader=FileSystemLoader(str(Path(__file__).resolve().parents[1] / "templates" / "email")),
    autoescape=False,          # see above — NOT an oversight
    trim_blocks=True,
    lstrip_blocks=False,
    keep_trailing_newline=False,
)


def render_block(name: str, **context) -> str:
    """Render one §06 block. `name` is the stem, e.g. "cta"."""
    return _BLOCK_ENV.get_template(f"blocks/{name}.jinja2").render(**context)


# ═══════════════════════════════════════════════════════════════════════════
# Input sanitisation — see the TRUST BOUNDARY block in schedule_email_html()
# ═══════════════════════════════════════════════════════════════════════════

# ── The platform's own postal address (CAN-SPAM §7704(a)(5), D-060) ─────────
#
# TrendyReports' registered business address, used when an account has not set
# its own. It is a real address supplied as a business decision — the original
# slot's TODO was explicit that a guess or a placeholder here would be worse
# than the omission it replaced, because a wrong address is an affirmative
# false statement rather than a missing one.
#
# It is deliberately NOT written into `affiliate_branding.postal_address` as a
# column default (see 0055). A row holding this address under an affiliate's
# brand would say that affiliate is located here. The fallback lives in the
# render path instead, where PLATFORM_SENDER_LABEL can say whose address it is.
#
# Overridable by environment for staging and for the day the office moves,
# without a deploy. A blank or unset variable falls back to the constant rather
# than to nothing: an empty postal address is the non-compliant state this
# whole entry exists to end, and a typo in a config value must not reintroduce
# it silently.
PLATFORM_POSTAL_ADDRESS = (
    os.getenv("PLATFORM_POSTAL_ADDRESS", "").strip()
    or "440 Rte. 66, Glendora, CA 91740"
)
PLATFORM_SENDER_LABEL = (
    os.getenv("PLATFORM_SENDER_LABEL", "").strip()
    or "Sent by TrendyReports"
)


# Brand keys carrying free text. Escaped.
_BRAND_TEXT_KEYS = (
    "display_name", "rep_name", "rep_title", "rep_phone", "rep_email",
    "contact_line1", "contact_line2", "postal_address",
)
# Brand keys carrying a URL. Scheme-allowlisted, NOT escaped — escaping a URL
# mangles its query string, and does nothing about the scheme, which is the
# part that matters.
_BRAND_URL_KEYS = (
    "logo_url", "email_logo_url", "footer_logo_url", "email_footer_logo_url",
    "rep_photo_url", "website_url",
)
# Brand keys parsed as hex before use. Guarded by normalize_hex_color at the
# read site; listed here so the classification of every brand key is explicit
# and a new key cannot be added without landing in one of the three buckets.
_BRAND_COLOR_KEYS = ("primary_color", "accent_color")

# Listing keys from the SimplyRETS feed. The numeric ones are deliberately not
# escaped: they are formatted with numeric specs (f"{price:,.0f}"), which a str
# would break, and a non-numeric value there is a builder bug, not an injection.
_LISTING_TEXT_KEYS = ("street_address", "city", "status", "zip_code")
_LISTING_URL_KEYS = ("hero_photo_url",)


def _esc(value):
    """
    HTML-escape a value that will be interpolated into markup or an attribute.

    `quote=True` matters as much as the tag escaping: most of the injection
    sites in this module are inside `attr="…"`, where an unescaped double quote
    is what breaks out. Non-strings pass through untouched so that numeric
    format specs downstream keep working.
    """
    if not isinstance(value, str):
        return value
    return html.escape(value, quote=True)


def _sanitize_brand(brand: Optional[Dict]) -> Dict:
    """Classify and clean every brand key. Unknown keys are escaped."""
    if not brand:
        return {}
    out = {}
    for key, value in brand.items():
        if key in _BRAND_URL_KEYS:
            out[key] = safe_url(value) or None
        elif key in _BRAND_COLOR_KEYS:
            out[key] = value          # normalize_hex_color runs at the read
        else:
            # _BRAND_TEXT_KEYS and anything not yet classified. Defaulting an
            # unrecognised key to "escape" is the safe direction: a new text
            # field is protected the day it is added, and a new URL field
            # renders visibly broken rather than silently injectable.
            out[key] = _esc(value)
    return out


def _sanitize_listing(listing: Dict) -> Dict:
    """Clean one listing from the vendor feed, leaving numerics alone."""
    if not isinstance(listing, dict):
        return listing
    out = dict(listing)
    for key in _LISTING_TEXT_KEYS:
        if key in out:
            out[key] = _esc(out[key])
    for key in _LISTING_URL_KEYS:
        if key in out:
            out[key] = safe_url(out[key]) or None
    return out


def _sanitize_metrics(metrics: Optional[Dict]) -> Dict:
    """
    Escape string-valued metrics (band labels and similar).

    A no-op for the numbers, which is all of them today. It is here so that a
    builder which starts putting a city or a filter label into metrics does not
    reopen the channel silently.
    """
    if not metrics:
        return metrics or {}
    return {k: (_esc(v) if isinstance(v, str) else v) for k, v in metrics.items()}


# Extension markers people actually type into a free-text phone field.
# Ordered longest-first so "extension" is not consumed by the "ext" rule.
_PHONE_EXT_MARKERS = ("extension", "ext.", "ext", "x", "#")


def _tel_uri(phone: Optional[str]) -> Optional[str]:
    """
    Build an RFC 3966 `tel:` URI from a free-text phone number.

    `rep_phone` is `users.phone` (tasks.py:465) — an unvalidated free-text
    column — so it arrives however the agent typed it: "(626) 555-0134",
    "626.555.0134", "626-555-0134 x12". Interpolating that straight into
    `href="tel:{rep_phone}"` produces a malformed URI: spaces and parentheses
    are not valid URI characters, and the space in particular is where strict
    parsers truncate or drop the link.

    Returns a dialable URI, or None when the input cannot be made into one —
    in which case the caller must render the number as plain text rather than
    as a link that goes nowhere.

    Extensions are emitted as RFC 3966 `;ext=` rather than folded into the
    number. Folding them in is worse than not linking at all: "626-555-0134
    x12" would otherwise yield a 12-digit string and dial a *different* number.
    (`services/twilio_sms.py:format_phone_e164` has exactly that behaviour; it
    is not reused here both because it lives in the API package, which the
    worker does not import, and because of that bug.)
    """
    if not phone:
        return None

    # Case-folded throughout: the marker search and the slice indices must be
    # taken against the same string, and only digits and a leading "+" are read
    # out afterwards, neither of which case affects.
    raw = phone.strip().lower()

    # Split off an extension before touching the digits, so its digits are
    # never mistaken for part of the subscriber number.
    ext_digits = ""
    for marker in _PHONE_EXT_MARKERS:
        idx = raw.find(marker)
        # A leading "#" or "x" is not an extension marker, it is a typo or a
        # prefix — requiring a preceding digit avoids eating the whole string.
        if idx > 0 and any(c.isdigit() for c in raw[:idx]):
            ext_digits = "".join(c for c in raw[idx + len(marker):] if c.isdigit())
            raw = raw[:idx]
            break

    has_plus = raw.startswith("+")
    digits = "".join(c for c in raw if c.isdigit())
    if not digits:
        return None

    if has_plus:
        number = f"+{digits}"
    elif len(digits) == 10:
        # NANP national number. The default is deliberate and US-only, matching
        # the rest of the product; a non-US number typed without a "+" cannot
        # be distinguished from this and will be wrong either way.
        number = f"+1{digits}"
    elif len(digits) == 11 and digits.startswith("1"):
        number = f"+{digits}"
    else:
        # 7-digit local numbers, truncated entries, "call me" — anything we
        # cannot resolve to a dialable number. Refuse rather than guess.
        return None

    return f"tel:{number};ext={ext_digits}" if ext_digits else f"tel:{number}"


# ============================================================================
# DESIGN'S 5TH PACKAGE — the market email
# docs/design-claude/5thpackage/design_handoff_email_social/emails/market/
# ============================================================================
#
# One brand colour, used two ways and never a third:
#
#   as a FILL      the masthead band, the button, the initials disc, the bars.
#                  `primary` exactly as the account set it — the fill is theirs.
#   as TEXT        the hero number, prices, the agent's links. `primary_ink`,
#                  which `derive_theme` guarantees at 4.5:1 on white AND on the
#                  tint — the only two light surfaces brand text lands on here.
#
# `accent_color` is no longer read. Design's emails are monochrome, and the
# accent was the source of most of the 1,167 unreadable runs measured on the old
# layout (a second colour nobody checked against the first).
#
# DARK MODE. Every element carries a `tr-*` class the shell's
# `prefers-color-scheme: dark` block remaps. Brand text carries `tr-brand`, and
# its dark colour is per brand, so the shell writes that one rule from
# `dark_ink` below. Without it the review measured a navy brand's prices at
# 1.00–1.13:1 on the dark card — present in the HTML, invisible on the phone.

#: The lightest dark surface brand text lands on: `.tr-tint` / `.tr-cell` in the
#: shell's dark block. The card (#1F2937) is darker, so clearing this clears it.
DARK_TINT = "#273244"


def _dark_ink(brand_hex: str) -> str:
    """
    The brand as TEXT in dark mode: `primary_on_dark`, brightened further until
    it clears 4.5:1 on `DARK_TINT`.

    `primary_on_dark` targets #0f172a, which is darker than any surface this
    email paints in dark mode, so on its own it can fall short on the tint by a
    step. Same value-first brightening as `themes._brighten` (D-099), so a navy
    stays blue rather than greying out. White terminates it: 13.6:1 on the tint.
    """
    ink = derive_theme(brand_hex)["primary_on_dark"]
    for _ in range(64):
        if _contrast(ink, DARK_TINT) >= 4.5:
            return ink
        stepped = _brighten(ink)
        if stepped == ink:
            break
        ink = stepped
    return "#ffffff"


def _tokens(primary_color: str) -> Dict[str, str]:
    """Every colour a block reads, derived once from the one brand colour."""
    t = derive_theme(primary_color)
    return {
        "primary": t["primary"],
        "on_primary": t["on_primary"],
        "ink": t["primary_ink"],
        "tint": t["tint"],
        "dark_ink": _dark_ink(primary_color),
        "cta_edge": _cta_edge(t),
    }


#: WCAG 1.4.11: a control's visual boundary needs 3:1 against what is behind it.
NON_TEXT_CONTRAST = 3.0


def _cta_edge(t: Dict[str, str]) -> str:
    """Inline style for the brand button's edge in LIGHT mode: none when the
    fill already stands out from the white card, a 2px edge in the brand's ink
    (which `derive_theme` holds at 4.5:1 on white) when it does not — an amber
    or lime button is otherwise a pale shape on white (D-313). Dark mode's edge
    is `.tr-edge` in the shell."""
    if _contrast(t["primary"], "#FFFFFF") >= NON_TEXT_CONTRAST:
        return ""
    return f"border:2px solid {t['primary_ink']};"


def _split_insight(text: str) -> Tuple[str, str]:
    """
    The insight paragraph as Design's headline and body: the first sentence, and
    the rest. A sentence ends at . ! or ? followed by whitespace, so "$1.42M" and
    "2.1%" do not end one. A one-sentence insight is all headline.
    """
    text = (text or "").strip()
    m = re.match(r"(.+?[.!?])\s+(\S.*)", text, re.S)
    if not m:
        return text, ""
    return m.group(1).strip(), m.group(2).strip()


def _build_ai_narrative(insight_text: str) -> str:
    """§06 block `read`, insight variant: the h1 and the paragraph under it."""
    if not insight_text:
        return ""
    headline, body = _split_insight(insight_text)
    return render_block("read", variant="insight", headline=headline, body=body)


def _build_quick_take(text: str, accent_color: str = None, primary_color: str = None) -> str:
    """
    §06 block `read`, panel variant — the Quick Take, which stands in as the
    headline when a report type has no insight paragraph (open houses).

    THIS WAS THE WORST CONTRAST DEFECT IN THE PRODUCT: the label and the panel
    arrived as two unrelated brand colours, and an account that set one colour
    rendered it on itself, invisible. Design's panel has no brand colour at all —
    it is the headline in ink — so the defect has nowhere left to live. The colour
    arguments are kept so the call sites read as before, and are unused.
    """
    if not text:
        return ""
    return render_block("read", variant="panel", headline=text)


def _build_hero_stat(value: str, label: str, tk: Dict[str, str],
                     sub_label: str = None) -> str:
    """§06 chrome `hero` — the headline figure on the tint panel, in `ink`."""
    return render_block("chrome", piece="hero", value=value, label=label,
                        sub=sub_label, tint=tk["tint"], ink=tk["ink"])


def _build_gallery_count(label: str, count: int) -> str:
    """§06 chrome `count_pill` — the small uppercase line over a list."""
    return render_block("chrome", piece="count_pill", text=f"{label} · {count}")


def _build_section_label(label: str) -> str:
    """§06 chrome `section_label` — the same line, over the price bands."""
    return render_block("chrome", piece="section_label", text=label)


def _build_filter_blurb(filter_text: str) -> str:
    """§06 chrome `filter_blurb` — the optional report-criteria line."""
    if not filter_text:
        return ""
    return render_block("chrome", piece="filter_blurb", text=filter_text)


def _build_stacked_stats(stats: List[Tuple[str, str]]) -> str:
    """
    §06 block `spec_list` — the four-across metric strip.

    Capped at four here rather than in the template: the cap is a layout fact
    (four 25% cells fill a row) and the block should not have to know it.
    """
    if not stats:
        return ""
    return render_block("spec_list", variant="strip", stats=stats[:4])


def _listing_price_str(listing: Dict) -> str:
    """Format a listing's price for display."""
    price = listing.get("list_price") or listing.get("close_price")
    if not price:
        return "Price N/A"
    return _format_price_clean(price)


def _listing_specs(listing: Dict) -> str:
    """`3 bd · 2 ba · 1,800 sq ft`, omitting whatever is missing."""
    parts = []
    if listing.get("bedrooms"):
        parts.append(f"{listing['bedrooms']} bd")
    if listing.get("bathrooms"):
        parts.append(f"{listing['bathrooms']} ba")
    if listing.get("sqft"):
        parts.append(f"{listing['sqft']:,} sq ft")
    return " · ".join(parts)


#: Photo boxes: (width, height). Rows are Design's 120×90; cards 264×150.
_PHOTO_SIZES = {"row": (120, 90), "card": (264, 150)}


def _photo_html(listing: Dict, size: str) -> str:
    """
    The listing photo, or a grey box the same size when there is none (B5: a
    missing photo used to be a broken-image glyph on one surface and a blank box
    on another; it is the box everywhere).

    The box carries no "Photo" label. Design's has one, and it measures 3.7:1 in
    light mode and 4.1:1 in dark — a label that fails the check to say nothing.
    """
    w, h = _PHOTO_SIZES[size]
    photo = listing.get("hero_photo_url")
    if photo:
        alt = listing.get("street_address") or ""
        return (f'<img src="{photo}" alt="{alt}" width="{w}" height="{h}" '
                f'style="display:block;width:100%;max-width:{w}px;height:{h}px;'
                f'object-fit:cover;border:0;">')
    return (f'<table role="presentation" cellpadding="0" cellspacing="0" border="0" '
            f'width="100%" style="max-width:{w}px;border-collapse:collapse;"><tr>'
            f'<td class="tr-ph" height="{h}" style="height:{h}px;background:#E4E2DA;'
            f'font-size:0;line-height:0;">&nbsp;</td></tr></table>')


#: §3.3 status chips: reserved, never drawn from the brand, so literals. Dark
#: text on a pale fill — 7.0:1 or better each — and the fill is inline with no
#: `tr-*` class, so it stays pale in dark mode and the text stays readable on it.
_STATUS_CHIPS = {
    "sold": ("#D1FAE5", "#065F46"),
    "active": ("#F1F5F9", "#475569"),
    "pending": ("#FEF3C7", "#92400E"),
}


def _build_property_row(listing: Dict, tk: Dict[str, str], chip: str = "") -> str:
    """§06 block `gallery`, row size — Design's photo-left list row."""
    bg, fg = _STATUS_CHIPS.get(chip.lower(), ("", "")) if chip else ("", "")
    return render_block(
        "gallery", size="row",
        photo_html=_photo_html(listing, "row"),
        price=_listing_price_str(listing),
        address=listing.get("street_address") or "Address N/A",
        specs=_listing_specs(listing),
        ink=tk["ink"],
        chip_text=chip if bg else "", chip_bg=bg, chip_fg=fg,
    )


def _build_photo_card_with_badge(listing: Dict, primary_color: str, accent_color: str = None,
                                 badge_text: str = "Sold") -> str:
    """A sales/inventory row with its status chip. Kept for the contrast tests."""
    return _build_property_row(listing, _tokens(primary_color), chip=badge_text)


def _build_gallery_card(listing: Dict, tk: Dict[str, str]) -> str:
    """§06 block `gallery`, card size — one half of Design's two-across gallery."""
    city = listing.get("city") or ""
    addr = listing.get("street_address") or "Address N/A"
    return render_block(
        "gallery", size="card",
        photo_html=_photo_html(listing, "card"),
        price=_listing_price_str(listing),
        address=f"{addr}, {city}" if city else addr,
        specs=_listing_specs(listing),
        ink=tk["ink"],
    )


def _build_rows(listings: List[Dict], tk: Dict[str, str], chips: bool = False) -> str:
    """§06 block `grid`, rows shape — a single column of `gallery:row`s."""
    if not listings:
        return ""
    return render_block("grid", shape="rows", cards=[
        _build_property_row(
            l, tk, chip=("Sold" if l.get("close_price") else (l.get("status") or "Active"))
            if chips else "")
        for l in listings
    ])


def _card_grid(cards: List[str]) -> str:
    """
    §06 block `grid`, cards shape — two across.

    A short final row is padded with an EMPTY CELL rather than left ragged: a
    `<tr>` with fewer `<td>`s than its siblings collapses the table's column
    widths in Outlook.
    """
    if not cards:
        return ""
    rows = [list(cards[i:i + 2]) + [""] * (2 - len(cards[i:i + 2]))
            for i in range(0, len(cards), 2)]
    return render_block("grid", shape="cards", rows=rows)


def _sales_table_row(listing: Dict, index: int) -> Dict:
    """
    One row's values, formatted. Shaped here rather than in the template so that
    `_format_price_clean`, the chip palette and the fallbacks stay testable in
    Python — a template is a bad place to hide any of them.
    """
    beds = listing.get("bedrooms") or ""
    baths = listing.get("bathrooms") or ""
    sqft = listing.get("sqft")
    price = listing.get("close_price") or listing.get("list_price")
    status = listing.get("status") or ""
    bg, fg = _STATUS_CHIPS.get(status.lower(), ("", ""))
    return {
        "address": listing.get("street_address") or "N/A",
        "specs": f"{beds} / {baths}" if beds and baths else "",
        "sqft": f"{sqft:,}" if sqft else "",
        "price": _format_price_clean(price) if price else "N/A",
        "dom": listing.get("days_on_market") or "",
        "zebra": index % 2 == 1,
        "badge_html": (
            f' <span style="display:inline-block;margin-left:6px;padding:1px 6px;'
            f'font-size:9px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;'
            f'background:{bg};color:{fg};">{status}</span>'
            if status and bg else ""
        ),
    }


def _build_sales_table(listings: List[Dict], primary_color: str,
                       accent_color: str = None) -> str:
    """§06 block `table` — the five-column listings table."""
    if not listings:
        return ""
    tk = _tokens(primary_color)
    return render_block(
        "table",
        rows=[_sales_table_row(l, i) for i, l in enumerate(listings)],
        tint=tk["tint"],
        price_ink=tk["ink"],
    )


# ---------------------------------------------------------------------------
# Layout body builders. Each returns the card rows between the masthead and
# the CTA.
# ---------------------------------------------------------------------------

def _build_market_narrative_body(
    insight_text: str, hero_value: str, hero_label: str,
    stats: List[Tuple[str, str]], quick_take: str, tk: Dict[str, str],
    filter_description: str = None, listings: List[Dict] = None,
    listings_label: str = "Notable listings",
) -> str:
    """Market Snapshot / New Listings / Open Houses — Design's market_snapshot."""
    body = _build_ai_narrative(insight_text) or _build_quick_take(quick_take)
    body += _build_filter_blurb(filter_description)
    body += _build_hero_stat(hero_value, hero_label, tk)
    if listings:
        body += _build_gallery_count(listings_label, len(listings))
        body += _build_rows(listings, tk)
    body += _build_stacked_stats(stats)
    return body


def _build_closed_sales_body(
    insight_text: str, hero_value: str, hero_label: str,
    listings: List[Dict], stats: List[Tuple[str, str]], quick_take: str,
    tk: Dict[str, str], filter_description: str = None,
) -> str:
    """Closed Sales / Inventory — Design's closed: four rows, then the table."""
    body = _build_ai_narrative(insight_text) or _build_quick_take(quick_take)
    body += _build_filter_blurb(filter_description)
    body += _build_hero_stat(hero_value, hero_label, tk)
    if listings:
        show = listings[:4]
        label = "Recent sales" if any(l.get("close_price") for l in show) else "Newest listings"
        body += _build_gallery_count(label, len(show))
        body += _build_rows(show, tk, chips=True)
        body += _build_sales_table(listings, tk["primary"])
    body += _build_stacked_stats(stats)
    return body


def _label_share(pct_str):
    """The percentage a band's label prints, as an int, or None. (D-115)

    The bar's width comes from here so that it can only ever depict the
    number the reader sees. `pct_str` is built as `f"{n:.0f}%"` one caller
    away; parsed rather than recomputed, because recomputing reintroduces the
    possibility of the two disagreeing.
    """
    m = re.match(r"\s*(\d+(?:\.\d+)?)\s*%", str(pct_str or ""))
    if not m:
        return None
    return max(0, min(100, int(round(float(m.group(1))))))


def _band_rows(trend_stats, primary_color: str = None, accent_color: str = None) -> List[Dict]:
    """
    One dict per price band, with the bar width and the percentage label
    computed together.

    They are computed together deliberately. B6 on the register is exactly these
    two drifting apart: the bars were normalised to the LARGEST band while the
    labels showed share of TOTAL, so Move-Up read 43% beside a bar filled to
    100%. Splitting the two calculations across a builder and a template is how
    that happens again.

    FIXED 2026-10-01 (D-115): THE BAR IS THE NUMBER PRINTED BESIDE IT. The width
    is parsed from `pct_str` itself rather than recomputed from a total, so it
    depicts the PRINTED value including its rounding.

    THE 2% FLOOR IS GONE, AND DESIGN'S 5TH PACKAGE ASKS FOR IT BACK. Kept, it
    would draw a 2% bar beside a label reading 0% or 1% — this defect again,
    smaller. The count is printed on every row, so a band with listings is never
    invisible; only its bar is, and only when its share rounds to zero, which is
    what the label says too.

    The most-active band is no longer drawn in a second colour: Design's bars
    are one brand fill, and the hero already names that band.
    """
    rows = []
    for label, count_str, pct_str, _is_highlight in trend_stats:
        # None when the label is not a percentage we can read. A bar drawn
        # from a guess would be the defect this fixes, so there is no bar.
        share = _label_share(pct_str)
        bar_pct = share if share is not None else 0
        rows.append({
            "label": label,
            "count": count_str,
            "pct": pct_str,
            "bar_pct": bar_pct,
            "empty_pct": 100 - bar_pct,
        })
    return rows


def _build_analytics_body(
    insight_text: str, hero_value: str, hero_label: str,
    trend_stats: List[Tuple[str, str, str, bool]],
    quick_take: str, tk: Dict[str, str],
    filter_description: str = None,
    supporting_metrics: List[Tuple[str, str]] = None,
    listings: List[Dict] = None,
) -> str:
    """Price Bands — Design's price_bands.

    trend_stats: each tuple is (band_label, listing_count_str, percentage_str, is_most_active).
    supporting_metrics: optional list of (label, value) for the row under the bars.
    """
    body = _build_ai_narrative(insight_text) or _build_quick_take(quick_take)
    body += _build_filter_blurb(filter_description)
    body += _build_hero_stat(hero_value, hero_label, tk)

    if trend_stats:
        body += _build_section_label("Price distribution")
        body += render_block("bands", bands=_band_rows(trend_stats), primary=tk["primary"])

    if supporting_metrics:
        n = len(supporting_metrics[:3])
        body += render_block(
            "spec_list", variant="supporting",
            stats=supporting_metrics[:3],
            cell_width=f"{100 // n}%",
        )

    if listings:
        body += _build_gallery_count("Example listings", len(listings))
        body += _build_rows(listings, tk)
    return body


def _build_gallery_body(
    insight_text: str, listings: List[Dict], quick_take: str, tk: Dict[str, str],
    gallery_label: str = "Featured listings", filter_description: str = None,
) -> str:
    """
    New Listings Gallery / Featured Listings — Design's two-across cards, at
    every count. The adaptive layouts this replaces (stacked, 2×2, 3×2, list)
    each drew a different number of listings from the one the truncation note
    was given: the 2×2 drew 4 under a note reading "Showing 8".
    """
    body = _build_ai_narrative(insight_text) or _build_quick_take(quick_take)
    body += _build_filter_blurb(filter_description)
    if listings:
        body += _build_gallery_count(gallery_label, len(listings))
        body += _card_grid([_build_gallery_card(l, tk) for l in listings])
    return body


# ---------------------------------------------------------------------------
# The truncation note, the CTA, the masthead and the signature
# ---------------------------------------------------------------------------

def _pdf_has_all(report_type: str, total_available: int) -> bool:
    """
    Whether the PDF really holds every listing the note counts.

    Design's note says "All of them are in the report." That is true for the
    catalog kinds, whose PDF lists everything (cap 200), and FALSE for the
    snapshot kinds, whose PDF is itself a sample — market_snapshot shows 9,
    price_bands 8, featured_listings 12. Read from `market_builder.PDF_CONFIG`
    rather than restated, so the two cannot drift.
    """
    from worker.market_builder import PDF_CONFIG
    cfg = PDF_CONFIG.get(report_type)
    return bool(cfg) and total_available <= cfg["cap"]


def _build_truncation_note(total_available: int, showing: int,
                           pdf_url: Optional[str], pdf_has_all: bool = False,
                           of_what: str = "") -> str:
    """
    §06 chrome `truncation_note` — "Showing X of Y."

    Both conditions stay here rather than in the template: a note claiming
    truncation that did not happen is worse than no note.
    """
    if not pdf_url or total_available <= showing or showing <= 0:
        return ""
    return render_block("chrome", piece="truncation_note", showing=showing,
                        total_available=total_available, pdf_has_all=pdf_has_all,
                        of_what=of_what)


def _build_masthead(tk: Dict[str, str], logo_url: Optional[str], brand_name: str,
                    date_label: str, kicker: str) -> str:
    """
    §06 block `masthead` — the solid brand band, then the kicker line.

    Solid, not the old primary-to-accent gradient: a gradient's text has to clear
    AA at every stop, and on a navy-to-lime band nothing did.
    """
    return render_block(
        "masthead", primary=tk["primary"], on_primary=tk["on_primary"],
        logo_url=logo_url, brand_name=brand_name,
        date_label=date_label, kicker=kicker,
    )


def _build_pdf_cta(pdf_url: Optional[str], tk: Dict[str, str], sub: str = "") -> str:
    """
    §06 block `cta` — "Open the full report", above the signature.

    This function stays as the seam: it decides whether the block renders at
    all, which keeps that judgement in Python where it is testable.
    """
    if not pdf_url:
        return ""
    return render_block("cta", pdf_url=pdf_url, primary=tk["primary"],
                        on_primary=tk["on_primary"], edge=tk["cta_edge"], sub=sub)


def _today() -> date:
    """The "as of" date the masthead and data line print. A seam for tests."""
    return date.today()


def _initials(name: str) -> str:
    """Up to two initials from a display name; letters only, so markup cannot leak in."""
    words = [w for w in re.split(r"\s+", html.unescape(name or "")) if w[:1].isalpha()]
    return "".join(w[0].upper() for w in words[:2])


def _build_signature(**ctx) -> str:
    """
    §06 block `signature` — the agent, then the footer CAN-SPAM requires.

    The footer lines arrive pre-rendered: whether the postal line carries the
    account's address or ours, and how it is labelled, is a compliance decision
    and belongs in Python where it is tested rather than behind a template
    conditional.
    """
    return render_block("signature", **ctx)


#: The §06 blocks each report type renders, in first-use order, with the variant
#: that distinguishes one shape of a block from another — recorded from an actual
#: render of the standard fixture, not from reading the code.
#:
#: PER REPORT TYPE, NOT PER LAYOUT, AND THAT IS A FINDING. §06 describes the body
#: as "assembled from blocks selected by report type", which implies the layout
#: decides the sequence. It does not. Three types share the `market_narrative`
#: layout and produce TWO different sequences: `open_houses` renders
#: `read:panel` where the other two render `read:insight`, because the Quick Take
#: stands in as the headline only when there is no insight text. Selection is conditional on the
#: DATA as much as on the type, and a map keyed by layout could not express it.
#:
#: Three more blocks are conditional and therefore absent below, each for a
#: reason in the fixture rather than in the code:
#:   chrome:filter_blurb   renders only with a filter_description
#:   chrome:section_label  } both only when the price-band chart has
#:   bands                 } trend_stats to draw
#: Their absence is a property of the standard fixture and is asserted, so if a
#: refactor started emitting them unconditionally this would fail.
#:
#: THIS IS DECLARED DATA AND IT IS ALSO CHECKED. `test_the_declared_block
#: _sequence_matches_what_renders` instruments `render_block` during a real
#: render of every report type and requires the observed sequence to equal the
#: declaration exactly. A table describing what the code does, which nothing
#: verifies, is a comment — and this project has spent a month finding those.
#:
#: WHY A DECLARATION AND NOT A DRIVER — AND WHY §06's WORDING IS NOT A REASON
#: TO "FINISH" IT INTO ONE.
#:
#: §06 says the body is "assembled from blocks selected by report type", which
#: reads like an instruction to build a loop over this map. Decided against, on
#: 2026-09-24, and the argument is here rather than in a pull request because
#: this is where someone will be standing when they consider it.
#:
#: Driving from the map requires every step to take a uniform context. That
#: turns seven readable functions of sixteen to fifty lines into roughly fifteen
#: small ones plus a context object plus a dispatcher — and the conditional
#: selection documented above, which is a plain `insight or quick_take` today,
#: becomes a predicate function registered against a block name. The sequence
#: then reads only through the registry, and the per-layout data gathering that
#: genuinely differs between report types — and is where this module's defects
#: have actually been — gets spread thinner across more places.
#:
#: The safety a driver would add is already provided by
#: `test_the_declared_block_sequence_matches_what_renders`: the map cannot
#: disagree with the code, because the code is what the map is checked against.
#: A driver would make the map authoritative instead of verified, which is not
#: obviously better and is certainly more machinery.
#:
#: This is a judgement, not a law. If a driver is wanted the map is already the
#: right shape for one — but it should be chosen on these trade-offs rather than
#: on §06's phrasing, which was written before anyone knew the selection was
#: data-conditional.
REPORT_BLOCKS = {
    "market_snapshot": (
        "read:insight", "chrome:hero", "chrome:count_pill", "gallery:row",
        "grid:rows", "spec_list:strip", "chrome:truncation_note",
    ),
    "new_listings": (
        "read:insight", "chrome:hero", "chrome:count_pill", "gallery:row",
        "grid:rows", "spec_list:strip", "chrome:truncation_note",
    ),
    "open_houses": (
        # no insight text for this type, so the Quick Take is the headline
        "read:panel", "chrome:hero", "chrome:count_pill", "gallery:row",
        "grid:rows", "spec_list:strip", "chrome:truncation_note",
    ),
    "closed": (
        "read:insight", "chrome:hero", "chrome:count_pill", "gallery:row",
        "grid:rows", "table", "spec_list:strip", "chrome:truncation_note",
    ),
    "inventory": (
        "read:insight", "chrome:hero", "chrome:count_pill", "gallery:row",
        "grid:rows", "table", "spec_list:strip", "chrome:truncation_note",
    ),
    "price_bands": (
        "read:insight", "chrome:hero", "spec_list:supporting",
        "chrome:count_pill", "gallery:row", "grid:rows", "chrome:truncation_note",
    ),
    "new_listings_gallery": (
        "read:insight", "chrome:count_pill", "gallery:card", "grid:cards",
        "chrome:truncation_note",
    ),
    "featured_listings": (
        "read:insight", "chrome:count_pill", "gallery:card", "grid:cards",
        "chrome:truncation_note",
    ),
}

#: Rendered on every report type regardless of layout, per §06 — "masthead,
#: agent block and footer invariant". A footer that renders on seven of eight is
#: a CAN-SPAM failure on the eighth and no per-type test would notice.
INVARIANT_BLOCKS = ("masthead", "cta", "signature")

#: Blocks that exist and render only when their data is present. Listed so their
#: absence from REPORT_BLOCKS reads as conditional rather than as dead.
CONDITIONAL_BLOCKS = ("chrome:filter_blurb", "chrome:section_label", "bands")

LAYOUT_MAP = {
    "market_snapshot": "market_narrative",
    "new_listings": "market_narrative",
    "price_bands": "analytics",
    "open_houses": "market_narrative",
    "closed": "closed_sales",
    "inventory": "closed_sales",
    "new_listings_gallery": "gallery",
    "featured_listings": "gallery",
}


def _format_decimal(value: Optional[float], decimals: int = 1) -> str:
    """Format decimal for display."""
    if value is None:
        return "N/A"
    return f"{value:.{decimals}f}"


def _get_metrics_for_report_type(
    report_type: str, 
    metrics: Dict,
    total_shown: int = 0
) -> Tuple[Tuple[str, str], Tuple[str, str], Tuple[str, str]]:
    """
    Get the 3 main metrics to display based on report type.
    Returns: ((label1, value1), (label2, value2), (label3, value3))
    """
    # Extract common metrics with defaults
    total_active = metrics.get("total_active", 0)
    total_pending = metrics.get("total_pending", 0)
    total_closed = metrics.get("total_closed", 0)
    total_listings = metrics.get("total_listings", total_active)
    new_this_month = metrics.get("new_this_month", 0)
    median_list_price = metrics.get("median_list_price")
    median_close_price = metrics.get("median_close_price")
    avg_dom = metrics.get("avg_dom")
    median_dom = metrics.get("median_dom", avg_dom)
    
    # Format DOM
    dom_display = f"{avg_dom:.0f}" if avg_dom else "N/A"
    median_dom_display = f"{median_dom:.0f}" if median_dom else dom_display
    
    if report_type == "market_snapshot":
        return (
            ("Active Listings", _format_number(total_active)),
            ("Median Price", _format_price_clean(median_close_price or median_list_price)),
            ("Avg DOM", f"{dom_display} days" if dom_display != "N/A" else "N/A"),
        )
    
    elif report_type == "new_listings":
        return (
            ("New Listings", _format_number(total_active)),
            ("Median Price", _format_price_clean(median_list_price)),
            ("Avg DOM", f"{dom_display} days" if dom_display != "N/A" else "N/A"),
        )
    
    elif report_type == "closed":
        return (
            ("Homes Sold", _format_number(total_closed)),
            ("Median Price", _format_price_clean(median_close_price)),
            ("Avg Days to Sell", f"{dom_display}" if dom_display != "N/A" else "N/A"),
        )
    
    elif report_type == "new_listings_gallery":
        # V14: Show "Showing X of Y" when curated
        if total_shown and total_shown < total_listings:
            listing_display = f"{total_shown} of {_format_number(total_listings)}"
        else:
            listing_display = _format_number(total_listings)
        return (
            ("New Listings", listing_display),
            ("Median Price", _format_price_clean(median_list_price)),
            ("Starting At", _format_price_clean(metrics.get("min_price"))),
        )
    
    elif report_type == "featured_listings":
        # V14: Show "Showing X of Y" when curated
        if total_shown and total_shown < total_listings:
            listing_display = f"{total_shown} of {_format_number(total_listings)}"
        else:
            listing_display = _format_number(total_listings)
        return (
            ("Featured Homes", listing_display),
            ("Highest Price", _format_price_clean(metrics.get("max_price"))),
            ("Avg Sq Ft", _format_number(metrics.get("avg_sqft"))),
        )
    
    elif report_type == "inventory":
        return (
            ("Active Listings", _format_number(total_active)),
            ("New This Month", _format_number(new_this_month)),
            ("Median DOM", f"{median_dom_display} days" if median_dom_display != "N/A" else "N/A"),
        )
    
    elif report_type == "price_bands":
        band_count = len(metrics.get("bands", [])) or 3
        return (
            ("Total Listings", _format_number(total_active or total_listings)),
            ("Median Price", _format_price_clean(median_list_price)),
            ("Price Tiers", str(band_count)),
        )
    
    elif report_type == "open_houses":
        return (
            ("Open Houses", _format_number(total_active)),
            ("Saturday", _format_number(metrics.get("saturday_count", 0))),
            ("Sunday", _format_number(metrics.get("sunday_count", 0))),
        )
    
    else:
        # Generic fallback
        return (
            ("Properties", _format_number(total_active)),
            ("Median Price", _format_price_clean(median_list_price)),
            ("Avg DOM", f"{dom_display} days" if dom_display != "N/A" else "N/A"),
        )


def _get_extra_stats(report_type: str, metrics: Dict) -> Optional[Tuple[Tuple[str, str], Tuple[str, str]]]:
    """
    Get extra stats for reports that support them.
    Returns: ((label1, value1), (label2, value2)) or None
    """
    if report_type == "market_snapshot":
        moi = metrics.get("months_of_inventory")
        ctl = metrics.get("sale_to_list_ratio") or metrics.get("close_to_list_ratio")
        moi_display = _format_decimal(moi) if moi else "N/A"
        ctl_display = _format_percent(ctl) if ctl else "N/A"
        return (
            (moi_display, "Months of Inventory"),
            (ctl_display, "Close-to-List Ratio"),
        )
    
    elif report_type == "closed":
        ctl = metrics.get("sale_to_list_ratio") or metrics.get("close_to_list_ratio")
        volume = metrics.get("total_volume")
        ctl_display = _format_percent(ctl) if ctl else "N/A"
        volume_display = _format_price_clean(volume) if volume else "N/A"
        return (
            (ctl_display, "Close-to-List Ratio"),
            (volume_display, "Total Volume"),
        )
    
    return None


def _get_price_bands(metrics: Dict) -> Optional[List[Dict]]:
    """
    Get price bands for price_bands report.
    Returns list of {name, range, count, color} or None
    
    V3.1: Uses monochromatic PRIMARY color for all bands for visual cohesion.
    """
    bands = metrics.get("bands", [])
    if not bands:
        # Try to construct from individual fields
        entry_count = metrics.get("entry_count")
        if entry_count is not None:
            return [
                {
                    "name": "Entry Level",
                    "range": metrics.get("entry_range", "$0 - Median"),
                    "count": entry_count,
                    "color": "PRIMARY",  # Monochromatic
                },
                {
                    "name": "Move-Up",
                    "range": metrics.get("moveup_range", "Median - 75th"),
                    "count": metrics.get("moveup_count", 0),
                    "color": "PRIMARY",  # Monochromatic
                },
                {
                    "name": "Luxury",
                    "range": metrics.get("luxury_range", "75th+"),
                    "count": metrics.get("luxury_count", 0),
                    "color": "PRIMARY",  # Monochromatic
                },
            ]
    
    # Map bands from metrics - all use PRIMARY for monochromatic design
    if bands:
        return [
            {
                "name": b.get("name", f"Band {i+1}"),
                "range": b.get("range", ""),
                "count": b.get("count", 0),
                "color": "PRIMARY",  # Monochromatic
            }
            for i, b in enumerate(bands)
        ]
    
    return None


def _get_property_type_breakdown(metrics: Dict) -> Optional[List[Dict]]:
    """
    Get property type breakdown for Market Snapshot.
    Returns list of {name, count, icon} or None
    
    V4.1: Updated to modern, minimal icons
    """
    # Try to get from metrics
    property_types = metrics.get("property_types", {})
    
    # Also check for individual fields
    sfr_count = property_types.get("sfr") or metrics.get("sfr_count", 0)
    condo_count = property_types.get("condo") or metrics.get("condo_count", 0)
    townhome_count = property_types.get("townhome") or metrics.get("townhome_count", 0)
    other_count = property_types.get("other") or metrics.get("other_type_count", 0)
    
    # If we have any counts, return the breakdown
    # V4.1: Modern icons - ◼ squares with labels
    if sfr_count or condo_count or townhome_count or other_count:
        result = []
        if sfr_count:
            result.append({"name": "Single Family", "count": sfr_count, "icon": "▪"})
        if condo_count:
            result.append({"name": "Condos", "count": condo_count, "icon": "▪"})
        if townhome_count:
            result.append({"name": "Townhomes", "count": townhome_count, "icon": "▪"})
        if other_count:
            result.append({"name": "Other", "count": other_count, "icon": "▪"})
        return result if result else None
    
    return None


def _get_price_tier_breakdown(metrics: Dict) -> Optional[List[Dict]]:
    """
    Get price tier breakdown for Market Snapshot.
    Returns list of {name, count, range, color} or None
    """
    # Try to get from metrics
    price_tiers = metrics.get("price_tiers", {})
    
    # Also check for individual fields
    entry_count = price_tiers.get("entry") or metrics.get("entry_tier_count", 0)
    moveup_count = price_tiers.get("moveup") or metrics.get("moveup_tier_count", 0)
    luxury_count = price_tiers.get("luxury") or metrics.get("luxury_tier_count", 0)
    
    # Get ranges if available
    entry_range = price_tiers.get("entry_range") or metrics.get("entry_tier_range", "Under $500K")
    moveup_range = price_tiers.get("moveup_range") or metrics.get("moveup_tier_range", "$500K - $1M")
    luxury_range = price_tiers.get("luxury_range") or metrics.get("luxury_tier_range", "$1M+")
    
    # If we have any counts, return the breakdown
    # Using PRIMARY for all tiers - opacity variations applied in template
    if entry_count or moveup_count or luxury_count:
        return [
            {"name": "Entry Level", "count": entry_count, "range": entry_range, "color": "PRIMARY", "opacity": "40"},
            {"name": "Move-Up", "count": moveup_count, "range": moveup_range, "color": "PRIMARY", "opacity": "70"},
            {"name": "Luxury", "count": luxury_count, "range": luxury_range, "color": "PRIMARY", "opacity": "100"},
        ]
    
    return None


# ============================================================================
# V4 FUNCTIONS: PDF-aligned email structure for Market Snapshot
# ============================================================================

def _get_hero_4_metrics(report_type: str, metrics: Dict) -> Tuple[
    Tuple[str, str], Tuple[str, str], Tuple[str, str], Tuple[str, str]
]:
    """
    V4: Get 4 hero metrics that match the PDF report header.
    Returns: ((label1, value1), (label2, value2), (label3, value3), (label4, value4))
    
    Each report type has its own relevant metrics matching the PDF ribbon.
    """
    # Extract common metrics
    median_close_price = metrics.get("median_close_price")
    median_list_price = metrics.get("median_list_price")
    total_active = metrics.get("total_active", 0)
    total_closed = metrics.get("total_closed", 0)
    avg_dom = metrics.get("avg_dom")
    moi = metrics.get("months_of_inventory")
    avg_ppsf = metrics.get("avg_ppsf")
    ctl = metrics.get("sale_to_list_ratio") or metrics.get("close_to_list_ratio")
    new_this_month = metrics.get("new_this_month", total_active)
    
    if report_type == "market_snapshot":
        # Matches PDF: Median Sale Price, Closed Sales, Avg DOM, MOI
        return (
            ("Median Sale Price", _format_price_clean(median_close_price or median_list_price)),
            ("Closed Sales", _format_number(total_closed)),
            ("Avg Days on Market", f"{avg_dom:.0f}" if avg_dom else "N/A"),
            ("Months of Inventory", f"{moi:.1f}" if moi else "N/A"),
        )
    
    elif report_type == "new_listings":
        # Matches PDF: Total Listings, Median List Price, Avg DOM, Avg $/SqFt
        return (
            ("New Listings", _format_number(total_active)),
            ("Median Price", _format_price_clean(median_list_price)),
            ("Avg DOM", f"{avg_dom:.0f}" if avg_dom else "N/A"),
            ("Avg $/SqFt", _format_price_clean(avg_ppsf) if avg_ppsf else "N/A"),
        )
    
    elif report_type == "inventory":
        # Matches PDF: Active Listings, New This Month, Median DOM, MOI
        return (
            ("Active Listings", _format_number(total_active)),
            ("New This Month", _format_number(new_this_month)),
            ("Median DOM", f"{avg_dom:.0f}" if avg_dom else "N/A"),
            ("Months of Inventory", f"{moi:.1f}" if moi else "N/A"),
        )
    
    elif report_type == "closed":
        # Matches PDF: Total Closed, Median Close Price, Avg DOM, Close-to-List
        return (
            ("Total Closed", _format_number(total_closed)),
            ("Median Price", _format_price_clean(median_close_price)),
            ("Avg DOM", f"{avg_dom:.0f}" if avg_dom else "N/A"),
            ("Close-to-List", f"{ctl:.1f}%" if ctl else "N/A"),
        )
    
    elif report_type == "price_bands":
        # Matches PDF: Total Listings, Median Price, Avg DOM, Price Range
        min_price = metrics.get("min_price")
        max_price = metrics.get("max_price")
        price_range = f"{_format_price_clean(min_price)}-{_format_price_clean(max_price)}" if min_price and max_price else "N/A"
        return (
            ("Total Listings", _format_number(total_active)),
            ("Median Price", _format_price_clean(median_list_price)),
            ("Avg DOM", f"{avg_dom:.0f}" if avg_dom else "N/A"),
            ("Price Range", price_range),
        )
    
    else:
        # Generic fallback
        return (
            ("Properties", _format_number(total_active)),
            ("Median Price", _format_price_clean(median_list_price or median_close_price)),
            ("Avg DOM", f"{avg_dom:.0f}" if avg_dom else "N/A"),
            ("MOI", f"{moi:.1f}" if moi else "N/A"),
        )


def _get_core_indicators(metrics: Dict) -> Tuple[
    Tuple[str, str], Tuple[str, str], Tuple[str, str]
]:
    """
    V4: Get 3 core indicator metrics that match the PDF report.
    Returns: ((label1, value1), (label2, value2), (label3, value3))
    
    PDF Core Indicators:
    1. New Listings (or Active Listings if new not available)
    2. Pending Sales
    3. Sale-to-List Ratio
    """
    # Extract metrics
    new_listings = metrics.get("new_listings_7d") or metrics.get("total_active", 0)
    total_pending = metrics.get("total_pending", 0)
    ctl = metrics.get("sale_to_list_ratio") or metrics.get("close_to_list_ratio")
    
    # Format values
    new_val = _format_number(new_listings)
    pending_val = _format_number(total_pending)
    ctl_val = f"{ctl:.1f}%" if ctl else "N/A"
    
    return (
        ("New Listings", new_val),
        ("Pending Sales", pending_val),
        ("Sale-to-List Ratio", ctl_val),
    )


# ═══════════════════════════════════════════════════════════════════════════
# D-085 — a sentence must name the price it means
# ═══════════════════════════════════════════════════════════════════════════
#
# THREE functions resolved one variable by precedence:
#
#     median_price = metrics.get("median_close_price") or metrics.get("median_list_price")
#
# and spent it on sentences that want different things — "homes SOLD at a median
# of", "median ASKING price of", "at a median SALE price". Every one of them
# renders correctly today and none is guaranteed to: the precedence happens to
# match because of which metrics each builder emits. `market_snapshot` emits
# both, so close wins and its sale sentences are right; `new_listings` emits only
# a list price, so its asking sentence is right. Correct by coincidence, across
# two files, with nothing stating the dependency.
#
# The entry recorded this in `_get_insight_paragraph`. It is also in
# `_get_quick_take` and `_get_conversation_starter` — three functions and nine
# sentences, not one and four.
#
# What makes it dangerous is the direction of the failure. Adding a close price
# to `build_inventory_result` is an obviously correct change to a builder, and it
# would silently turn *"42 active listings at a median of $450,000"* into a
# figure describing homes that have already sold. Demonstrated before the fix: a
# metrics dict carrying only a list price rendered *"18 homes sold at a median of
# $825K"* — the asking price, described as a sale price.
#
# So the kind is named at every site, and a sentence whose price is missing
# changes its WORDING rather than borrowing the other kind. A wrong figure reads
# as authoritative; a missing one reads as missing.

SOLD = "sold"       #: median_close_price — what homes actually transacted at
ASKING = "asking"   #: median_list_price — what sellers are asking
EITHER = "either"    #: a sentence that genuinely does not distinguish


def _median(kind: str, metrics: Dict) -> Optional[str]:
    """
    A formatted median price of the requested KIND, or None.

    None means "this sentence cannot be written as drafted" — never "use the
    other one". Returning a fallback price here would put the precedence bug
    back inside the function built to remove it.
    """
    close = metrics.get("median_close_price")
    lst = metrics.get("median_list_price")
    if kind == SOLD:
        value = close
    elif kind == ASKING:
        value = lst
    elif kind == EITHER:
        value = close or lst
    else:
        raise ValueError(f"unknown price kind: {kind!r}")
    return _format_price_clean(value) if value else None


def _get_insight_paragraph(
    report_type: str, 
    area: str, 
    metrics: Dict, 
    lookback_days: int,
    filter_description: str = None,
    sender_type: str = "REGULAR",
    total_found: int = 0,
    total_shown: int = 0,
    audience_name: str = None,
) -> str:
    """
    V14: Generate insight paragraph for reports with sender/audience awareness.
    
    First tries AI-generated insight via OpenAI (with full context),
    falls back to template-based text if AI is disabled or fails.
    """
    # V14: Try AI-generated insight first with full context
    try:
        from ..ai_insights import generate_insight, AI_INSIGHTS_ENABLED
        print(f"[INSIGHT] Generating for {report_type} in {area}, sender={sender_type}, AI_ENABLED={AI_INSIGHTS_ENABLED}")
        ai_insight = generate_insight(
            report_type=report_type,
            area=area,
            metrics=metrics,
            lookback_days=lookback_days,
            filter_description=filter_description,
            sender_type=sender_type,
            total_found=total_found,
            total_shown=total_shown,
            audience_name=audience_name,
        )
        if ai_insight:
            print(f"[INSIGHT] AI SUCCESS: {ai_insight[:80]}...")
            return ai_insight
        else:
            print(f"[INSIGHT] AI returned None, using fallback")
    except ImportError as e:
        print(f"[INSIGHT] Import error: {e}")
    except Exception as e:
        print(f"[INSIGHT] Exception: {e}")
    
    # Fallback: Template-based text (V13: More exciting and personable)
    print(f"[INSIGHT] Using FALLBACK template for {report_type}")
    # Extract key metrics for narrative
    total_active = metrics.get("total_active", 0)
    total_closed = metrics.get("total_closed", 0)
    median_price = metrics.get("median_close_price") or metrics.get("median_list_price")
    avg_dom = metrics.get("avg_dom")
    moi = metrics.get("months_of_inventory")
    avg_ppsf = metrics.get("avg_ppsf")
    ctl = metrics.get("sale_to_list_ratio") or metrics.get("close_to_list_ratio")
    
    # Build insight text based on report type
    price_str = _format_price_clean(median_price) if median_price else "varying prices"
    dom_str = f"{avg_dom:.0f} days" if avg_dom else "typical time"

    # D-085 clause fragments. Each names its kind; each collapses to "" when the
    # metric it needs is absent, so the sentence loses a clause rather than
    # gaining a wrong number.
    _sold = _median(SOLD, metrics)
    _asking = _median(ASKING, metrics)
    _sold_at = f" at a median of {_sold}" if _sold else ""
    _asking_of = f"with a median asking price of {_asking}" if _asking else ""
    
    ctl_str = f"{ctl:.1f}%" if ctl else None
    ppsf_str = f"${avg_ppsf:,.0f}/sq ft" if avg_ppsf else None

    # Inventory clauses for the `else` branches below.
    #
    # Those branches are reached precisely when `moi` is FALSY, and they used to
    # format it anyway — `f"{moi:.1f}"` on None raises TypeError, which
    # propagates through schedule_email_html() to send_schedule_email() and the
    # email is never sent. See tests/test_insight_paragraph_missing_metrics.py.
    #
    # Guarded on `is not None` rather than truthiness (the metric-tile code at
    # :1394 uses `if moi else "N/A"`). moi == 0 is a real figure — no active
    # listings against some closed ones — and stating "0.0 months of inventory"
    # is more useful than suppressing it. Only a genuinely absent value is
    # dropped, and when it is dropped the sentence must not still assert what
    # the number was going to support.
    _has_moi = moi is not None
    moi_with_clause = f" with {moi:.1f} months of inventory" if _has_moi else ""
    moi_and_clause = f"and {moi:.1f} months of inventory " if _has_moi else ""

    if report_type == "market_snapshot":
        # NOTE: these stay truthiness checks (`if moi`), deliberately. Routing
        # moi == 0 to the seller's-market branch looks more correct in the
        # abstract, but 0 is not a market reading here — it is a sentinel.
        # build_inventory_result (report_builders.py:468) sets moi = 0.0 when
        # there are NO closed sales, while build_market_snapshot_result:150
        # uses 99.9 for the same condition, and 6 of the 8 sample report types
        # (services/sample_report_data.py) ship moi = 0 as "not modelled".
        # Sending any of those to "Inventory is tight — excellent time to list"
        # would be confidently wrong. The sentinel disagreement is the real
        # defect; it is recorded rather than papered over here.
        if moi and moi < 3:
            return (
                f"Great news for sellers in {area}—the market is moving fast. "
                f"With only {moi:.1f} months of inventory and {total_closed} homes sold{_sold_at}, "
                f"buyers are competing for well-priced properties. "
                f"Homes are averaging {dom_str} on market, which means pricing right from day one is critical. "
                f"For buyers, acting decisively and coming in with strong offers is the best strategy in this environment."
            )
        elif moi and moi > 6:
            return (
                f"Buyers have excellent options in {area} right now. "
                f"With {moi:.1f} months of inventory and homes averaging {dom_str} on market, "
                f"there's room to find the perfect fit without rushing. "
                + (f"The median sale price sits at {_sold}, and sellers may be more open to negotiation. "
                   if _sold else "Sellers may be more open to negotiation. ") +
                f"For sellers, competitive pricing and strong presentation are essential to stand out in a market with more choices."
            )
        else:
            return (
                f"Healthy activity in {area} this month—{total_closed} families found their new home"
                + (f" at a median price of {_sold}. " if _sold else ". ") +
                f"Homes are averaging {dom_str} on market{moi_with_clause}, "
                + (
                    "suggesting a balanced environment for both buyers and sellers. "
                    if _has_moi
                    # Without an inventory figure there is nothing supporting a
                    # "balanced" reading, so the claim goes with the number.
                    else "which gives both buyers and sellers a clear read on current demand. "
                ) +
                f"Buyers have time to explore without the pressure of bidding wars, "
                f"while sellers in this range are still seeing solid demand for well-prepared homes."
            )

    elif report_type == "new_listings":
        return (
            f"Fresh opportunities in {area}—{total_active} new properties just hit the market"
            + (f" {_asking_of}. " if _asking else ". ") +
            f"Current inventory is averaging {dom_str} on market, "
            f"which signals healthy buyer interest without extreme urgency. "
            f"For buyers, this is a strong window to tour and compare before the best options go under contract. "
            f"Sellers entering the market now benefit from steady demand and motivated buyers."
        )

    elif report_type == "inventory":
        if moi and moi < 3:
            return (
                f"Inventory is tight in {area} with just {moi:.1f} months of supply—well below the balanced threshold. "
                + (f"{total_active} active listings at a median of {_asking} means competition is real. "
                   if _asking else f"{total_active} active listings means competition is real. ") +
                f"Homes are moving in an average of {dom_str}, rewarding buyers who act quickly with strong offers. "
                f"For sellers, this is an excellent time to list—limited supply is keeping upward pressure on prices."
            )
        elif moi and moi > 6:
            return (
                f"You have options in {area}—{total_active} active listings and {moi:.1f} months of inventory "
                + (f"means time to find exactly what you're looking for at a median of {_asking}. "
                   if _asking else "means time to find exactly what you're looking for. ") +
                f"Homes are averaging {dom_str} on market, giving buyers room to negotiate. "
                f"Sellers should focus on pricing strategically and making homes show-ready to attract serious offers "
                f"in a market where buyers have the luxury of comparison."
            )
        else:
            # Assembled then terminated, rather than each branch carrying its
            # own ending. Two seams came out of doing it the other way: the
            # no-price branch appended "right now" to a clause that already said
            # it ("in Glendora right now right now"), and stripping that left a
            # space before the full stop. Building the clauses and punctuating
            # once is the shape that cannot produce either.
            _opening = (
                f"The {area} market is well-balanced right now with {total_active} active listings"
                if _has_moi
                # "well-balanced" is an inference from moi sitting between 3 and
                # 6. With no figure, report the count without the verdict.
                else f"There are {total_active} active listings in {area} right now"
            )
            _clauses = " ".join(
                part for part in (moi_and_clause.strip(),
                                  f"at a median of {_asking}" if _asking else "")
                if part
            )
            return (
                (f"{_opening} {_clauses}. " if _clauses else f"{_opening}. ")
                + f"Homes are averaging {dom_str} on market—neither rushed nor stagnant. "
                f"Buyers can explore confidently without extreme competition, "
                f"while sellers benefit from consistent demand that rewards well-priced, well-presented homes."
            )

    elif report_type == "closed":
        ctl_display = f"Buyers paid {ctl_str} of asking price, " if ctl_str else ""
        return (
            f"The {area} market is active—{total_closed} homes sold in the last {lookback_days} days"
            + (f" at a median of {_sold}. " if _sold else ". ")
            + f"{ctl_display}showing confidence in current property values. "
            f"Homes closed in an average of {dom_str}, reflecting steady buyer demand. "
            f"For sellers, these results confirm that well-priced properties are finding motivated buyers. "
            f"For buyers, the pace of sales underscores the importance of being prepared to move when the right home appears."
        )

    elif report_type == "price_bands":
        return (
            f"Price analysis for {area} over the last {lookback_days} days reveals where the market is most active. "
            f"This report segments listings into price bands to show where inventory and buyer demand concentrate. "
            # EITHER, deliberately: "the median" here describes the whole
            # distribution the bands are cut from, not a sale or an ask.
            + (f"The median sits at {_median(EITHER, metrics)} with homes averaging {dom_str} on market. "
               if _median(EITHER, metrics) else f"Homes are averaging {dom_str} on market. ")
            +
            f"Bands with faster turnover indicate stronger demand—useful for both buyers targeting competitive price points "
            f"and sellers positioning their listing price for maximum interest."
        )

    elif report_type == "new_listings_gallery":
        total_listings = metrics.get("total_listings", 0)
        min_price = metrics.get("min_price")
        max_price = metrics.get("max_price")
        min_str = _format_price_clean(min_price) if min_price else "various"
        max_str = _format_price_clean(max_price) if max_price else "price points"

        if filter_description:
            return (
                f"Fresh opportunities for {filter_description} buyers in {area}. "
                f"We found {total_listings} new listings in the last {lookback_days} days, "
                f"with prices ranging from {min_str} to {max_str}. "
                f"These curated properties match your specific criteria and represent the strongest options available right now. "
                f"Reach out to schedule showings on any that catch your eye—the best ones tend to move quickly."
            )
        else:
            return (
                f"The newest listings hitting the market in {area}—{total_listings} properties "
                + (f"listed in the last {lookback_days} days at a median of {_asking}. "
                   if _asking else f"listed in the last {lookback_days} days. ") +
                f"Prices range from {min_str} to {max_str}, offering options across multiple budgets. "
                f"Homes are averaging {dom_str} on market, so there's time to compare—but the standouts won't last. "
                f"Let me know which properties interest you and I'll arrange private showings."
            )

    elif report_type == "featured_listings":
        total_listings = metrics.get("total_listings", 0)
        max_price = metrics.get("max_price")
        max_str = _format_price_clean(max_price) if max_price else "premium pricing"

        return (
            f"Hand-picked properties showcasing the best of {area}. "
            f"These {total_listings} featured homes represent exceptional value and quality, "
            f"with prices reaching {max_str}. "
            f"Each one was selected for standout features—whether that's location, condition, or price relative to the market. "
            f"Reach out to schedule private showings on any that catch your attention."
        )

    else:
        return (
            f"Market report for {area} covering the last {lookback_days} days. "
            f"The median price sits at {price_str} with homes averaging {dom_str} on market. "
            f"These numbers reflect current conditions for both buyers and sellers in the area. "
            f"Review the full report for a detailed breakdown of activity, pricing trends, and opportunities."
        )


def _get_quick_take(report_type: str, area: str, metrics: Dict) -> str:
    """
    V10: Generate a professional market insight one-liner.
    Clean, data-focused language without emojis.
    """
    total_active = metrics.get("total_active", 0)
    total_closed = metrics.get("total_closed", 0)
    median_price = metrics.get("median_close_price") or metrics.get("median_list_price")
    avg_dom = metrics.get("avg_dom")
    moi = metrics.get("months_of_inventory")
    
    price_str = _format_price_clean(median_price) if median_price else None
    
    if report_type == "market_snapshot":
        if moi and moi < 3:
            return f"Seller's market conditions: {moi:.1f} months of inventory indicates strong demand in {area}."
        elif moi and moi > 6:
            return f"Buyer-favorable conditions: {moi:.1f} months of inventory provides negotiating leverage in {area}."
        elif total_closed and _median(SOLD, metrics):
            return f"{total_closed} closed transactions at {_median(SOLD, metrics)} median price point in {area}."
        else:
            return f"Current market conditions and key indicators for {area}."
    
    elif report_type in ("new_listings", "new_listings_gallery"):
        if total_active and _median(ASKING, metrics):
            return f"{total_active} new properties listed in {area} with a median asking price of {_median(ASKING, metrics)}."
        elif total_active:
            return f"{total_active} new listings now available in {area}."
        else:
            return f"Latest available properties in {area}."
    
    elif report_type == "closed":
        if total_closed and _median(SOLD, metrics):
            return f"{total_closed} properties closed in {area} at a {_median(SOLD, metrics)} median sale price."
        elif total_closed:
            return f"{total_closed} recent closings recorded in {area}."
        else:
            return f"Recent closed transactions in {area}."
    
    elif report_type == "featured_listings":
        return f"Selected properties currently available in {area}."
    
    else:
        return f"Market summary for {area}."


def _get_conversation_starter(report_type: str, area: str, metrics: Dict, listings: Optional[List[Dict]] = None) -> str:
    """
    V5: Generate a ready-to-text conversation starter for agents.
    This is what agents can copy and send to their clients.
    """
    total_active = metrics.get("total_active", 0)
    median_price = metrics.get("median_close_price") or metrics.get("median_list_price")
    price_str = _format_price_clean(median_price) if median_price else None
    
    # Try to get a featured listing for personalization
    featured_address = None
    featured_price = None
    if listings and len(listings) > 0:
        first = listings[0]
        featured_address = first.get("street_address")
        featured_price = _format_price_clean(first.get("list_price")) if first.get("list_price") else None
    
    if report_type in ("new_listings", "new_listings_gallery"):
        if featured_address and featured_price:
            return (
                f"Hey! Just saw a new listing at {featured_address} for {featured_price} - "
                f"thought of you. Want me to send you the details?"
            )
        elif total_active:
            return (
                f"Hey! {total_active} new listings just hit the market in {area}. "
                f"Want me to send you the ones that match what you're looking for?"
            )
        else:
            return (
                f"Hey! Some new listings just came up in {area}. "
                f"Let me know if you'd like to take a look!"
            )
    
    elif report_type == "market_snapshot":
        if price_str:
            return (
                f"Hey! Quick update on the {area} market - "
                f"median prices are at {price_str}. Want to chat about what this means for you?"
            )
        else:
            return (
                f"Hey! Just pulled the latest market data for {area}. "
                f"Let me know if you want to talk strategy!"
            )
    
    elif report_type == "closed":
        return (
            f"Hey! Just looked at recent sales in {area} - "
            f"some interesting comps. Want me to walk you through them?"
        )
    
    elif report_type == "featured_listings":
        if featured_address:
            return (
                f"Hey! I think you'll love this one - {featured_address}. "
                f"Free this weekend to take a look?"
            )
        else:
            return (
                f"Hey! Found some great properties in {area} I think you'll love. "
                f"When can we chat?"
            )
    
    else:
        return (
            f"Hey! Just pulled some fresh market data for {area}. "
            f"Let me know when you have a few minutes to chat!"
        )


def _build_preheader(report_type: str, area: str, metrics: Dict) -> str:
    """Build preheader text for email preview. V10: Professional tone without emojis."""
    config = REPORT_CONFIG.get(report_type, {})
    label = config.get("label", "Report")
    
    # Get a key metric for the preheader
    if report_type == "market_snapshot":
        count = metrics.get("total_active", 0)
        return f"{label} for {area}: {count} active listings, median prices, and market trends"
    elif report_type == "new_listings":
        count = metrics.get("total_active", 0)
        return f"{count} new listings in {area} - prices, photos, and property details"
    elif report_type == "closed":
        count = metrics.get("total_closed", 0)
        return f"{count} closed sales in {area} - sale prices and market activity"
    elif report_type == "price_bands":
        return f"Price analysis for {area} - entry, move-up, and luxury tier breakdown"
    elif report_type == "inventory":
        count = metrics.get("total_active", 0)
        return f"{count} active listings in {area} - current market inventory"
    else:
        return f"Your {label} for {area} is ready"


def schedule_email_html(
    account_name: str,
    report_type: str,
    city: Optional[str],
    zip_codes: Optional[list],
    lookback_days: int,
    metrics: Dict,
    pdf_url: str,
    unsubscribe_url: str,
    brand: Optional[Brand] = None,
    listings: Optional[List[Dict]] = None,
    preset_display_name: Optional[str] = None,
    filter_description: Optional[str] = None,
    sender_type: str = "REGULAR",
    total_found: int = 0,
    total_shown: int = 0,
    audience_name: Optional[str] = None,
    total_available: int = 0,
    showing: int = 0,
) -> str:
    """
    Generate HTML email for a scheduled report notification.
    
    V2: Complete redesign with V0-generated email-safe template.
    V14: Sender-aware AI insights with audience context.
    
    Features:
    - Gradient header with Outlook VML fallback
    - Dark mode support
    - Mobile responsive (metrics stack)
    - Extra stats row for Market Snapshot & Closed Sales
    - Price bands section for Price Bands report
    - Preheader text for email preview
    - Polished agent footer with circular photo
    - V14: AI insights adapt based on sender type and audience
    
    Args:
        account_name: Name of the account (for personalization)
        report_type: Type of report (market_snapshot, new_listings, etc.)
        city: City name (if city-based report)
        zip_codes: List of ZIP codes (if ZIP-based report)
        lookback_days: Number of days covered by the report
        metrics: Dictionary of key metrics to display
        pdf_url: Direct link to the PDF report
        unsubscribe_url: Link to unsubscribe from future emails
        brand: Optional brand configuration (for white-label output)
        sender_type: "REGULAR" (agent) or "INDUSTRY_AFFILIATE" (title company)
        total_found: Total listings in market (for AI context)
        total_shown: How many listings displayed (for AI context)
        audience_name: Preset audience (e.g., "First-Time Buyers")
    
    Returns:
        HTML string for the email body
    """
    # ═══════════════════════════════════════════════════════════════════════
    # TRUST BOUNDARY — everything below this block is safe by construction.
    #
    # DO NOT ADD PER-SITE ESCAPING BELOW. If you are reading this because you
    # noticed ~460 raw `{…}` interpolations in an HTML string and no template
    # engine, that instinct is right about the risk and wrong about the fix.
    # Escaping at the sites requires a correct judgement at every one of them,
    # and ~50 of them insert HTML fragments this module built (`*_html`,
    # `_build_*` returns) — escaping those renders the markup as visible text.
    # Sanitising the inputs once, here, makes that mistake structurally
    # impossible: fragments are assembled from values that are already clean.
    #
    # The channels, all confirmed by render rather than by reading:
    #   brand      — users.phone/job_title, affiliate_branding.*; user-editable
    #   listings   — SimplyRETS. VENDOR data, so injection needs one bad MLS
    #                record and no malicious account at all.
    #   arguments  — account_name, city, preset/filter/audience labels
    #   metrics    — string-valued entries (band labels and the like)
    #
    # URLs are a SEPARATE problem handled by safe_url(), not by escaping:
    # html.escape("javascript:…") is a no-op and the value stays live in an
    # href. See safe_url's docstring for why that matters more for the PDF
    # surfaces than for this one.
    # ═══════════════════════════════════════════════════════════════════════
    brand = _sanitize_brand(brand)
    account_name = _esc(account_name)
    city = _esc(city)
    zip_codes = [_esc(z) for z in zip_codes] if zip_codes else zip_codes
    report_type = _esc(report_type)
    preset_display_name = _esc(preset_display_name)
    filter_description = _esc(filter_description)
    audience_name = _esc(audience_name)
    metrics = _sanitize_metrics(metrics)
    listings = [_sanitize_listing(l) for l in listings] if listings else listings
    pdf_url = safe_url(pdf_url)
    # The unsubscribe URL is HMAC-built by send.py, never user data, and is
    # substituted per recipient after this render — scheme-checked anyway so
    # the rule holds for every href in the document without exception.
    unsubscribe_url = (
        unsubscribe_url if unsubscribe_url == _UNSUB_URL_SENTINEL
        else safe_url(unsubscribe_url)
    )

    # Extract brand values with defaults
    brand = brand or {}
    brand_name = brand.get("display_name") or account_name or "Market Reports"
    logo_url = brand.get("logo_url")
    email_logo_url = brand.get("email_logo_url")  # Separate logo for email headers
    # Normalised, not just defaulted. `or` only catches an empty value; these
    # columns accept any string on two of their three write paths, and the
    # result is interpolated both into compute_color_roles (which parses it as
    # hex) and directly into ~48 `style="…"` attributes below. An unparseable
    # value used to raise ValueError out of this function and stop the send.
    # ── The DEFAULTS, and why they changed ─────────────────────────────────
    # These were #6366f1 (indigo-500) and #8b5cf6 (violet-500). Both sit inside
    # D-098's unreachable band: the best text colour against #6366f1 scores
    # 4.47:1 and against #8b5cf6 scores 4.31:1, so no choice of label clears AA
    # on either. That made the DEFAULT the one brand in the product that could
    # not be fixed — not a hypothetical 5% of the colour space but the value
    # every account that has not picked a colour actually ships.
    #
    # `on_primary` may not adjust the fill (decided 2026-09-23) because the fill
    # is the affiliate's colour. A DEFAULT is not: nobody chose it, and it is
    # ours to set. So it is set to a value that works.
    #
    # #4F46E5 is not a new colour. It is already `DEFAULT_PRIMARY_COLOR` in
    # apps/web/lib/templates.ts:29 and apps/web/lib/social-templates.ts:14, and
    # apps/web/__tests__/TemplatesMapping.test.ts:285 asserts it. The email was
    # the only surface using a different default, which is its own small defect:
    # an unbranded account's PDF and its email did not match. Now they do.
    #
    #   #4f46e5: white on it 6.29:1 · as ink on the darkest card 5.74:1
    primary_color = normalize_hex_color(brand.get("primary_color"), "#4f46e5")  # Indigo-600
    # `accent_color` is not read: Design's emails are one brand colour. See
    # the 5TH PACKAGE header above `DARK_TINT`.
    rep_name = brand.get("rep_name")
    rep_title = brand.get("rep_title")
    rep_photo_url = brand.get("rep_photo_url")
    rep_phone = brand.get("rep_phone")
    # The href and the label are not the same string: the href must be a valid
    # tel: URI, the label stays as the agent typed it. None means the number
    # could not be made dialable, and the pill renders as text with no link.
    rep_phone_href = _tel_uri(rep_phone)
    rep_email = brand.get("rep_email")
    contact_line1 = brand.get("contact_line1") or rep_name
    contact_line2 = brand.get("contact_line2") or rep_title
    website_url = brand.get("website_url")

    # Every colour the blocks read, derived once from the one brand colour.
    tk = _tokens(primary_color)

    # Get report config
    config = REPORT_CONFIG.get(report_type, {
        "label": report_type.replace("_", " ").title(),
        "tagline": "Your Market Report",
        "section": "Market Overview",
    })
    # V6: Use preset_display_name if provided (e.g., "First-Time Buyer" instead of "New Listings Gallery")
    report_label = preset_display_name or config.get("label")
    tagline = config.get("tagline")
    section_label = config.get("section")
    has_extra_stats = config.get("has_extra_stats", False)
    has_price_bands = config.get("has_price_bands", False)
    has_property_types = config.get("has_property_types", False)
    has_price_tiers = config.get("has_price_tiers", False)
    
    # V4 features
    has_hero_4 = config.get("has_hero_4", False)
    has_core_indicators = config.get("has_core_indicators", False)
    has_insight = config.get("has_insight", False)
    
    # Format area for display
    if city:
        area_display = city
    elif zip_codes and len(zip_codes) > 0:
        if len(zip_codes) == 1:
            area_display = f"ZIP {zip_codes[0]}"
        elif len(zip_codes) <= 3:
            area_display = f"ZIPs {', '.join(zip_codes)}"
        else:
            area_display = f"{len(zip_codes)} ZIP codes"
    else:
        area_display = "Your Area"
    
    
    # V4: Get 4-metric hero row (for all V4 report types)
    if has_hero_4:
        (h1_label, h1_value), (h2_label, h2_value), (h3_label, h3_value), (h4_label, h4_value) = \
            _get_hero_4_metrics(report_type, metrics)
    
    # V4: Get core indicators for Market Snapshot
    if has_core_indicators:
        (ci1_label, ci1_value), (ci2_label, ci2_value), (ci3_label, ci3_value) = \
            _get_core_indicators(metrics)
    
    # V14: Get insight paragraph (with sender/audience-aware AI)
    insight_text = _get_insight_paragraph(
        report_type=report_type,
        area=area_display,
        metrics=metrics,
        lookback_days=lookback_days,
        filter_description=filter_description,
        sender_type=sender_type,
        total_found=total_found,
        total_shown=total_shown,
        audience_name=audience_name,
    ) if has_insight else None
    
    # Legacy: Get 3 metrics for non-V4 reports (V14: with total_shown for galleries)
    (m1_label, m1_value), (m2_label, m2_value), (m3_label, m3_value) = \
        _get_metrics_for_report_type(report_type, metrics, total_shown=total_shown)
    
    # Get extra stats if applicable (not used in V4 Market Snapshot)
    extra_stats = _get_extra_stats(report_type, metrics) if has_extra_stats else None
    
    # Get price bands if applicable
    price_bands = _get_price_bands(metrics) if has_price_bands else None
    
    # Get property type breakdown if applicable (Market Snapshot)
    property_types = _get_property_type_breakdown(metrics) if has_property_types else None
    
    # Get price tier breakdown if applicable (Market Snapshot)
    price_tiers = _get_price_tier_breakdown(metrics) if has_price_tiers else None
    
    # V5: Gallery reports - check for listings data
    has_gallery = report_type in ("new_listings_gallery", "featured_listings") and listings
    
    # V5: Listings table for inventory (and future: new_listings, closed)
    has_listings_table = config.get("has_listings_table", False) and listings
    
    # Build preheader
    preheader = _build_preheader(report_type, area_display, metrics)
    
    # V10: Quick Take (professional market insight)
    quick_take = _get_quick_take(report_type, area_display, metrics)
    
    header_logo_url = email_logo_url or logo_url

    # ------------------------------------------------------------------
    # V16: Build body via layout router
    # ------------------------------------------------------------------
    layout = LAYOUT_MAP.get(report_type, "market_narrative")

    if layout == "gallery":
        gallery_label = preset_display_name or ("New listings" if report_type == "new_listings_gallery" else "Featured listings")
        body_html = _build_gallery_body(
            insight_text=insight_text, listings=listings or [], quick_take=quick_take,
            tk=tk, gallery_label=gallery_label, filter_description=filter_description,
        )

    elif layout == "closed_sales":
        hero_val = h1_value if has_hero_4 else m1_value
        hero_lbl = h1_label if has_hero_4 else m1_label
        secondary = []
        if has_hero_4:
            secondary = [(h2_label, h2_value), (h3_label, h3_value), (h4_label, h4_value)]
        else:
            secondary = [(m2_label, m2_value), (m3_label, m3_value)]
        body_html = _build_closed_sales_body(
            insight_text=insight_text, hero_value=hero_val, hero_label=hero_lbl,
            listings=listings or [], stats=secondary, quick_take=quick_take,
            tk=tk, filter_description=filter_description,
        )

    elif layout == "analytics":
        hero_val = h1_value if has_hero_4 else m1_value
        hero_lbl = h1_label if has_hero_4 else m1_label

        band_stats = []
        bands_data = _get_price_bands(metrics) if has_price_bands else None
        if bands_data:
            total_count = sum(b.get("count", 0) for b in bands_data) or 1
            # `max_count` was computed here and used by nothing once D-115
            # stopped normalising the bars to the largest band. Removed rather
            # than left: an unused normaliser is an invitation to normalise.
            most_active_name = max(bands_data, key=lambda b: b.get("count", 0)).get("name")
            for b in bands_data:
                cnt = b.get("count", 0)
                pct = f"{cnt / total_count * 100:.0f}%" if total_count else "0%"
                is_top = (b.get("name") == most_active_name)
                band_stats.append((b.get("name", ""), str(cnt), pct, is_top))

        avg_dom = metrics.get("avg_dom")
        total_active = metrics.get("total_active", 0)
        supporting = []
        if bands_data:
            most_active = max(bands_data, key=lambda b: b.get("count", 0))
            supporting.append(("Most Active", most_active.get("name", "N/A")))
        supporting.append(("Avg DOM", f"{avg_dom:.0f} days" if avg_dom else "N/A"))
        supporting.append(("Total Analyzed", _format_number(total_active)))

        body_html = _build_analytics_body(
            insight_text=insight_text, hero_value=hero_val, hero_label=hero_lbl,
            trend_stats=band_stats, quick_take=quick_take, tk=tk,
            filter_description=filter_description,
            supporting_metrics=supporting,
            listings=listings,
        )

    else:
        hero_val = h1_value if has_hero_4 else m1_value
        hero_lbl = h1_label if has_hero_4 else m1_label
        secondary = []
        if has_hero_4:
            secondary = [(h2_label, h2_value), (h3_label, h3_value), (h4_label, h4_value)]
        if has_core_indicators:
            secondary += [(ci1_label, ci1_value), (ci2_label, ci2_value), (ci3_label, ci3_value)]
        if not secondary:
            secondary = [(m1_label, m1_value), (m2_label, m2_value), (m3_label, m3_value)]
        narrative_label = {
            "market_snapshot": "Recent activity",
            "new_listings":    "New listings",
            "open_houses":     "Open houses",
        }.get(report_type, "Notable listings")
        body_html = _build_market_narrative_body(
            insight_text=insight_text, hero_value=hero_val, hero_label=hero_lbl,
            stats=secondary, quick_take=quick_take, tk=tk,
            filter_description=filter_description,
            listings=listings,
            listings_label=narrative_label,
        )

    # ------------------------------------------------------------------
    # Truncation note + PDF CTA, after the body on every report type.
    #
    # `showing` is what this email DREW, not what the caller says it sent: the
    # layouts above draw every listing they are handed, so the two agree — and
    # where they did not (the old 2×2 gallery drew 4 of 8), the note was wrong.
    # ------------------------------------------------------------------
    _shown = len(listings) if listings else 0
    _total = total_available or total_found or _shown
    # D-077: the inventory headline counts every home for sale; the list under
    # it is the ones listed in the window, and its note says so.
    body_html += _build_truncation_note(
        _total, _shown, pdf_url, _pdf_has_all(report_type, _total),
        of_what=f"listed in the last {lookback_days} days" if report_type == "inventory" else "")
    body_html += _build_pdf_cta(pdf_url, tk, f"{area_display}, last {lookback_days} days")

    # ── The agent ───────────────────────────────────────────────────────────
    # Phone and email are built once and shown whether or not there is a photo:
    # they used to live in the photo branch only, so an agent without a headshot
    # sent reports carrying no way to reach them. The phone links only when it
    # resolves to a dialable tel: URI; the label is always as the agent typed it.
    agent_name = contact_line1 or rep_name or brand_name
    title = contact_line2 or rep_title
    title_line = " · ".join(x for x in (title, brand_name if brand_name != agent_name else None) if x)

    # ── Sender postal address (CAN-SPAM §7704(a)(5)) ────────────────────────
    #
    # THE ATTRIBUTION IS THE WHOLE DESIGN HERE, and it is why this is not a
    # one-line `or`. The line reads "<name> · <address>", so falling back
    # naively would print the AFFILIATE'S brand beside TRENDYREPORTS' address —
    # an affirmative statement that this business is located at an address that
    # is not theirs. A wrong address is a worse compliance posture than a
    # missing one. So the label travels with the value:
    #
    #   account set its own   "<their brand> · <their address>"
    #   falling back          "Sent by TrendyReports · <ours> · on behalf of <agent>"
    #
    # The fallback is reordered from Design's "Sent by TrendyReports on behalf
    # of <agent> · <ours>", which puts the agent's name immediately before our
    # address — the pairing this block exists to prevent. Ours comes first and
    # sits beside our own name.
    #
    # Both satisfy the statute, which requires the valid physical postal address
    # of the sender or of the person who initiated the message. Our name appears
    # only on the fallback, where it is the truth (Design, 5th package; owner
    # call 2026-10-28: follow Design, so no "Powered by" line). The address is
    # PLATFORM_POSTAL_ADDRESS — never the one in Design's mocks, which is wrong.
    postal_address = (brand.get("postal_address") or "").strip()
    if postal_address:
        postal_line = f"{brand_name} · {postal_address}"
    else:
        postal_line = f"{PLATFORM_SENDER_LABEL} · {PLATFORM_POSTAL_ADDRESS} · on behalf of {agent_name}"

    as_of = _today().strftime("%B %-d, %Y")
    signature_html = _build_signature(
        primary=tk["primary"], on_primary=tk["on_primary"], ink=tk["ink"],
        photo_url=rep_photo_url, initials=_initials(agent_name), agent_name=agent_name,
        title_line=title_line, phone=rep_phone, phone_href=rep_phone_href,
        email=rep_email,
        website_url=website_url,
        website_label=(website_url or "").replace("https://", "").replace("http://", "").rstrip("/"),
        reason_line=f"You're getting this because you're in {agent_name}'s contacts.",
        unsubscribe_url=unsubscribe_url,
        postal_line=postal_line,
        # Design's line adds "a dash means the MLS didn't report it". This email
        # prints "N/A" for a missing figure, not a dash, so that clause would be
        # false here and is left out. "the MLS" rather than Design's "CRMLS":
        # which MLS feeds an account is not known at render time.
        data_line=(f"Data from the MLS, {as_of}. Figures cover {area_display} "
                   f"for the last {lookback_days} days."),
    )

    masthead_html = _build_masthead(
        tk, header_logo_url, brand_name, as_of,
        f"{report_label} · {area_display} · Last {lookback_days} days",
    )

    # ── The shell (Design, 5th package) ─────────────────────────────────────
    #
    # `color-scheme: light dark` and the `tr-*` rules ARE the dark-mode support.
    # This said `light only` before, which no client honours reliably: Apple
    # Mail and Outlook inverted the card anyway and left brand text on navy at
    # 1.00–1.13:1. Now the dark palette is ours, and `.tr-brand` — the one
    # per-brand rule — is written from `dark_ink`, measured against the dark
    # tint. `tests/test_email_dark_mode.py` renders it with a dark scheme and
    # checks every text run.
    #
    # No web font: Design's stack is the system one, and the Outfit @import was
    # a request to Google from every open.
    html = f'''<!DOCTYPE html>
<html lang="en" xmlns:v="urn:schemas-microsoft-com:vml" xmlns:o="urn:schemas-microsoft-com:office:office">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="light dark">
<meta name="supported-color-schemes" content="light dark">
<meta http-equiv="X-UA-Compatible" content="IE=edge">
<meta name="x-apple-disable-message-reformatting">
<title>{report_label} · {area_display} — {brand_name}</title>
<!--[if mso]><noscript><xml><o:OfficeDocumentSettings><o:PixelsPerInch>96</o:PixelsPerInch></o:OfficeDocumentSettings></xml></noscript><![endif]-->
<style>
  body{{margin:0;padding:0;-webkit-text-size-adjust:100%;}}
  table{{mso-table-lspace:0;mso-table-rspace:0;}}
  img{{border:0;line-height:100%;outline:none;text-decoration:none;-ms-interpolation-mode:bicubic;}}
  a{{color:inherit;}}
  @media (prefers-color-scheme: dark){{
    .tr-page{{background:#111827 !important;}}
    .tr-card{{background:#1F2937 !important;border-color:#374151 !important;}}
    .tr-ink{{color:#F3F4F6 !important;}}
    .tr-body{{color:#D1D5DB !important;}}
    .tr-muted{{color:#9CA3AF !important;}}
    .tr-rule{{border-color:#374151 !important;}}
    .tr-tint{{background:{DARK_TINT} !important;}}
    .tr-cell{{background:{DARK_TINT} !important;border-color:#374151 !important;}}
    .tr-ph{{background:#374151 !important;}}
    .tr-brand{{color:{tk["dark_ink"]} !important;}}
    .tr-edge{{border:2px solid {tk["dark_ink"]} !important;}}
  }}
  @media only screen and (max-width:620px){{
    .tr-wrap{{width:100% !important;}}
    .tr-pad{{padding-left:20px !important;padding-right:20px !important;}}
    .tr-stack{{display:block !important;width:100% !important;}}
    .tr-hide{{display:none !important;}}
  }}
</style>
</head>
<body class="tr-page" style="margin:0;padding:0;background:#FAFAF7;">
<div style="display:none;font-size:1px;line-height:1px;max-height:0;max-width:0;opacity:0;overflow:hidden;mso-hide:all;">{preheader}&nbsp;&#847;&zwnj;&nbsp;&#847;&zwnj;&nbsp;&#847;&zwnj;&nbsp;&#847;&zwnj;&nbsp;&#847;&zwnj;&nbsp;&#847;&zwnj;</div>
<table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" class="tr-page" style="background:#FAFAF7;border-collapse:collapse;">
<tr><td align="center" style="padding:24px 12px;">
<!--[if mso]><table role="presentation" width="600" cellpadding="0" cellspacing="0" border="0"><tr><td><![endif]-->
<table role="presentation" cellpadding="0" cellspacing="0" border="0" width="600" class="tr-wrap tr-card" style="width:600px;max-width:600px;background:#ffffff;border-collapse:collapse;border:1px solid #E4E2DA;">
{masthead_html}
{body_html}
{signature_html}
</table>
<!--[if mso]></td></tr></table><![endif]-->
</td></tr>
</table>
</body>
</html>'''

    return html

def schedule_email_subject(
    report_type: str, 
    city: Optional[str], 
    zip_codes: Optional[list]
) -> str:
    """Generate email subject line for a scheduled report."""
    # Get report label
    config = REPORT_CONFIG.get(report_type, {})
    report_label = config.get("label", report_type.replace("_", " ").title())
    
    # Format area
    if city:
        area = city
    elif zip_codes and len(zip_codes) > 0:
        if len(zip_codes) == 1:
            area = f"ZIP {zip_codes[0]}"
        else:
            area = f"{len(zip_codes)} ZIP codes"
    else:
        area = "Your Area"
    
    return f"📊 Your {report_label} for {area} is Ready!"
