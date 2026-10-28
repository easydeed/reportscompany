#!/usr/bin/env python3
"""Convert the Ticker lockup's lettering to outlined paths.

    PYTHONPATH=<fonttools+uharfbuzz> python3 scripts/outline_lockup.py \
        FONT_700.ttf FONT_800.ttf OUT_DIR

WHY. Design's lockups (`apps/web/public/trendy-lockup-{light,dark}.svg`) set
"Trendy" and "Reports" as live `<text>` in Plus Jakarta Sans. On the web app the
font is loaded by next/font, so that is fine. A mail client loads no web font:
the same file there would draw in whatever system typeface the client has —
the failure that put the atlas reports in Times New Roman. So the email header
needs the letters as shapes.

HOW. Each word is shaped with HarfBuzz (so kerning matches what a browser
draws), and each glyph's outline is written as an SVG path at the size,
position and letter-spacing the live-text SVG uses. The rect and the triangle
are copied as they are. The output is checked against a browser render of the
live-text original by `tests/test_outlined_lockup.py`.

The fonts are the static 700 and 800 instances Google Fonts serves for Plus
Jakarta Sans (OFL). They are inputs, not committed.
"""
import sys
from pathlib import Path

import uharfbuzz as hb
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

#: The lockup's geometry, from Design's SVG — with the pill widened from 86 to
#: 98 (and the viewBox from 236 to 248) so "Reports" fits it in this font.
VIEW_W, PILL_W = 248, 98
WORDS = (
    # text, weight, size, x, baseline y, letter-spacing
    ("Trendy", 800, 44, 0, 38, -2),
    ("Reports", 700, 15, 180, 28, 0),
)
PALETTES = {
    "light": {"ink": "#0F172A", "tag": "#D1FAE5", "tag_ink": "#065F46"},
    "dark": {"ink": "#FFFFFF", "tag": "#065F46", "tag_ink": "#D1FAE5"},
}


def word_path(font_path, text, size, x0, y0, spacing):
    blob = hb.Blob.from_file_path(str(font_path))
    face = hb.Face(blob)
    font = hb.Font(face)
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(font, buf, {"kern": True, "liga": True})

    tt = TTFont(str(font_path))
    glyph_set = tt.getGlyphSet()
    order = tt.getGlyphOrder()
    scale = size / tt["head"].unitsPerEm
    pen = SVGPathPen(glyph_set, ntos=lambda v: f"{v:.2f}".rstrip("0").rstrip("."))
    x = x0
    for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
        name = order[info.codepoint]
        # Font units are y-up; SVG is y-down. Scale, flip, then move to the pen.
        t = TransformPen(pen, (scale, 0, 0, -scale, x + pos.x_offset * scale,
                               y0 - pos.y_offset * scale))
        glyph_set[name].draw(t)
        x += pos.x_advance * scale + spacing
    return pen.getCommands()


def lockup_svg(f700, f800, palette):
    c = PALETTES[palette]
    fonts = {700: f700, 800: f800}
    paths = []
    for text, weight, size, x, y, spacing in WORDS:
        fill = c["ink"] if text == "Trendy" else c["tag_ink"]
        d = word_path(fonts[weight], text, size, x, y, spacing)
        paths.append((text, fill, d))
    trendy, reports = paths
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{VIEW_W}" height="48" viewBox="0 0 {VIEW_W} 48" '
        'role="img" aria-label="Trendy Reports">'
        f'<path fill="{trendy[1]}" d="{trendy[2]}"/>'
        f'<rect x="150" y="8" width="{PILL_W}" height="28" rx="6" fill="{c["tag"]}"/>'
        f'<g transform="translate(160 14) scale(1.15)"><path d="M7 2 L12 9 L2 9 Z" fill="{c["tag_ink"]}"/></g>'
        f'<path fill="{reports[1]}" d="{reports[2]}"/>'
        '</svg>\n'
    )


def main():
    f700, f800, out = (Path(a) for a in sys.argv[1:4])
    out.mkdir(parents=True, exist_ok=True)
    for palette in PALETTES:
        p = out / f"trendy-lockup-{palette}-outlined.svg"
        p.write_text(lockup_svg(f700, f800, palette))
        print(p)


if __name__ == "__main__":
    main()
