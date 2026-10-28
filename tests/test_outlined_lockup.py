"""The Ticker lockup: live text on the web, outlined shapes in email.

Design's lockup SVGs set "Trendy" and "Reports" as `<text>` in Plus Jakarta
Sans. The web app loads that font (next/font), so `components/logo.tsx` inlines
the live-text lockup and it draws as designed. A mail client loads no web
font, and would draw the same file in a system typeface — so email uses
`public/email/trendy-lockup-{light,dark}@3x.png`, rendered from outlined paths
made by `scripts/outline_lockup.py`. Mail clients do not render SVG, hence PNG.

The outline was checked against a browser render of the live text with the
font loaded: 0.035% of pixels differ (anti-aliasing), against 19.4% for the
live text without the font.
"""
import re
import struct
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "apps/web/public"
EMAIL = PUBLIC / "email"
LOGO_TSX = ROOT / "apps/web/components/logo.tsx"


def _strip(svg):
    return re.sub(r"<metadata>.*?</metadata>", "", svg, flags=re.S)


@pytest.mark.parametrize("v", ["light", "dark"])
def test_the_email_lockup_has_no_live_text(v):
    svg = (EMAIL / f"trendy-lockup-{v}-outlined.svg").read_text()
    assert "<text" not in svg and "font-family" not in svg, (
        "the email lockup must be shapes: a mail client has no Plus Jakarta Sans")


@pytest.mark.parametrize("v", ["light", "dark"])
def test_the_outline_has_the_live_lockups_geometry(v):
    live = _strip((PUBLIC / f"trendy-lockup-{v}.svg").read_text())
    outl = (EMAIL / f"trendy-lockup-{v}-outlined.svg").read_text()
    for pat in (r'viewBox="[^"]+"', r'<rect [^>]+>', r'<g transform="[^"]+">'):
        a, b = re.search(pat, live).group(0), re.search(pat, outl).group(0)
        assert a.replace("></rect>", "/>").rstrip("/>") == b.rstrip("/>"), (pat, a, b)


def test_the_inline_web_lockup_matches_the_files():
    tsx = LOGO_TSX.read_text()
    live = _strip((PUBLIC / "trendy-lockup-light.svg").read_text())
    vb = re.search(r'viewBox="([^"]+)"', live).group(1)
    width = re.search(r'<rect x="150" y="8" width="(\d+)"', live).group(1)
    assert f'viewBox="{vb}"' in tsx
    assert f'<rect x="150" y="8" width="{width}"' in tsx


@pytest.mark.parametrize("v", ["light", "dark"])
def test_reports_fits_inside_its_pill(v):
    """
    Design's pill was 86 wide in a 236 viewBox; in Plus Jakarta Sans "Reports"
    ends at x 237.7, so the "s" was clipped. The pill is 98: the word must end
    inside it with room to spare, on the outline where the coordinates are real.
    """
    svg = (EMAIL / f"trendy-lockup-{v}-outlined.svg").read_text()
    paths = re.findall(r'<path fill="[^"]+" d="([^"]+)"', svg)
    reports = paths[-1]
    xs = [float(x) for x in re.findall(r"(-?\d+(?:\.\d+)?)\s+-?\d+(?:\.\d+)?", reports)]
    rect = re.search(r'<rect x="(\d+)" y="\d+" width="(\d+)"', svg)
    right = int(rect.group(1)) + int(rect.group(2))
    assert max(xs) <= right - 6, f"'Reports' ends at {max(xs):.1f}, the pill at {right}"


@pytest.mark.parametrize("v", ["light", "dark"])
def test_the_email_pngs_are_3x_with_transparency(v):
    data = (EMAIL / f"trendy-lockup-{v}@3x.png").read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    w, h, depth, colour = struct.unpack(">IIBB", data[16:26])
    assert (w, h) == (372, 72), "3x of the 124x24 the email header shows it at"
    assert colour == 6, "RGBA, so the lockup sits on the card in both schemes"


def test_white_png_stays_because_sent_emails_load_it():
    """
    Every account email sent before the new shell, and the failure notice and
    home-value email until theirs ship, load https://www.trendyreports.io/white.png.
    Emails already in inboxes keep that URL for ever. Deleting the file breaks
    the logo in all of them.
    """
    assert (PUBLIC / "white.png").is_file()


def test_nothing_in_the_web_app_renders_the_lockup_through_an_img():
    """An <img> of the live-text SVG cannot see next/font and would fall back."""
    offenders = []
    for f in (ROOT / "apps/web").rglob("*.tsx"):
        if "node_modules" in f.parts:
            continue
        for n, line in enumerate(f.read_text(errors="ignore").splitlines(), 1):
            if re.search(r"trendy-lockup-(light|dark)\.svg", line):
                offenders.append(f"{f.relative_to(ROOT)}:{n}")
    assert not offenders, offenders
