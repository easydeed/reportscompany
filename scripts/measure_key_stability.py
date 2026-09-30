#!/usr/bin/env python3
"""How far does a contrast baseline key move when only the layout moves? (D-153)

    python3 scripts/measure_key_stability.py            # both measurements
    python3 scripts/measure_key_stability.py --spreads  # just the corpus spreads
    python3 scripts/measure_key_stability.py --nudge    # just the layout nudge

WHY THIS IS A SCRIPT. D-153 recommends comparing baseline entries with a
TOLERANCE rather than by exact equality, and recommends 48. That number is
only defensible while the two populations it sits between stay separated, and
both populations are properties of the templates — a redesign moves them. This
re-derives it, so the next person checks rather than inherits.

WHAT IT MEASURES

  --spreads   Every run in the ten production renders, grouped by
              (document, selector, page). Inside a group the only thing that
              varies is WHERE THE TEXT SITS, so the spread of sampled
              backdrops is the noise a position-keyed baseline picks up.
              Measured 2026-10-01: 21 groups at 1–37 and 7 at 131–614, with
              nothing in between. 48 sits in that gap.

  --nudge     The trigger itself, rather than the noise. Renders elegant
              twice — the second with the cover text pushed 60px across and
              40px down and NO colour changed — and reports which runs
              sampled a different backdrop. Measured: 2 of 11 cover runs
              moved, by distance 3. Small, and the point is that an exact-hex
              key treats 3 the same as 300.

The distance is the sum of absolute per-channel differences, which is what the
recommendation is written in. It is not perceptual and does not need to be:
the question is "is this the same backdrop or a different one", not "how
different does it look".
"""
import argparse
import collections
import json
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

import measure_contrast_by_pixel as pixel  # noqa: E402

#: The recommendation on D-153. Re-derive it, do not trust it.
RECOMMENDED_TOLERANCE = 48


def _rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def distance(a, b):
    return sum(abs(x - y) for x, y in zip(_rgb(a), _rgb(b)))


def _spread(hexes):
    return max((distance(a, b) for a in hexes for b in hexes), default=0)


def _render_production(out: Path, variant="bare"):
    subprocess.run([sys.executable, str(REPO / "scripts/render_property_production.py"),
                    str(out), variant], check=True, capture_output=True)


def spreads():
    """The noise floor: same rule, same page, different position."""
    out = Path(tempfile.mkdtemp(prefix="keystab-renders-"))
    _render_production(out)
    rows = pixel.score(pixel.measure(out))

    #: Pages are ~1096px tall in these renders; 1000 separates them cleanly
    #: and no page has two of anything this close to a boundary.
    groups = collections.defaultdict(set)
    for r in rows:
        groups[(r["doc"], r["selector"], int(r["y"]) // 1000)].add(r["bg_hex"])
    multi = {k: v for k, v in groups.items() if len(v) > 1}

    print(f"{len(rows)} runs; {len(multi)} (document, selector, page) groups whose "
          f"runs sit on more than one backdrop\n")
    ranked = sorted(multi.items(), key=lambda kv: _spread(kv[1]))
    for (doc, sel, pg), v in ranked:
        print(f"  {_spread(v):4d}  {doc.split('__')[1]:8s} p{pg} {sel[:30]:30s} {sorted(v)}")

    vals = sorted(_spread(v) for v in multi.values())
    below = [v for v in vals if v <= RECOMMENDED_TOLERANCE]
    above = [v for v in vals if v > RECOMMENDED_TOLERANCE]
    print(f"\n  at or below {RECOMMENDED_TOLERANCE}: {len(below)} groups, up to {max(below, default=0)}")
    print(f"  above       {RECOMMENDED_TOLERANCE}: {len(above)} groups, from {min(above, default=0)}")
    gap = min(above, default=0) - max(below, default=0)
    print(f"  GAP: {gap}. The recommendation holds while this is comfortably positive;")
    print( "  if a redesign closes it, the tolerance needs re-deriving rather than nudging.")
    return 0


def nudge():
    """The trigger: move the text, change nothing else, see if the key moves."""
    src_dir = Path(tempfile.mkdtemp(prefix="keystab-src-"))
    _render_production(src_dir)
    src = (src_dir / "property__elegant__bare.html").read_text(encoding="utf-8")

    work = Path(tempfile.mkdtemp(prefix="keystab-nudge-"))
    (work / "elegant__base.html").write_text(src, encoding="utf-8")
    # A layout change of the kind any redesign makes. No colour is touched.
    shifted = src.replace(
        "</head>",
        "<style>.cover{padding-top:40px !important;}"
        ".cover-city,.cover-street,h1.cover-title,.cover-agent-name,"
        ".cover-agent-title,.cover-brand-text{margin-left:60px !important;}"
        "</style></head>", 1)
    if shifted == src:
        sys.exit("could not inject the nudge — the template's <head> changed shape")
    (work / "elegant__nudged.html").write_text(shifted, encoding="utf-8")

    rows = pixel.score(pixel.measure(work))

    def cover(doc):
        return {(r["selector"], r["text"][:18]): (r["fg_hex"], r["bg_hex"], r["ratio"])
                for r in rows if r["doc"] == doc and r["y"] < 1100}

    a, b = cover("elegant__base"), cover("elegant__nudged")
    shared = sorted(set(a) & set(b))
    moved = [(k, a[k], b[k]) for k in shared if a[k][1] != b[k][1]]

    print(f"{len(shared)} cover runs present in both renders")
    print(f"{len(moved)} sampled a DIFFERENT BACKDROP after a move that changed no colour\n")
    for k, x, y in moved:
        print(f"  {k[0][:26]:26s} {k[1][:18]:18s} {x[1]} -> {y[1]}  "
              f"distance {distance(x[1], y[1]):3d}   ratio {x[2]:.2f} -> {y[2]:.2f}")
    if moved:
        ds = [distance(x[1], y[1]) for _, x, y in moved]
        print(f"\n  distances: min {min(ds)}, max {max(ds)}")
        print(f"  An exact-hex key treats {min(ds)} the same as 300: a new key, "
              f"reported as a new pairing.")
    else:
        print("  No run moved. Either the nudge missed, or this template no longer "
              "has a gradient behind its cover text — check before concluding the "
              "defect is gone.")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--spreads", action="store_true")
    ap.add_argument("--nudge", action="store_true")
    args = ap.parse_args()
    both = not (args.spreads or args.nudge)
    rc = 0
    if args.spreads or both:
        print("── SPREADS " + "─" * 62)
        rc |= spreads()
        print()
    if args.nudge or both:
        print("── NUDGE " + "─" * 64)
        rc |= nudge()
    return rc


if __name__ == "__main__":
    sys.exit(main())
