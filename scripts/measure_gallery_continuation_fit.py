#!/usr/bin/env python3
"""How many photo-grid rows fit on a market continuation page, measured.

THE QUESTION, AND WHY IT IS NOT A QUESTION FOR DESIGN
-----------------------------------------------------
Design's per-kind spec gives `new_listings_gallery` a **3x2** photo grid and
`open_houses` a **3x3** grid described as "same card as listings". Their
continuation-pages section covers only the three table kinds, so what a gallery
continuation page carries is unstated — and the two readings differ by eleven
pages across those two kinds.

But page 1 carries the fixed masthead band and a continuation page does not, and
their own spec already puts **nine of the same card** on a page that has a band.
So the gap is plausibly geometry rather than taste, and geometry is measurable.
Jerry's call, 2026-10-07: measure it rather than spend a fourth round asking for
a number we could take ourselves.

WHY THIS MEASURES OUR RENDER AND NOT DESIGN'S REFERENCE FILE
------------------------------------------------------------
The first attempt drove `Report Page.dc.html` in Chromium through
`window.__dcSetProps`. It cannot work in this container and should not be made
to: the file loads React from unpkg and Geist from Google Fonts, both of which
the browser refuses with `ERR_CERT_AUTHORITY_INVALID` because Chromium does not
trust the agent proxy's CA — and the remedy for that is to disable certificate
verification, which is not on the table. Vendoring React, two font families and
the photos would measure a document assembled differently from the one Design
looks at, which is the fixture-is-not-production shape with extra steps.

**The geometry that governs the PDF is ours**, because the PDF is rendered from
`MarketReportBuilder`'s HTML through PDFShift, with our fonts and our card. So
this measures the card we actually paint, in the page box a market PDF actually
has, and reports the headroom. Design's type sizes are the remaining variable
and are reported as a delta rather than guessed at.

    letter 11in - (0.44in header + 0.89in footer reserved) = 9.67in = 928px @96

NOT A GATE. Needs a real browser, and CI has none — the same reason
`measure_market_pagination.py` is a script. `find_chromium` is its third copy in
this repo; the alternative is a shared helper module for three four-line
functions, which is a change to two working scripts for no measurement.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps/worker/src"))
sys.path.insert(0, str(ROOT / "apps/worker/tests"))

#: Body height of a market PDF page, in CSS pixels at 96dpi.
BODY_PX = 9.67 * 96

#: The three kinds with a photo grid, and Design's stated page-1 grid.
GRID_KINDS = {
    "new_listings_gallery": {"cols": 3, "rows": 2},
    "open_houses": {"cols": 3, "rows": 3},
    "featured_listings": {"cols": 2, "rows": 2},
}

#: The 2026-10-07 measurement, taken against the LEGACY gallery page.
#:
#: Re-measured on 2026-10-10 because the architecture under it changed: the
#: three gallery kinds moved onto Design's `_v2` page, whose card moves the
#: price onto the photo (so the info block loses a 23px line), sets the photo
#: from the column width instead of a fixed 180px, and sits in a body with
#: different padding. **A fit measured against a page that has been replaced
#: describes nothing** — the same rule as a contrast baseline outliving its
#: template, applied to a geometry measurement.
#:
#: The page BOX did not change: `pdf_engine.py`'s 0.44in header and 0.89in
#: footer reserve are untouched since PR #101, so the 928px body is the same.
#: What moved is the card.
LEGACY_2026_10_07 = {
    "card_px": 258.0,
    "row_gap_px": 8.0,
    "rows_fit_continuation": 3,
    "headroom_after_3_rows_px": 138.0,
}

#: Design's stated type for the listings/gallery card, from the market README's
#: per-kind table. The card's own height is not stated; these are.
DESIGN_CARD_TYPE = {
    "address_px": 13, "address_weight": 600,
    "meta_px": 11.5,
    "price_plate_px": 15, "price_plate_weight": 700,
}

MEASURE_JS = r"""
() => {
  // Found by COMPUTED STYLE, not by class name: a renamed class should make
  // this return an error, not zero rows.
  const all = [...document.querySelectorAll('*')];
  const grids = all.filter(el => {
    const cs = getComputedStyle(el);
    if (cs.display !== 'grid') return false;
    const cols = cs.gridTemplateColumns.split(' ').filter(Boolean).length;
    return cols >= 2 && el.getBoundingClientRect().height > 80;
  });
  if (!grids.length) return { error: 'no photo grid found' };
  const grid = grids.sort((a, b) => b.getBoundingClientRect().height -
                                     a.getBoundingClientRect().height)[0];
  const cs = getComputedStyle(grid);
  const cards = [...grid.children].filter(
      c => c.getBoundingClientRect().height > 10);
  const heights = cards.map(c => c.getBoundingClientRect().height);

  // The text block under the photo, so Design's type sizes can be compared
  // against what ours actually costs in height.
  let textBlock = null;
  if (cards.length) {
    const first = cards[0];
    // BY COMPUTED STYLE, NOT BY INLINE ATTRIBUTE. The first version was
    // `first.querySelector('img, [style*="background-image"]')`, which finds a
    // card WITH a photo url and misses the missing-photo tile — so against the
    // `_v2` page, where a headless render resolves no photos and every card is
    // the tile, it reported `photo_px: 0` and folded the whole card into
    // `text_px`. The card height was still right (it is read off the card), so
    // the FIT was correct and only the breakdown was wrong, which is the quiet
    // kind: a plausible split nobody would question.
    //
    // `background-size: cover` is what both the legacy card and the `_v2` one
    // set on their photo box, with or without a url.
    const img = [...first.querySelectorAll('*')].find(el => {
      const cs = getComputedStyle(el);
      // THREE WAYS A PHOTO BOX RESERVES HEIGHT, and the `_v2` card uses the
      // third. `aspect-ratio` is how a width-driven grid reserves its box; the
      // legacy card used a fixed height with `background-size: cover`. Asking
      // only about `cover` missed the `_v2` tile twice over — once because the
      // `background` shorthand had reset it, and once because `cover` is not
      // what makes the box in the first place.
      return cs.aspectRatio !== 'auto'
          || cs.backgroundSize === 'cover'
          || (el.tagName === 'IMG' && el.getBoundingClientRect().height > 10);
    });
    const imgH = img ? img.getBoundingClientRect().height : 0;
    textBlock = {
      card_px: first.getBoundingClientRect().height,
      photo_px: imgH,
      text_px: first.getBoundingClientRect().height - imgH,
      font_sizes: [...first.querySelectorAll('*')]
        .map(e => parseFloat(getComputedStyle(e).fontSize))
        .filter(n => n > 0),
    };
  }
  return {
    cols: cs.gridTemplateColumns.split(' ').filter(Boolean).length,
    rowGap: parseFloat(cs.rowGap) || 0,
    nCards: cards.length,
    cardHeights: heights.map(h => Math.round(h * 10) / 10),
    cardHeight: heights.length ? Math.max(...heights) : null,
    first: textBlock,
  };
}
"""


def find_chromium() -> str:
    """Same two-location resolution as the other two measurement scripts."""
    roots = [Path(os.environ["PLAYWRIGHT_BROWSERS_PATH"])] if os.environ.get(
        "PLAYWRIGHT_BROWSERS_PATH") else [Path("/opt/pw-browsers")]
    roots.append(Path.home() / ".cache/ms-playwright")
    for root in roots:
        for candidate in sorted(root.glob("chromium-*/chrome-linux/chrome"),
                                reverse=True):
            return str(candidate)
    return ""


def rows_that_fit(budget: float, card: float, gap: float) -> int:
    """Rows of `card` height that fit in `budget`, `gap` between them."""
    if card <= 0:
        return 0
    n, used = 0, 0.0
    while True:
        need = card if n == 0 else card + gap
        if used + need > budget:
            return n
        used += need
        n += 1


def main() -> int:
    from playwright.sync_api import sync_playwright
    from measure_market_pagination import report_data  # noqa: E402
    from worker.market_builder import MarketReportBuilder  # noqa: E402

    report = {"body_px": round(BODY_PX, 1),
              "design_card_type": DESIGN_CARD_TYPE, "kinds": {}}
    exe = find_chromium()
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=exe or None)
        page = browser.new_page(viewport={"width": 816, "height": 1056})
        for report_type, stated in GRID_KINDS.items():
            data = report_data(report_type, 40)
            data["ai_insights"] = None  # Design removes it from these kinds
            html = MarketReportBuilder(data).render_html()
            page.set_content(html, wait_until="load")
            page.wait_for_timeout(300)
            geom = page.evaluate(MEASURE_JS)
            if geom.get("error"):
                report["kinds"][report_type] = geom
                continue
            card, gap = geom["cardHeight"], geom["rowGap"]
            three = 3 * card + 2 * gap
            legacy_head = LEGACY_2026_10_07["headroom_after_3_rows_px"]
            report["kinds"][report_type] = {
                "design_states_page_1": f"{stated['cols']}x{stated['rows']}",
                "legacy_card_px": LEGACY_2026_10_07["card_px"],
                "legacy_headroom_after_3_rows_px": legacy_head,
                "headroom_moved_px": round(
                    (BODY_PX - three) - legacy_head, 1),
                "a_fourth_row_would_need_px": round(card + gap, 1),
                "a_fourth_row_fits": (BODY_PX - three) >= (card + gap),
                "our_grid_cols": geom["cols"],
                "card_px": round(card, 1),
                "row_gap_px": round(gap, 1),
                "photo_px": round(geom["first"]["photo_px"], 1),
                "text_px": round(geom["first"]["text_px"], 1),
                "font_sizes_px": sorted(set(geom["first"]["font_sizes"])),
                "rows_fit_continuation": rows_that_fit(BODY_PX, card, gap),
                "three_rows_px": round(three, 1),
                "headroom_after_3_rows_px": round(BODY_PX - three, 1),
                "headroom_as_fraction_of_a_card": round(
                    (BODY_PX - three) / card, 2) if card else None,
            }
        browser.close()

    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
