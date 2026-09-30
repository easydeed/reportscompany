#!/usr/bin/env python3
"""How far does a contrast baseline key move when only the layout moves? (D-153)

    python3 scripts/measure_key_stability.py               # all three
    python3 scripts/measure_key_stability.py --nudge       # the churn (the floor)
    python3 scripts/measure_key_stability.py --collisions  # the bound (the ceiling)
    python3 scripts/measure_key_stability.py --spreads     # single-brand spreads

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

#: The tolerance in `test_pdf_contrast.py`. Re-derive it, do not trust it.
#:
#: IT WAS 48 AND 48 WAS WRONG. That number came from `--spreads` below, which
#: measures the TEN SINGLE-BRAND production renders. The gate's corpus is
#: sixty documents across SIX brand colours, and two of those brands are 41
#: apart — so 48 merged them, losing the distinction six brands are rendered
#: to make. `--collisions` measures the corpus the tolerance is applied to,
#: which is the one that decides the ceiling. `--spreads` is kept because it
#: is still the clearest picture of position noise; it is just not the bound.
RECOMMENDED_TOLERANCE = 12


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


def collisions():
    """The ceiling: how close do two DISTINCT baseline entries get?

    This is the measurement that matters, and the one the first
    recommendation skipped. A tolerance merges any two entries closer than
    itself, so the smallest distance between two entries that genuinely
    differ is the hard ceiling — and on this corpus that is two brand
    colours, not two shades of one gradient.
    """
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "_pdf_contrast", REPO / "apps/worker/tests/test_pdf_contrast.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    entries = sorted(mod.read_baseline())
    pairs = []
    for i, x in enumerate(entries):
        for y in entries[i + 1:]:
            if x[0] == y[0] and x[1] == y[1]:
                pairs.append((max(distance(x[2], y[2]), distance(x[3], y[3])), x, y))
    pairs.sort()

    print(f"{len(entries)} baseline entries, {len(pairs)} pairs sharing family+selector\n")
    print("closest 12 — a tolerance at or above any of these merges that pair:\n")
    for dist, x, y in pairs[:12]:
        print(f"  {dist:4d}  {x[0]:18s} {x[1][:22]:22s} {x[3]}  vs  {y[3]}")

    t = RECOMMENDED_TOLERANCE
    merged = {y for dist, x, y in pairs if dist <= t}
    print(f"\n  at tolerance {t}: {len(merged)} of {len(entries)} entries merge into another")
    for dist, x, y in pairs:
        if dist > t:
            print(f"  nearest pair LEFT DISTINCT: {dist} — {x[0]} {x[1]} "
                  f"{x[3]} vs {y[3]}")
            break
    print("\n  Every merged pair should be ONE FINDING SAMPLED TWICE. Read them.")
    print("  If any is two different colours the design uses on purpose — two")
    print("  brands, a panel against a page — the tolerance is too high.")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--spreads", action="store_true")
    ap.add_argument("--nudge", action="store_true")
    ap.add_argument("--collisions", action="store_true")
    args = ap.parse_args()
    all_ = not (args.spreads or args.nudge or args.collisions)
    rc = 0
    if args.nudge or all_:
        print("── NUDGE · the churn, which sets the floor " + "─" * 31)
        rc |= nudge()
        print()
    if args.collisions or all_:
        print("── COLLISIONS · the corpus, which sets the ceiling " + "─" * 23)
        rc |= collisions()
        print()
    if args.spreads or all_:
        print("── SPREADS · position noise on the single-brand renders " + "─" * 18)
        rc |= spreads()
    return rc


if __name__ == "__main__":
    sys.exit(main())
