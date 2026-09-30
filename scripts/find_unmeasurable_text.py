#!/usr/bin/env python3
"""Text the pixel contrast measurer cannot measure, by construction. (D-154)

    python3 scripts/find_unmeasurable_text.py

WHY THIS EXISTS. `measure_contrast_by_pixel.py` reads the backdrop by
rendering the page a second time with every glyph blanked:

    * { color: transparent; -webkit-text-fill-color: transparent }

That is sound for text painted by `color`. It is not sound for text painted
by a **gradient clipped to the glyphs** — `background-clip: text` with
`-webkit-text-fill-color: transparent` — because such an element:

  * has no meaningful `color`, so the measurer's FOREGROUND is whatever
    `color` happens to be set to and is not what the reader sees; and
  * is already transparent-filled, so blanking it changes nothing and the
    BACKDROP sample returns the element's own gradient rather than what sits
    behind it.

Both halves of the measurement are wrong, and neither is wrong loudly. The
script's own header names the `currentColor` case as its caveat; this is its
sibling and is not named there.

THE WALKER HAD THE SAME BLIND SPOT FOR A DIFFERENT REASON — it resolved a
declared `color` too — so switching instruments (D-130) did not fix it and
could not have.

WHAT THIS COUNTS. Every element in the gate's own sixty-document corpus
whose computed style says the glyphs are not painted by `color`. Run it
after any template change that adds gradient text: one known blind spot is a
footnote on the 215, several would be an asterisk on it.
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "apps/worker/src"))

import measure_contrast_by_pixel as pixel  # noqa: E402

JS = r"""
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
const [dir, exePath, outJson] = process.argv.slice(2);

const FIND = () => {
  const out = [];
  for (const el of document.querySelectorAll('*')) {
    const cs = getComputedStyle(el);
    const fill = cs.webkitTextFillColor || '';
    const clip = (cs.backgroundClip || '') + ' ' + (cs.webkitBackgroundClip || '');
    const transparentFill = /transparent|rgba\(0,\s*0,\s*0,\s*0\)/.test(fill);
    const clipsToText = /text/.test(clip);
    if (!transparentFill && !clipsToText) continue;
    const text = (el.textContent || '').trim();
    if (!text) continue;
    const r = el.getBoundingClientRect();
    if (r.width < 1 || r.height < 1) continue;
    out.push({
      selector: el.tagName.toLowerCase() +
        (el.className && typeof el.className === 'string'
          ? '.' + el.className.trim().split(/\s+/).join('.') : ''),
      text: text.slice(0, 40),
      color: cs.color,
      fill: fill,
      clip: clip.trim(),
      background: cs.backgroundImage !== 'none' ? 'image/gradient' : cs.backgroundColor,
    });
  }
  return out;
};

(async () => {
  const b = await chromium.launch(exePath ? { executablePath: exePath } : {});
  const all = {};
  for (const f of fs.readdirSync(dir).filter(f => f.endsWith('.html'))) {
    const p = await b.newPage({ viewport: { width: 816, height: 1056 } });
    await p.goto('file://' + path.join(dir, f), { waitUntil: 'networkidle' });
    all[f.replace(/\.html$/, '')] = await p.evaluate(FIND);
    await p.close();
  }
  await b.close();
  fs.writeFileSync(outJson, JSON.stringify(all));
})();
"""


def main():
    spec_path = REPO / "scripts/measure_pdf_contrast.py"
    import importlib.util
    spec = importlib.util.spec_from_file_location("_corpus", spec_path)
    corpus = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(corpus)

    docs = {}
    docs.update(corpus.market_documents())
    docs.update(corpus.property_documents())

    work = Path(tempfile.mkdtemp(prefix="unmeasurable-"))
    for name, html in docs.items():
        (work / f"{name}.html").write_text(html, encoding="utf-8")
    js = REPO / "_find_unmeasurable_text.js"
    js.write_text(JS)
    out = work / "found.json"
    try:
        subprocess.run(["node", str(js), str(work), pixel.find_chromium(), str(out)],
                       cwd=str(REPO), check=True)
    finally:
        js.unlink(missing_ok=True)

    found = json.loads(out.read_text())
    total = sum(len(v) for v in found.values())
    docs_hit = {k: v for k, v in found.items() if v}

    print(f"{len(docs)} documents measured, {total} element(s) whose glyphs are NOT "
          f"painted by `color`\n")
    if not total:
        print("  None. The measurer's blanking technique collides with nothing in")
        print("  this corpus, and the 215 has no asterisk from this cause.")
        return 0

    seen = {}
    for doc, items in sorted(docs_hit.items()):
        for it in items:
            seen.setdefault((it["selector"], it["text"]), []).append(doc)
    print(f"{len(seen)} distinct (selector, text) across {len(docs_hit)} documents:\n")
    for (sel, text), where in sorted(seen.items()):
        fams = sorted({d.rsplit('__', 1)[0] for d in where})
        print(f"  {sel[:34]:34s} {text[:22]:22s} in {len(where):2d} docs  {fams}")
    print()
    print("  Each of these is measured with a foreground that is not what the")
    print("  reader sees and a backdrop that may be the element's own paint.")
    print("  Neither the pixel measurer nor the DOM walker can read them: both")
    print("  resolve a declared `color`.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
