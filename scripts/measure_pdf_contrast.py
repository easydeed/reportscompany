"""The first contrast measurement the market and property PDFs have ever had.

WHY A BROWSER AND NOT THE EXISTING WALKER
-----------------------------------------
`apps/worker/tests/_contrast_audit.py` resolves backgrounds from inline
`style="…"` attributes, which is correct for email and useless here: the PDF
templates set every colour from a `<style>` block, through classes. Pointed at
a market render it sees a document of black-on-white and reports nothing —
passing while covering nothing, which is the one failure mode a gate must not
have (docs/TEST_DURABILITY.md).

The fix is not to write a CSS cascade in Python and hope it matches. **These
documents are rendered by a real browser** — PDFShift drives Chromium — so the
ground truth is `getComputedStyle`, and anything else is a model of it. This
script asks the browser directly. `_contrast_audit.py`'s new stylesheet
resolver is then checked against these numbers rather than against my reading
of the CSS (scripts/crosscheck_contrast_resolvers.py).

WHAT IT MEASURES
----------------
Every text node in every market report type and every property theme, across
the six brand colours the email audit already uses, so the two surfaces are
comparable. For each: the computed text colour, the nearest ancestor that
actually paints a background, and the ratio between them.

  * a semi-transparent text colour is flattened over the background it sits on
  * a semi-transparent background is flattened over whatever is behind it
  * a gradient yields every stop, and the text is measured against each — text
    on a gradient must be readable at both ends (D-097)
  * WCAG's large-text allowance is APPLIED, not ignored: >=24px, or >=18.66px
    at weight 700, needs 3:1 rather than 4.5:1. The email walker deliberately
    reports everything at 4.5:1 and leaves the judgement to the reader; here
    there are hundreds of headings and that would bury the real findings. Both
    numbers are printed so nothing is hidden by the choice.

WHAT IT DOES NOT MEASURE, STATED SO THE NUMBER IS NOT OVERREAD
---------------------------------------------------------------
  * **SVG text is measured against the nearest HTML ancestor's background**,
    because an SVG has no background of its own and resolving what a `<rect>`
    paints underneath a `<text>` means geometry, not style. In these charts the
    labels sit outside the bars, so this is right today and would silently
    become wrong if a label moved inside one.
  * Text hidden by `display:none`, `visibility:hidden`, `opacity:0` or a zero
    box is skipped. Text hidden by being painted the same colour as its
    background is NOT skipped — that is a 1.00:1 finding and the point.
  * Images. Text over a photo is reported against whatever CSS background is
    behind the image, which may be nothing like what the reader sees.

    python3 scripts/measure_pdf_contrast.py            # the report
    python3 scripts/measure_pdf_contrast.py --json OUT # the raw findings
"""
import json
import os
import subprocess
import sys
import tempfile
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "apps/worker/src"))

#: The same six the email audit uses (test_email_contrast.BRANDS), so a finding
#: on one surface can be compared with the same brand on the other.
BRANDS = [
    ("demo_title", "#DC2626"),
    ("luxury_estates", "#0D9488"),
    ("coastal", "#0E7490"),
    ("amber", "#F59E0B"),
    ("lime", "#84CC16"),
    ("violet", "#7C3AED"),
]

JS = r"""
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const WALK = () => {
  const out = [];
  let covered = 0, unresolved = 0, offscreen = 0;
  const offscreenWhat = [];

  const parseColor = (s) => {
    const m = /rgba?\(\s*([\d.]+)[,\s]+([\d.]+)[,\s]+([\d.]+)(?:[,\s/]+([\d.%]+))?\s*\)/i.exec(s || '');
    if (!m) return null;
    let a = m[4] === undefined ? 1 : (String(m[4]).endsWith('%') ? parseFloat(m[4]) / 100 : parseFloat(m[4]));
    return { r: +m[1], g: +m[2], b: +m[3], a: isNaN(a) ? 1 : a };
  };
  const hex = (c) => '#' + [c.r, c.g, c.b].map(v => Math.round(v).toString(16).padStart(2, '0')).join('');
  const over = (fg, bg) => ({
    r: fg.r * fg.a + bg.r * (1 - fg.a),
    g: fg.g * fg.a + bg.g * (1 - fg.a),
    b: fg.b * fg.a + bg.b * (1 - fg.a),
    a: 1,
  });
  const WHITE = { r: 255, g: 255, b: 255, a: 1 };

  // Every colour a gradient names. Chromium normalises background-image to
  // `linear-gradient(115deg, rgb(24, 35, 92) 0%, ...)`.
  const gradientStops = (img) => {
    if (!img || img === 'none' || !/gradient/i.test(img)) return [];
    const stops = [];
    const re = /rgba?\([^)]*\)/gi;
    let m;
    while ((m = re.exec(img))) { const c = parseColor(m[0]); if (c) stops.push(c); }
    return stops;
  };
  const hasPhoto = (img) => !!img && img !== 'none' && /url\(/i.test(img);

  const describe = (el) => {
    const cls = (el.getAttribute && el.getAttribute('class')) || '';
    return el.tagName.toLowerCase() + (cls ? '.' + String(cls).trim().split(/\s+/).join('.') : '');
  };

  // WHAT IS ACTUALLY PAINTED UNDER THIS TEXT, BY GEOMETRY RATHER THAN BY
  // ANCESTRY. The first version climbed parentElement, which is what a mail
  // client does and what these documents do not: the property covers paint
  // their background with absolutely-positioned SIBLINGS (`.cover-photo`,
  // `.cover-overlay`, inset:0) that are nowhere in the text's ancestor chain.
  // Against them the ancestor walk reported white-on-white at 1.00:1 for every
  // cover in the corpus — 66 runs of pure false positive, and they were the
  // loudest thing in the first report.
  //
  // elementsFromPoint returns the hit-test stack topmost-first, which is paint
  // order. Everything after the text's own element is painted beneath it.
  const backdropsFor = (el, rect) => {
    const x = Math.min(Math.max(rect.left + rect.width / 2, 0), innerWidth - 1);
    const y = Math.min(Math.max(rect.top + rect.height / 2, 0), innerHeight - 1);
    const chain = document.elementsFromPoint(x, y);
    const idx = chain.indexOf(el);
    // slice(idx), NOT slice(idx + 1): an element's own background is painted
    // behind its own text. Excluding it reported white-on-white for every
    // coloured table header in the corpus.
    const hit = idx >= 0 ? chain.slice(idx) : chain;
    const isCovered = idx > 0;   // something paints on top of this text

    // elementsFromPoint SKIPS thead, tbody and tr — measured, not assumed:
    // hit-testing a <th> inside `thead { background: navy }` returns
    // th, table, body, html and no thead at all. Those sections paint, so the
    // chain is expanded with the ancestors that sit between consecutive hits.
    // Without this, every table header in the corpus reads white-on-white.
    const beneath = [];
    for (let i = 0; i < hit.length; i++) {
      beneath.push(hit[i]);
      const next = hit[i + 1];
      if (!next) continue;
      for (let a = hit[i].parentElement; a && a !== next; a = a.parentElement) {
        if (!next.contains(a)) break;
        beneath.push(a);
      }
    }

    const acc = [];              // translucent layers, nearest first
    for (const e of beneath) {
      const cs = getComputedStyle(e);
      if (hasPhoto(cs.backgroundImage)) {
        // A photo. What the reader sees is not a CSS colour, so this is
        // declined rather than guessed — the same rule the email walker
        // applies to a `color:` it cannot parse.
        return { photo: true, source: describe(e) + ' image', covered: isCovered };
      }
      const stops = gradientStops(cs.backgroundImage);
      if (stops.length) {
        return {
          layers: stops.map(sp => acc.reduce((c, l) => over(l, c), sp)),
          source: describe(e) + ' gradient', covered: isCovered,
        };
      }
      const bc = parseColor(cs.backgroundColor);
      if (bc && bc.a > 0) {
        if (bc.a >= 0.999) {
          return { layers: [acc.reduce((c, l) => over(l, c), bc)],
                   source: describe(e), covered: isCovered };
        }
        acc.push(bc);
      }
    }
    return { layers: [acc.reduce((c, l) => over(l, c), WHITE)],
             source: 'page default', covered: isCovered };
  };

  const nodes = [];
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  let n;
  while ((n = walker.nextNode())) {
    if ((n.nodeValue || '').trim()) nodes.push(n);
  }

  for (const node of nodes) {
    const text = node.nodeValue.replace(/\s+/g, ' ').trim();
    const el = node.parentElement;
    if (!el) continue;
    const tag = el.tagName.toLowerCase();
    if (tag === 'style' || tag === 'script' || tag === 'title') continue;

    const cs = getComputedStyle(el);
    if (cs.display === 'none' || cs.visibility === 'hidden' || parseFloat(cs.opacity) === 0) continue;

    // elementsFromPoint is viewport-relative, and these documents are up to
    // sixteen pages long. Scroll the run into view before hit-testing it.
    const range = document.createRange();
    range.selectNodeContents(node);
    let rect = range.getBoundingClientRect();
    if (rect.width === 0 || rect.height === 0) continue;
    if (rect.top < 0 || rect.bottom > innerHeight) {
      el.scrollIntoView({ block: 'center' });
      rect = range.getBoundingClientRect();
    }
    if (rect.width === 0 || rect.height === 0) continue;
    // Still off-screen after scrolling. Measured, these are all the font
    // warm-up spans — a single "." parked at -10000px, six per document —
    // which are never painted. Hit-testing them would clamp to a point
    // somewhere else on the page and measure the wrong background, so they
    // are counted and reported rather than silently measured or dropped.
    if (rect.bottom < 0 || rect.top > innerHeight) {
      offscreen++;
      offscreenWhat.push(describe(el) + ' h=' + Math.round(rect.height) +
                         ' top=' + Math.round(rect.top));
      continue;
    }

    const isSvg = el.namespaceURI === 'http://www.w3.org/2000/svg';
    const fg = parseColor(isSvg ? cs.fill : cs.color);
    if (!fg) { unresolved++; continue; }

    const backdrop = backdropsFor(el, rect);
    if (backdrop.photo) { unresolved++; continue; }
    if (backdrop.covered) covered++;

    const size = parseFloat(cs.fontSize) || 0;
    const w = cs.fontWeight;
    const weight = w === 'bold' ? 700 : (w === 'normal' ? 400 : (parseInt(w, 10) || 400));

    for (const bg of backdrop.layers) {
      const eff = fg.a >= 0.999 ? fg : over(fg, bg);
      out.push({
        fg: hex(eff), bg: hex(bg), tag, selector: describe(el),
        bg_source: backdrop.source, text: text.slice(0, 60),
        size, weight, svg: isSvg, covered: backdrop.covered,
      });
    }
  }
  return { runs: out, declined_photo: unresolved, covered, offscreen, offscreenWhat };
};

(async () => {
  const [dir, exe, outPath] = process.argv.slice(2);
  const browser = await chromium.launch(exe ? { executablePath: exe } : {});
  const page = await browser.newPage({ viewport: { width: 816, height: 2200 } });
  const result = {};
  for (const f of fs.readdirSync(dir).filter(f => f.endsWith('.html')).sort()) {
    await page.goto('file://' + path.join(dir, f), { waitUntil: 'load' });
    result[f.replace(/\.html$/, '')] = await page.evaluate(WALK);
  }
  await browser.close();
  fs.writeFileSync(outPath, JSON.stringify(result));
})();
"""


def find_chromium():
    """An explicit chromium path, or "" to let Playwright resolve its own.

    TWO LOCATIONS, because they are different machines. A Claude Code cloud
    container preinstalls browsers under PLAYWRIGHT_BROWSERS_PATH and pins a
    build that is not the one the `playwright` package wants, so an unaided
    launch there fails and the explicit path is required. A CI runner that has
    just run `playwright install` has them in ~/.cache/ms-playwright under the
    exact pinned name, where Playwright finds them itself.

    Returning "" is a valid answer, not a failure: the caller then launches
    without `executablePath`. Treating "" as "no browser" is what made the
    first CI run of the contrast gate fail on a runner that had one.
    """
    roots = [Path(os.environ["PLAYWRIGHT_BROWSERS_PATH"])] if os.environ.get(
        "PLAYWRIGHT_BROWSERS_PATH") else [Path("/opt/pw-browsers")]
    roots.append(Path.home() / ".cache/ms-playwright")
    for root in roots:
        for candidate in sorted(root.glob("chromium-*/chrome-linux/chrome"), reverse=True):
            return str(candidate)
    return ""


# ── the corpus ──────────────────────────────────────────────────────────────
def market_documents():
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "_measure", REPO / "scripts/measure_market_pagination.py")
    measure = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(measure)
    from worker.market_builder import ALL_REPORT_TYPES, MarketReportBuilder

    docs = {}
    for report_type in ALL_REPORT_TYPES:
        for brand, primary in BRANDS:
            data = measure.report_data(report_type, 12)
            data["branding"]["primary_color"] = primary
            data["price_bands"] = [
                {"label": "Under $900K", "count": 18, "pct": 40},
                {"label": "$900K – $1.1M", "count": 12, "pct": 27},
                {"label": "$1.1M+", "count": 15, "pct": 33},
            ]
            builder = MarketReportBuilder(data)
            docs[f"market__{report_type}__{brand}"] = builder.render_html()
            # The running head and footer are separate documents PDFShift
            # composes onto every page. They are the two places a brand colour
            # meets text most directly, and neither is part of the body render.
            if report_type == "market_snapshot":
                docs[f"market__runninghead__{brand}"] = builder.render_page_header_html()
                docs[f"market__footer__{brand}"] = builder.render_page_footer_html()
    return docs


def property_documents():
    from worker.property_builder import THEME_TEMPLATES, PropertyReportBuilder
    base = {
        "property_address": "1234 Oak Avenue", "property_city": "Irvine",
        "property_state": "CA", "property_zip": "92602",
        "owner_name": "Jane Homeowner", "apn": "123-456-789",
        "agent": {"name": "Jennifer Martinez", "title": "Luxury Home Specialist",
                  "phone": "(949) 555-0100", "email": "jen@example.com",
                  "company_name": "Coastal Realty"},
        "sitex_data": {"bedrooms": 4, "bathrooms": 3, "sqft": 2400,
                       "year_built": 1998, "lot_size": 7200,
                       "assessed_value": 980000},
        "comps": [
            {"address": f"{100 + i * 11} Elm St", "price": 900000 + i * 25000,
             "bedrooms": 3 + i % 2, "bathrooms": 2, "sqft": 2100 + i * 90,
             "days_on_market": 5 + i * 4, "status": "Closed",
             "close_date": "2026-08-15", "distance": 0.4 + i * 0.2}
            for i in range(6)
        ],
    }
    docs = {}
    for theme in sorted(THEME_TEMPLATES):
        for brand, primary in BRANDS:
            data = {**base, "theme": theme,
                    "branding": {"primary_color": primary,
                                 "company_name": "Coastal Realty"}}
            docs[f"property__{theme}__{brand}"] = PropertyReportBuilder(data).render_html()
    return docs


# ── the measurement ─────────────────────────────────────────────────────────
def measure(docs):
    work = Path(tempfile.mkdtemp(prefix="pdf-contrast-"))
    for name, html in docs.items():
        (work / f"{name}.html").write_text(html, encoding="utf-8")
    js = REPO / "_measure_pdf_contrast.js"
    js.write_text(JS)
    out = work / "findings.json"
    try:
        subprocess.run(["node", str(js), str(work), find_chromium(), str(out)],
                       cwd=str(REPO), check=True)
    finally:
        js.unlink(missing_ok=True)
    return json.loads(out.read_text()), work


def ratio(fg, bg):
    from worker.themes import contrast
    return contrast(fg, bg)


def required(size, weight):
    """WCAG 1.4.3: 3:1 for large text, 4.5:1 otherwise. 18.66px == 14pt."""
    large = size >= 24 or (size >= 18.66 and weight >= 700)
    return 3.0 if large else 4.5


def main():
    docs = {}
    docs.update(market_documents())
    docs.update(property_documents())
    print(f"rendering {len(docs)} documents "
          f"({len(BRANDS)} brands x 8 market types + head/foot, 5 property themes)\n")
    raw, work = measure(docs)

    rows, declined, covered, offscreen = [], 0, 0, 0
    offscreen_what = Counter()
    for doc, payload in raw.items():
        declined += payload["declined_photo"]
        covered += payload["covered"]
        offscreen += payload["offscreen"]
        offscreen_what.update(payload.get("offscreenWhat", []))
        for e in payload["runs"]:
            r = ratio(e["fg"], e["bg"])
            rows.append({**e, "doc": doc, "ratio": r,
                         "needs": required(e["size"], e["weight"])})

    surfaces = defaultdict(list)
    for r in rows:
        surfaces[r["doc"].split("__")[0]].append(r)

    print(f"{'surface':10s} {'runs':>7s} {'<4.5':>7s} {'< req':>7s} {'worst':>7s}  documents")
    print("-" * 74)
    for surface in sorted(surfaces):
        rs = surfaces[surface]
        fails = [r for r in rs if r["ratio"] < r["needs"]]
        strict = [r for r in rs if r["ratio"] < 4.5]
        worst = min((r["ratio"] for r in rs), default=0)
        ndocs = len({r["doc"] for r in rs})
        print(f"{surface:10s} {len(rs):7d} {len(strict):7d} {len(fails):7d} "
              f"{worst:7.2f}  {ndocs}")

    print(f"\n{declined} runs declined (text over a photo — the backdrop is not a "
          f"CSS colour) · {covered} have something painted over them · "
          f"{offscreen} sit off-canvas and are never painted")
    for what, n in offscreen_what.most_common(6):
        print(f"      {n:5d}  {what}")

    fails = sorted([r for r in rows if r["ratio"] < r["needs"]], key=lambda r: r["ratio"])
    print(f"\n{len(fails)} text runs below their WCAG threshold, "
          f"{len({(f['selector'], f['fg'], f['bg']) for f in fails})} distinct "
          f"(selector, colour, background) combinations\n")

    groups = defaultdict(list)
    for f in fails:
        groups[(f["selector"], f["fg"], f["bg"], round(f["ratio"], 2))].append(f)
    for (sel, fg, bg, r), items in sorted(groups.items(), key=lambda kv: kv[0][3]):
        brands = sorted({i["doc"].split("__")[-1] for i in items})
        docs_hit = sorted({i["doc"].rsplit("__", 1)[0] for i in items})
        sizes = sorted({(i["size"], i["weight"]) for i in items})
        print(f"{r:5.2f}:1  {fg} on {bg}  needs {items[0]['needs']}:1")
        print(f"         {sel}   ({items[0]['bg_source']})")
        print(f"         {len(items)} runs · {len(brands)} brand(s): {', '.join(brands)}")
        print(f"         in: {', '.join(docs_hit[:4])}{' …' if len(docs_hit) > 4 else ''}")
        print(f"         size/weight: {sizes[:3]}   e.g. {items[0]['text']!r}")
        print()

    if "--json" in sys.argv:
        dest = Path(sys.argv[sys.argv.index("--json") + 1])
        dest.write_text(json.dumps(rows, indent=1))
        print(f"raw findings -> {dest}")
    print(f"renders left in {work}")
    return rows


if __name__ == "__main__":
    main()
