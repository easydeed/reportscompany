#!/usr/bin/env python3
"""One PDF for a human to read: every market report type, old page then new.

WHY THIS EXISTS
---------------
Every claim made about this surface so far is a measurement — page counts,
contrast ratios, row capacities, pixel fits. **None of them answers whether the
documents read better**, and that is the only question that matters to the
person whose customers receive them. Forty-six pages of new design have been
built without anyone outside the tooling looking at a single one.

So this renders both architectures on the same brand, through the same
paginator, and stitches them into one file in review order: a divider naming
the kind and what changed, then the OLD report, then the NEW one.

WHAT IT IS NOT
--------------
NOT the page-count measurement. That is `measure_market_pagination.py` at 120
listings, which is the figure the 58 -> 48 claim comes from. This pack renders
at `--listings` (default 24) because a realistic weekly report is what you can
judge the typography of, and fourteen pages of photo grid is not. **The page
counts in this pack will not match the measured ones and are not meant to.**

NOT PDFShift. Chromium's own `page.pdf` with PDFShift's margins, which is the
same path the measurement uses — no credentials, no network, and the geometry
that governs the real PDF is the margin reservation, which is replicated here.

HOW THE "OLD" PAGES ARE PRODUCED
--------------------------------
By emptying `V2_KINDS` for the first pass, so both passes go through today's
builder and paginator and the only variable is which page each kind renders.
Restored in a `finally`. Checking out an old commit would also change the
builder, the filters and the fixtures, and the comparison would be of two
different programs rather than two page architectures.

    python3 scripts/build_review_pack.py [--listings 24] [--out DIR]

Writes BOTH forms into `--out`, from the same rendered pages so they cannot
disagree: `market-reports-old-beside-new.pdf` for reading the surface whole,
and `by-report-type/` as one file per kind for flipping between a single
report's old and new pages — which is what judging a document involves.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps/worker/src"))
sys.path.insert(0, str(ROOT / "scripts"))

from measure_market_pagination import (  # noqa: E402
    MARGIN_BOTTOM, MARGIN_TOP, PDF_JS, find_chromium, report_data,
)
from worker import market_builder as mb  # noqa: E402

#: What to look at on each kind, in a reviewer's terms rather than a builder's.
#: Written per kind because "the new one is tidier" is not a review — the
#: question has to be specific enough to answer no to.
WHAT_CHANGED = {
    "closed": (
        "The stats bar became a band: one big number (homes sold) with the "
        "close-to-list ratio as a pill. The listings table gained a `vs. list` "
        "column that goes brand-coloured above asking.",
        "Does the band tell you more at a glance than the old stat cards? Is "
        "`vs. list` readable at that size? NOTE: the old page's headline "
        "number (117) is wrong and the new one (38) is right \u2014 see the "
        "cover."),
    "new_listings": (
        "Was six stat blocks, a chart and a long table across sixteen pages. "
        "Now the same band and a `Listed` column reading `Today` or `n d ago`.",
        "This is the biggest change on the surface. Does anything you relied "
        "on in the old analytics layout seem missing?"),
    "price_bands": (
        "The hero card, six stat cards and the SVG bar chart are gone. One "
        "table: band, a bar, listings, median, days, $/sq ft. No listings.",
        "The old version listed eight individual properties under the chart. "
        "The new one lists none. Is that the right trade for one page?"),
    "inventory": (
        "Same band as `closed`, with months-of-inventory as the pill and a "
        "`Status` column marking anything listed in the last week.",
        "THE TWELVE-MONTH SALES-PACE CHART IS GONE — Design's page has no "
        "chart slot. Do you want it back?"),
    "new_listings_gallery": (
        "Price moved onto the photo as a white plate; address and "
        "`{hood} / specs` beneath. Six cards on page 1, nine after.",
        "Does the price plate read cleanly over a real photo? (None load "
        "here — the tiles are the missing-photo state.)"),
    "open_houses": (
        "Same card as the listings gallery, with the viewing time on each "
        "card and From / To / Neighborhoods in the band.",
        "Design specified nine cards on page 1 and six fit. Does page 1 look "
        "underfilled at six?"),
    "featured_listings": (
        "Its own larger card: 18px price plate, 15px address, and beds / "
        "baths / sq ft stacked to the right.",
        "THIS ONE GOT LONGER — two pages to four. Is the bigger card worth "
        "two extra pages, or should it use the smaller shared card?"),
    "market_snapshot": (
        "NOT YET REDESIGNED. This is the current report, shown once.",
        "It is the last kind. Its band is the most complex in the package "
        "and three of its four stat deltas have no data source on this path."),
}

COVER = """<!doctype html><html><head><meta charset="utf-8"><style>
 @page {{ size: letter; margin: 0 }}
 body {{ margin:0; font-family: -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif;
        color:#14161A; padding:86px 72px; }}
 h1 {{ font-size:34px; line-height:1.15; margin:0 0 10px; letter-spacing:-0.02em }}
 .sub {{ font-size:13px; color:#5E636B; margin:0 0 34px }}
 h2 {{ font-size:15px; margin:30px 0 8px; letter-spacing:0.04em;
      text-transform:uppercase; color:{primary} }}
 p, li {{ font-size:13.5px; line-height:1.55; margin:0 0 9px }}
 ul {{ padding-left:18px; margin:0 0 9px }}
 .note {{ background:#F4F6F9; border-left:3px solid {primary};
         padding:12px 14px; font-size:12.5px; line-height:1.5 }}
 b {{ font-weight:650 }}
</style></head><body>
<h1>Market reports: the redesign, old beside new</h1>
<p class="sub">Seven of eight report types redesigned &middot; rendered {n} listings each
&middot; one brand (#1B365D) &middot; {date}</p>
<h2>How to read this</h2>
<p>For each report type: a divider page saying what changed and what to look at, then the
<b>current</b> report, then the <b>new</b> one. Eight types, in the order they were redesigned.</p>
<h2>What is measured, and what is not</h2>
<p>These are measured and hold: the surface went from <b>58 pages to 48</b> at 120 listings,
carrying the same listings at <b>19% higher density</b> (10.5 to 12.5 rows per page); there are
<b>zero contrast failures</b> across 5,058 text runs and six brand colours; and how much
page&nbsp;1 holds no longer depends on how long the AI narrative happens to be.</p>
<p><b>Nothing measured says the documents read better.</b> That is what this pack is for, and no
test can answer it.</p>
<div class="note"><b>The page counts in this pack are not the measured ones.</b> It renders {n}
listings per report so the typography is reviewable; the 58&nbsp;&rarr;&nbsp;48 figure comes from
a separate 120-listing run. Photos do not load in this renderer, so every gallery card shows the
missing-photo tile &mdash; that state is deliberate design, not a fault.</div>
<h2>One number in here is wrong, and it is the old page</h2>
<p>On the <b>current</b> `closed` report the headline reads <b>117 closed sales</b>; the new band
says <b>38</b>. <b>38 is right.</b> The old page's headline is the sum of every status count added
together &mdash; active plus pending plus closed &mdash; printed under whatever the report is
called. The new band reads the closed count.</p>
<p>This is a real defect in the live reports, found by putting the two side by side rather than by
any test. It is worst on <b>open houses</b>, where the two counts are the same listings counted
twice, so the headline is <b>exactly double</b> the real number. Filed; the redesign fixes it as a
side effect, which is not the same as having fixed it on purpose.</p>
<h2>Three things worth a decision</h2>
<ul>
<li><b>The inventory report lost its twelve-month sales-pace chart.</b> Design's page has no chart
slot. Nothing replaced it.</li>
<li><b>`price_bands` no longer lists individual properties</b> &mdash; eight of them before, none
now. It went two pages to one.</li>
<li><b>`featured_listings` got longer</b>, two pages to four, because its card is 88px taller than
the shared one.</li>
</ul>
</body></html>"""

DIVIDER = """<!doctype html><html><head><meta charset="utf-8"><style>
 @page {{ size: letter; margin: 0 }}
 body {{ margin:0; font-family: -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif;
        color:#14161A; padding:150px 72px 0; }}
 .n {{ font-family: ui-monospace, Menlo, monospace; font-size:11px; letter-spacing:0.12em;
      text-transform:uppercase; color:#5E636B; margin:0 0 14px }}
 h1 {{ font-size:40px; margin:0 0 6px; letter-spacing:-0.025em }}
 .pages {{ font-size:13px; color:#5E636B; margin:0 0 40px }}
 h2 {{ font-size:12px; letter-spacing:0.07em; text-transform:uppercase;
      color:{primary}; margin:26px 0 7px }}
 p {{ font-size:14px; line-height:1.55; margin:0 }}
 .ask {{ background:#F4F6F9; border-left:3px solid {primary}; padding:14px 16px;
        font-size:14px; line-height:1.55 }}
</style></head><body>
<p class="n">{idx} of 8</p>
<h1>{title}</h1>
<p class="pages">{pages}</p>
<h2>What changed</h2><p>{changed}</p>
<h2>What to look at</h2><div class="ask">{ask}</div>
</body></html>"""


def render(work: Path, pages: dict[str, str]) -> None:
    """Write each HTML and drive Chromium once over all of them."""
    for name, html in pages.items():
        (work / f"{name}.html").write_text(html, encoding="utf-8")
    (work / "types.json").write_text(json.dumps(sorted(pages)), encoding="utf-8")
    # THE JS GOES IN THE REPO, NOT THE WORK DIRECTORY. Node resolves `require`
    # from the SCRIPT's own directory upwards, not from `cwd` — so a renderer
    # written next to the HTML in /tmp cannot find `playwright` however the
    # subprocess is invoked. `measure_market_pagination.py` puts its copy in
    # `REPO` for exactly this reason and the reason was not written down, so it
    # was rediscovered here by a MODULE_NOT_FOUND.
    js = ROOT / "_build_review_pack.js"
    js.write_text(PDF_JS, encoding="utf-8")
    try:
        subprocess.run(
            ["node", str(js), str(work), find_chromium(),
             MARGIN_TOP, MARGIN_BOTTOM],
            cwd=str(ROOT), check=True,
        )
    finally:
        js.unlink(missing_ok=True)


def main() -> int:
    from pypdf import PdfReader, PdfWriter

    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--listings", type=int, default=24)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    kinds = [k for k in WHAT_CHANGED if k in mb.ALL_REPORT_TYPES]
    assert len(kinds) == len(mb.ALL_REPORT_TYPES), (
        f"WHAT_CHANGED covers {sorted(kinds)}; the surface has "
        f"{sorted(mb.ALL_REPORT_TYPES)}. A review pack missing a kind is a "
        f"review that silently did not cover it."
    )

    def build(kind: str) -> str:
        data = report_data(kind, args.listings)
        data["ai_insights"] = None if kind in mb.V2_KINDS else data.get("ai_insights")
        return mb.MarketReportBuilder(data).render_html()

    work = Path(tempfile.mkdtemp(prefix="review-pack-"))
    primary = "#1B365D"
    try:
        # Pass 1: the OLD architecture, with the seam emptied.
        original = mb.V2_KINDS
        try:
            mb.V2_KINDS = frozenset()
            old = {f"old__{k}": build(k) for k in kinds}
        finally:
            mb.V2_KINDS = original
        # Pass 2: as it is today.
        new = {f"new__{k}": build(k) for k in kinds}

        render(work, {**old, **new})
        counts = {}
        for name in list(old) + list(new):
            counts[name] = len(PdfReader(str(work / f"{name}.pdf")).pages)

        chrome = {"cover": COVER.format(
            n=args.listings, primary=primary,
            date="12 October 2026")}
        for i, kind in enumerate(kinds, 1):
            changed, ask = WHAT_CHANGED[kind]
            o, nw = counts[f"old__{kind}"], counts[f"new__{kind}"]
            pages = (f"Not yet redesigned &middot; {o} page"
                     f"{'s' if o != 1 else ''}, shown once"
                     if kind not in mb.V2_KINDS else
                     f"{o} page{'s' if o != 1 else ''} &rarr; "
                     f"<b>{nw} page{'s' if nw != 1 else ''}</b> at "
                     f"{args.listings} listings")
            chrome[f"div__{kind}"] = DIVIDER.format(
                idx=i, title=kind.replace("_", " "), pages=pages,
                changed=changed, ask=ask, primary=primary)
        render(work, chrome)

        out = Path(args.out) if args.out else work
        out.mkdir(parents=True, exist_ok=True)

        def parts(kind: str) -> list[str]:
            """Divider, then old, then new — the review order for one kind."""
            got = [f"div__{kind}", f"old__{kind}"]
            if kind in mb.V2_KINDS:
                got.append(f"new__{kind}")
            return [str(work / f"{n}.pdf") for n in got]

        # THE STITCHED PACK, and then the SAME pages as one file per kind.
        #
        # Both, because they answer different questions. A 46-page scroll is
        # right for reading the surface as a whole; eight separate files are
        # right for flipping between one report's old and new pages, which is
        # what judging a document actually involves. Built from the same
        # per-kind PDFs, so the two cannot disagree.
        writer = PdfWriter()
        writer.append(str(work / "cover.pdf"))
        for kind in kinds:
            for part in parts(kind):
                writer.append(part)
        dest = out / "market-reports-old-beside-new.pdf"
        with open(dest, "wb") as fh:
            writer.write(fh)

        loose = out / "by-report-type"
        loose.mkdir(parents=True, exist_ok=True)
        for stale in loose.glob("*.pdf"):
            # A regenerated set must not leave a renamed kind's file behind: a
            # stale PDF in a review folder is a document describing a build
            # nobody is looking at, which is this project's most-filed shape.
            stale.unlink()
        shutil.copyfile(str(work / "cover.pdf"),
                        str(loose / "0-how-to-read-this.pdf"))
        for i, kind in enumerate(kinds, 1):
            one = PdfWriter()
            for part in parts(kind):
                one.append(part)
            name = f"{i}-{kind.replace('_', '-')}.pdf"
            with open(loose / name, "wb") as fh:
                one.write(fh)

        print(f"{len(PdfReader(str(dest)).pages)} pages -> {dest}")
        print(f"{len(list(loose.glob('*.pdf')))} loose files -> {loose}\n")
        print(f"{'kind':24s} {'old':>4s} {'new':>4s}   at {args.listings} listings")
        print("-" * 52)
        for kind in kinds:
            o, nw = counts[f"old__{kind}"], counts[f"new__{kind}"]
            mark = "" if kind in mb.V2_KINDS else "  (unwired)"
            print(f"{kind:24s} {o:4d} {nw:4d}{mark}")
        return 0
    finally:
        if not args.out:
            print(f"(working files in {work})")
        else:
            shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
