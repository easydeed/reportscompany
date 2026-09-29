"""Contrast by reading the rendered pixel, with no hit-testing at all.

WHY THIS EXISTS ALONGSIDE measure_pdf_contrast.py
-------------------------------------------------
That script resolves "what is painted behind this text" from the
`elementsFromPoint` stack, expanded with the DOM ancestors sitting between
consecutive hits. The expansion was added because `elementsFromPoint` skips
`thead`, `tbody` and `tr`. Measured over the property surface, the method
produces 22 false positives in 1,965 runs and **zero** misses, by two
mechanisms (D-130):

  1. the ancestor expansion attributes an absolutely-positioned child to a
     parent whose painted box it has escaped — teal's `.bar .val` sits at
     `top:-24px`, above its bar, and is read as navy-on-navy at 1.00:1;
  2. `pointer-events:none` hides an element from hit-testing entirely, so
     `idx === -1` and its own background is never considered — bold's
     `.mt-gauge-marker` makes its navy pill read as white-on-white.

Each is the same family of error the resolver has now made four times, and
mechanism 1 was introduced by the fix for the `thead`/`tbody`/`tr` skip.

WHAT THIS DOES INSTEAD
----------------------
It renders each document twice. Once normally, to collect every text run's
rect, colour, size and weight. Then it makes every glyph transparent, takes a
full-page screenshot, and reads the pixel at each rect. That pixel IS the
backdrop, whatever painted it — no chain, no ancestors, no assumption about
paint order, and nothing to be wrong about.

Five points are sampled across each run. When they disagree the run straddles
two backdrops; the modal colour is used and the disagreement is counted and
reported rather than averaged away.

CAVEAT, STATED RATHER THAN HIDDEN
---------------------------------
Blanking text also blanks any paint deriving from `currentColor`. Nothing in
these templates uses `currentColor` for a background today, checked by grep; a
future template could, and this method would then under-report it.

Text over a photograph is measured against whatever the photo paints at that
pixel, which is what the reader sees and is strictly better than the DOM
walker's "declined" — but a JPEG's local colour is not a design token, so a
finding there means "this instance", not "this rule".

    python3 scripts/measure_contrast_by_pixel.py HTML_DIR [--json OUT]
"""
import json
import os
import subprocess
import sys
import tempfile
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "apps/worker/src"))

JS = r"""
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
const { PNG } = require('pngjs');

const COLLECT = () => {
  const out = [];
  const walk = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  let n;
  while ((n = walk.nextNode())) {
    const t = n.textContent.trim();
    if (!t) continue;
    const el = n.parentElement;
    if (!el) continue;
    const cs = getComputedStyle(el);
    if (cs.visibility === 'hidden' || cs.display === 'none' || parseFloat(cs.opacity) === 0) continue;
    const range = document.createRange();
    range.selectNodeContents(n);
    const r = range.getBoundingClientRect();
    if (r.width < 1 || r.height < 1) continue;
    const sel = el.tagName.toLowerCase() +
      (el.className && typeof el.className === 'string'
        ? '.' + el.className.trim().split(/\s+/).join('.') : '');
    out.push({
      selector: sel, text: t.slice(0, 60),
      fg: (cs.webkitTextFillColor && cs.webkitTextFillColor !== 'rgba(0, 0, 0, 0)')
          ? cs.webkitTextFillColor : cs.color,
      size: parseFloat(cs.fontSize), weight: parseInt(cs.fontWeight, 10) || 400,
      x: r.left + window.scrollX, y: r.top + window.scrollY, w: r.width, h: r.height,
    });
  }
  return out;
};

(async () => {
  const [dir, exePath, outJson] = process.argv.slice(2);
  const b = await chromium.launch(exePath ? { executablePath: exePath } : {});
  const all = [];
  for (const f of fs.readdirSync(dir).filter(f => f.endsWith('.html'))) {
    const p = await b.newPage({ viewport: { width: 816, height: 1056 } });
    await p.goto('file://' + path.join(dir, f), { waitUntil: 'networkidle' }).catch(()=>{});
    const runs = await p.evaluate(COLLECT);
    await p.addStyleTag({ content:
      `*,*::before,*::after{color:transparent!important;` +
      `-webkit-text-fill-color:transparent!important;text-shadow:none!important;}` });
    const png = PNG.sync.read(await p.screenshot({ fullPage: true }));
    const at = (x, y) => {
      x = Math.round(x); y = Math.round(y);
      if (x < 0 || y < 0 || x >= png.width || y >= png.height) return null;
      const i = (png.width * y + x) << 2;
      return [png.data[i], png.data[i+1], png.data[i+2]];
    };
    for (const r of runs) {
      const pts = [0.1, 0.3, 0.5, 0.7, 0.9]
        .map(k => at(r.x + r.w * k, r.y + r.h / 2)).filter(Boolean);
      if (!pts.length) continue;
      const counts = {};
      for (const c of pts) counts[c.join(',')] = (counts[c.join(',')] || 0) + 1;
      const [best, n] = Object.entries(counts).sort((a, b2) => b2[1] - a[1])[0];
      all.push({ ...r, doc: f.replace(/\.html$/, ''),
                 bgPixel: best.split(',').map(Number), agree: n, samples: pts.length });
    }
    await p.close();
  }
  await b.close();
  fs.writeFileSync(outJson, JSON.stringify(all));
})();
"""


def find_chromium():
    """Same two-location resolution as measure_pdf_contrast.py; "" is valid."""
    roots = [Path(os.environ["PLAYWRIGHT_BROWSERS_PATH"])] if os.environ.get(
        "PLAYWRIGHT_BROWSERS_PATH") else [Path("/opt/pw-browsers")]
    roots.append(Path.home() / ".cache/ms-playwright")
    for root in roots:
        for candidate in sorted(root.glob("chromium-*/chrome-linux/chrome"), reverse=True):
            return str(candidate)
    return ""


def _hex(rgb):
    return "#%02x%02x%02x" % tuple(rgb)


def _parse_css_color(s):
    """-> (hex, alpha). Accepts `#rgb`, `#rrggbb`, `rgb(...)`, `rgba(...)`."""
    s = s.strip()
    if s.startswith("#"):
        h = s[1:]
        if len(h) == 3:
            h = "".join(c * 2 for c in h)
        return "#" + h, 1.0
    nums = [float(x) for x in s[s.index("(") + 1:s.index(")")].replace("/", ",").split(",")]
    r, g, b = nums[:3]
    a = nums[3] if len(nums) > 3 else 1.0
    return "#%02x%02x%02x" % (round(r), round(g), round(b)), a


def required(size, weight):
    """WCAG 1.4.3: 3:1 for large text, 4.5:1 otherwise. 18.66px == 14pt."""
    return 3.0 if (size >= 24 or (size >= 18.66 and weight >= 700)) else 4.5


def measure(html_dir: Path):
    work = Path(tempfile.mkdtemp(prefix="pixel-contrast-"))
    js = REPO / "_measure_contrast_by_pixel.js"
    js.write_text(JS)
    out = work / "runs.json"
    try:
        subprocess.run(["node", str(js), str(html_dir), find_chromium(), str(out)],
                       cwd=str(REPO), check=True)
    finally:
        js.unlink(missing_ok=True)
    return json.loads(out.read_text())


def score(rows):
    from worker.themes import contrast
    out = []
    for r in rows:
        fg, alpha = _parse_css_color(r["fg"])
        bg_rgb = r["bgPixel"]
        if alpha < 0.999:
            # A translucent text colour is flattened over the pixel it sits on,
            # which is the one thing pixel sampling cannot see through.
            fr, fg_, fb = (int(fg[i:i + 2], 16) for i in (1, 3, 5))
            fg = "#%02x%02x%02x" % tuple(
                round(f * alpha + b * (1 - alpha)) for f, b in zip((fr, fg_, fb), bg_rgb))
        bg = _hex(bg_rgb)
        out.append({**r, "fg_hex": fg, "bg_hex": bg,
                    "ratio": contrast(fg, bg),
                    "needs": required(r["size"], r["weight"])})
    return out


def main():
    html_dir = Path(sys.argv[1])
    rows = score(measure(html_dir))
    fails = sorted([r for r in rows if r["ratio"] < r["needs"]], key=lambda r: r["ratio"])
    straddle = sum(1 for r in rows if r["agree"] < r["samples"])

    print(f"{len(rows)} text runs in {len({r['doc'] for r in rows})} documents")
    print(f"{sum(1 for r in rows if r['ratio'] < 4.5)} below 4.5:1 · "
          f"{len(fails)} below their WCAG threshold · "
          f"worst {min((r['ratio'] for r in rows), default=0):.2f}:1")
    print(f"{straddle} runs straddle two backdrops across their own width "
          f"(modal pixel used)\n")

    for axis, part in (("document", lambda d: d),):
        by = defaultdict(lambda: [0, 0])
        for r in rows:
            k = part(r["doc"])
            by[k][0] += 1
            if r["ratio"] < r["needs"]:
                by[k][1] += 1
        print(f"{axis:28s} {'runs':>7s} {'fail':>7s}")
        print("-" * 46)
        for k in sorted(by):
            print(f"{k:28s} {by[k][0]:7d} {by[k][1]:7d}")

    groups = defaultdict(list)
    for f in fails:
        groups[(f["selector"], f["fg_hex"], f["bg_hex"], round(f["ratio"], 2))].append(f)
    print(f"\n{len(fails)} failing runs in {len(groups)} distinct "
          f"(selector, colour, background) combinations\n")
    for (sel, fg, bg, r), items in sorted(groups.items(), key=lambda kv: kv[0][3]):
        docs = sorted({i["doc"] for i in items})
        print(f"{r:5.2f}:1  {fg} on {bg}  needs {items[0]['needs']}:1  ({len(items)} runs)")
        print(f"         {sel}")
        print(f"         {', '.join(docs[:5])}{' …' if len(docs) > 5 else ''}")
        print(f"         e.g. {items[0]['text']!r}\n")

    if "--json" in sys.argv:
        dest = Path(sys.argv[sys.argv.index("--json") + 1])
        dest.write_text(json.dumps(rows, indent=1))
        print(f"raw findings -> {dest}")
    return rows


if __name__ == "__main__":
    main()
