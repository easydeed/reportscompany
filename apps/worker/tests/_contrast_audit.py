"""
Walk rendered email HTML and measure every text colour against the background it
actually sits on.

WHY A WALKER AND NOT THIRTY ASSERTIONS
--------------------------------------
The email template puts a brand colour into roughly thirty `style="…"` strings,
some as text on a white card, some as a fill with hardcoded white text on it.
Asserting each one individually gives thirty tests that pass while the thirty-
first site, added next month, fails silently. Asserting the *property* — no text
in this document is unreadable against its own background — covers all of them
and the ones not written yet.

HOW THE BACKGROUND IS RESOLVED
------------------------------
Inline styles only, which is all an email has: `background` / `background-color`
on an element or any ancestor, nearest ancestor winning, with the document
default as the floor. That is exactly how a mail client resolves it, because
email CSS has no cascade worth speaking of and every rule here is inline.

WHAT IT DELIBERATELY DOES NOT DO
--------------------------------
- **Gradients are reduced to their stops** and each stop is measured separately.
  A `linear-gradient(a, b)` panel is reported against both a and b, because text
  on it must be readable at either end. This is stricter than a mail client that
  ignores the gradient and uses the fallback colour, and the strictness is the
  point: the market header band's 9.90:1-at-one-end / 2.53:1-at-the-other is a
  real defect (D-097) that a single-colour check cannot see.
- **rgba text is flattened over the background the walker already resolved**,
  which is correct rather than a guess: the backdrop is known by the time the
  text is measured. `rgba(255,255,255,0.7)` on a brand panel is a real colour a
  recipient sees, and it is a very common way this template writes a muted
  label on a coloured band.

  An rgba **background** is still skipped — there the backdrop is the *parent*,
  and resolving it would need a second pass. Stated so the gap is known.

- **A `color:` the walker cannot parse suppresses the element's text rather
  than inheriting.** The first version inherited, so an unparseable rgba fell
  back to the document's black and reported `#000000 on #dc2626` at 4.35:1 —
  text that is actually white-at-70% and perfectly legible. Two false positives
  per render, and they were the first thing the audit surfaced. Inheriting a
  value the author explicitly overrode is not a conservative default, it is a
  wrong one.
- **Nothing about size.** WCAG allows 3:1 for large text. Every threshold here
  is 4.5:1, so a finding may be a false positive for a genuinely large heading —
  which is a judgement for the reader of the report, not for the walker.
"""
from __future__ import annotations

import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from typing import Dict, List, NamedTuple, Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from worker.themes import contrast, normalize_hex  # noqa: E402

HEX = re.compile(r"#[0-9a-fA-F]{6}\b|#[0-9a-fA-F]{3}\b")
DECL = re.compile(r"([a-zA-Z-]+)\s*:\s*([^;]+)")
RGBA = re.compile(
    r"rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*(?:,\s*([\d.]+)\s*)?\)", re.I
)

#: Sentinel for "this element declares a colour we cannot resolve". Its text is
#: not measured, rather than measured against an inherited value the author
#: overrode.
UNRESOLVED = "?unresolved"


def flatten(rgba_text: str, backdrop: str) -> Optional[str]:
    """`rgba(255,255,255,0.7)` over `#dc2626` -> the hex a recipient sees."""
    m = RGBA.search(rgba_text or "")
    if not m:
        return None
    r, g, b = (int(m.group(i)) for i in (1, 2, 3))
    a = float(m.group(4)) if m.group(4) is not None else 1.0
    a = max(0.0, min(1.0, a))
    try:
        back = normalize_hex(backdrop)[1:]
    except ValueError:
        return None
    br, bg_, bb = (int(back[i:i + 2], 16) for i in (0, 2, 4))
    mix = lambda c, d: int(round(c * a + d * (1 - a)))  # noqa: E731
    return "#{:02x}{:02x}{:02x}".format(mix(r, br), mix(g, bg_), mix(b, bb))

#: The outermost surface of these emails. Used when no ancestor declares one.
DOCUMENT_BG = "#ffffff"

#: Elements whose text we do not judge: MSO-only VML is measured through its own
#: attributes, and a <style> block's contents are not rendered text.
SKIP_TEXT_IN = {"style", "script", "head", "title"}


class Finding(NamedTuple):
    ratio: float
    fg: str
    bg: str
    tag: str
    text: str
    bg_source: str

    def __str__(self) -> str:
        return (f"{self.ratio:5.2f}:1  {self.fg} on {self.bg}  <{self.tag}> "
                f"({self.bg_source})  {self.text[:48]!r}")


def _declarations(style: str) -> Dict[str, str]:
    return {m.group(1).strip().lower(): m.group(2).strip()
            for m in DECL.finditer(style or "")}


def _colours_in(value: str) -> List[str]:
    """
    Every concrete colour a declaration names. A gradient yields all its stops;
    rgba() yields nothing, because flattening it needs a backdrop this function
    does not have.
    """
    out = []
    for h in HEX.findall(value or ""):
        try:
            out.append(normalize_hex(h))
        except ValueError:
            pass
    return out


class ContrastWalker(HTMLParser):
    def __init__(self, document_bg: str = DOCUMENT_BG):
        super().__init__(convert_charrefs=True)
        # (tag, background colours, source description, text colour)
        self._stack: List[tuple] = []
        self._bg_stack: List[tuple] = [(document_bg, "document default")]
        self._fg_stack: List[str] = ["#000000"]
        self._skip_depth = 0
        self.pairs: List[Finding] = []
        #: Text runs the walker declined to judge. Reported so "no findings" can
        #: be distinguished from "nothing was looked at" — a count of zero pairs
        #: and a large unresolved count is a broken walker, not a clean document.
        self.unresolved = 0

    # -- background/foreground inheritance ---------------------------------
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        decls = _declarations(a.get("style", ""))
        bgs = []
        for prop in ("background-color", "background"):
            if prop in decls:
                bgs = _colours_in(decls[prop])
                if bgs:
                    break
        # VML fill and the legacy bgcolor attribute are backgrounds too
        if not bgs and a.get("fillcolor"):
            bgs = _colours_in(a["fillcolor"])
        if not bgs and a.get("bgcolor"):
            bgs = _colours_in(a["bgcolor"])

        pushed_bg = False
        if bgs:
            self._bg_stack.append((bgs, f"<{tag}>"))
            pushed_bg = True

        fg = None
        if "color" in decls:
            c = _colours_in(decls["color"])
            if c:
                fg = c[0]
            elif RGBA.search(decls["color"]):
                # Resolved at measurement time against whatever background is
                # then in force; kept as the raw declaration until then.
                fg = decls["color"]
            else:
                fg = UNRESOLVED
        pushed_fg = False
        if fg:
            self._fg_stack.append(fg)
            pushed_fg = True

        if tag in SKIP_TEXT_IN:
            self._skip_depth += 1

        self._stack.append((tag, pushed_bg, pushed_fg, tag in SKIP_TEXT_IN))

    def handle_startendtag(self, tag, attrs):
        pass  # void elements carry no text

    def handle_endtag(self, tag):
        # tolerate unbalanced markup (mail HTML is full of it)
        for i in range(len(self._stack) - 1, -1, -1):
            if self._stack[i][0] == tag:
                for t, pbg, pfg, skip in reversed(self._stack[i:]):
                    if pbg:
                        self._bg_stack.pop()
                    if pfg:
                        self._fg_stack.pop()
                    if skip:
                        self._skip_depth -= 1
                del self._stack[i:]
                return

    # -- the measurement ---------------------------------------------------
    def handle_data(self, data):
        if self._skip_depth:
            return
        text = data.strip()
        if not text:
            return
        fg = self._fg_stack[-1]
        if fg == UNRESOLVED:
            self.unresolved += 1
            return
        bgs, src = self._bg_stack[-1]
        if isinstance(bgs, str):
            bgs = [bgs]
        tag = self._stack[-1][0] if self._stack else "?"
        for bg in bgs:
            effective = fg
            if not fg.startswith("#"):
                effective = flatten(fg, bg)
                if effective is None:
                    self.unresolved += 1
                    continue
            self.pairs.append(
                Finding(contrast(effective, bg), effective, bg, tag, text, src)
            )


def audit(html: str, threshold: float = 4.5) -> List[Finding]:
    """Every (text, background) pair below `threshold`, worst first."""
    w = ContrastWalker()
    w.feed(html)
    bad = [p for p in w.pairs if p.ratio < threshold]
    return sorted(bad, key=lambda f: f.ratio)


def all_pairs(html: str) -> List[Finding]:
    w = ContrastWalker()
    w.feed(html)
    return w.pairs


def coverage(html: str) -> tuple:
    """(pairs measured, text runs declined). The second number is the blind spot."""
    w = ContrastWalker()
    w.feed(html)
    return len(w.pairs), w.unresolved
