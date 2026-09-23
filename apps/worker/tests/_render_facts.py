"""
Extract the FACTS a rendered email asserts, so a restructure can be proved to
change none of them.

WHY NOT DIFF THE HTML
---------------------
The consolidation replaces Python f-strings with one Jinja2 template. Every
design decision was already made — in the colour work and in D-099 — so the
restructure must change nothing a recipient sees. But it will change the bytes:
indentation, attribute order, where the newlines fall. A byte diff would be
enormous and would say nothing.

So the gate is a diff of **what the document means**, not how it is spelled:

    text          every visible text run, whitespace-normalised, in order
    colours       every text run's foreground and its RESOLVED background
    links         every href, in order
    images        every img src, in order
    css_vars      every custom property declaration and its value
    classes       the set of classes actually attached to elements
    structure     counts of the elements that carry layout

A restructure that leaves all seven identical has changed nothing that renders.
One that changes any of them has changed something, and the diff names it.

WHAT THIS DELIBERATELY DOES NOT CATCH
-------------------------------------
Geometry. Two documents can agree on every fact here and lay out differently —
a `width="50%"` that became `width="33%"`, a padding change, a cell that moved
to a different row. `structure` catches gross shape changes (a table gained a
row) and nothing finer. Stated because "the facts are identical" is a weaker
claim than "the render is identical", and the difference is exactly where a
restructure bug would hide.
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from typing import Dict, List

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _contrast_audit import ContrastWalker  # noqa: E402

WS = re.compile(r"\s+")
DECL = re.compile(r"(--[a-zA-Z0-9-]+)\s*:\s*([^;]+)")

#: Elements whose presence and count describe the document's shape.
STRUCTURAL = ("table", "tr", "td", "th", "img", "a", "p", "span", "div", "center")


class FactWalker(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links: List[str] = []
        self.images: List[str] = []
        self.classes: Counter = Counter()
        self.tags: Counter = Counter()
        self._skip = 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        self.tags[tag] += 1
        if tag == "a" and "href" in a:
            self.links.append(a["href"])
        if tag == "img" and "src" in a:
            self.images.append(a["src"])
        for c in (a.get("class") or "").split():
            self.classes[c] += 1


def _text_and_colours(html: str):
    w = ContrastWalker()
    w.feed(html)
    text, colours = [], []
    for f in w.pairs:
        t = WS.sub(" ", f.text).strip()
        if not t:
            continue
        text.append(t)
        colours.append(f"{t[:40]}|{f.fg}|{f.bg}")
    # de-duplicate the gradient fan-out: a run on a two-stop background is
    # reported once per stop, which is right for contrast and noise here.
    seen, ordered = set(), []
    for t in text:
        ordered.append(t)
    return ordered, sorted(set(colours))


def facts(html: str) -> Dict:
    fw = FactWalker()
    fw.feed(html)
    text, colours = _text_and_colours(html)
    css_vars = sorted({f"{k}:{WS.sub(' ', v).strip()}" for k, v in DECL.findall(html)})
    return {
        "text": text,
        "colours": colours,
        "links": fw.links,
        "images": fw.images,
        "css_vars": css_vars,
        "classes": dict(sorted(fw.classes.items())),
        "structure": {t: fw.tags.get(t, 0) for t in STRUCTURAL},
    }


def diff(before: Dict, after: Dict) -> Dict[str, str]:
    """{key: human-readable description} for each fact set that differs."""
    out = {}
    for key in before:
        b, a = before[key], after[key]
        if b == a:
            continue
        if isinstance(b, list):
            bs, as_ = Counter(b), Counter(a)
            gone = sorted((bs - as_).elements())
            new = sorted((as_ - bs).elements())
            if not gone and not new:
                out[key] = f"same {len(b)} items, different ORDER"
            else:
                out[key] = f"-{len(gone)} +{len(new)}  gone={gone[:4]} new={new[:4]}"
        elif isinstance(b, dict):
            keys = sorted(set(b) | set(a))
            changed = [f"{k}: {b.get(k)}->{a.get(k)}" for k in keys if b.get(k) != a.get(k)]
            out[key] = "; ".join(changed[:6])
        else:
            out[key] = f"{b!r} -> {a!r}"
    return out


def save(path: Path, data: Dict) -> None:
    path.write_text(json.dumps(data, indent=1, sort_keys=True) + "\n")


def load(path: Path) -> Dict:
    return json.loads(path.read_text())
