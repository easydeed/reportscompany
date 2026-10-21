#!/usr/bin/env python3
"""Sweep the brand input space across the live property covers.

WHY THIS EXISTS
---------------
`test_pdf_contrast.py` measures six brands. Six is the set the email audit
uses, which made it the right set to compare surfaces across — and the wrong
set to decide a threshold with. Measured on those six, the `linen` cover
footer fails for brands at relative luminance 0.439 and 0.481 and passes at
0.230 and below. **Nothing in the corpus sits between 0.23 and 0.44**, so the
six cannot say where the boundary is, and a brand an agent picks tomorrow lands
anywhere in that gap (D-205).

That is §0.6's derived-set rule for the third time in a month — a bound taken
from the inputs that happened to be present. The answer is not a seventh
preset. It is to sweep the axis the failure actually depends on.

WHAT IT SWEEPS, AND WHY NOT A SINGLE HUE
----------------------------------------
32 generated brands plus the six presets. The generated ramp walks relative
luminance from near-black to near-white **and rotates hue as it goes**, because
a ramp at one hue would be a set derived from one input — the mistake this file
exists to stop, made inside the fix for it. Each step's luminance is recorded
with its measurement, so the output is a curve rather than a verdict.

WHAT IT MEASURES
----------------
The live themes come from the renderer's own registry, and **the roles come from
the live templates**: each template is read for the `theme_*` values it actually
interpolates, so a template that stops deriving a surface from the brand drops
out of the sweep by itself. Nothing here maintains a list of surfaces beside the
thing it describes — that is what let `EXPECTED_DECLINED = 1` outlive its own
theme (D-206).

Measurement is `scripts/measure_contrast_by_pixel.py`, the same instrument the
gate uses. Text whose glyphs are painted by a clipped gradient is declined by
that instrument and is reported here as `declined`, not as a pass: D-206 is
exactly a declined surface that was failing.

    python3 scripts/sweep_cover_brand_space.py [--steps 32] [--out PATH]

Runtime is a few minutes per theme. It writes a record the suite reads rather
than re-running: `tests/test_cover_brand_sweep_is_current.py` asserts the record
still describes the live themes and the roles they still use.
"""
import argparse
import colorsys
import importlib.util
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "apps/worker/src"))

DEFAULT_OUT = REPO / "apps/worker/tests/cover_brand_sweep.json"

#: WHICH SURFACES THIS SWEEP IS ABOUT, AND IT IS NOT A SELECTOR PATTERN.
#:
#: The first version matched selectors containing `cover` or `brand`, on the
#: reasoning that the cover is where both D-205 and D-206 live. It ran, and it
#: **excluded D-206's own surface** — whose selector is bare `span`, because
#: that is what the measurer reports for `.cover-title span`. A filter named
#: after the instances, inside the tool built to stop exactly that (§0.6).
#:
#: So nothing is filtered by name. Every text run is measured, and a surface is
#: kept when **its colours actually move with the brand** — the foreground, the
#: backdrop, or both, differ across the swept brands. That is the construct:
#: brand-dependence is a property of the measurement, not of the selector, and
#: a surface that stops being brand-derived drops out by itself.
#:
#: Runs the instrument declines are kept whatever they do, because a declined
#: surface is the one case where "it did not vary" means "it was not measured".


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _srgb_to_lum(rgb):
    def f(c):
        c /= 255
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (f(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def luminance(hex_colour):
    h = hex_colour.lstrip("#")
    return _srgb_to_lum(tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)))


def _at_luminance(target, hue, sat=0.75):
    """A colour at `hue` whose relative luminance is `target`, by bisection.

    STEPPING HSL LIGHTNESS WAS NOT GOOD ENOUGH, and the first version did.
    Lightness is what a colour picker offers, so it looked like the honest
    axis — but the thresholds are in **relative luminance**, and the two are
    not linear in each other. A 32-step lightness ramp put only three brands
    inside the 0.230–0.439 band the six presets leave empty, at 0.251, 0.260
    and 0.394: a 0.13-wide hole in the middle of the one region the sweep
    exists to cover. A derived set that does not cover the thing it was derived
    to cover (§0.6), inside the tool built for two instances of that.
    """
    lo, hi = 0.0, 1.0
    for _ in range(40):
        mid = (lo + hi) / 2
        r, g, b = colorsys.hls_to_rgb(hue, mid, sat)
        got = _srgb_to_lum((r * 255, g * 255, b * 255))
        if got < target:
            lo = mid
        else:
            hi = mid
    r, g, b = colorsys.hls_to_rgb(hue, (lo + hi) / 2, sat)
    return "#%02x%02x%02x" % (round(r * 255), round(g * 255), round(b * 255))


def ramp(steps):
    """`steps` brands evenly spaced in RELATIVE LUMINANCE, hue rotating.

    Luminance, because that is the axis the thresholds are on and the axis the
    failures track. Hue rotates as it goes, because a ramp at one hue would be
    a set derived from one input — the mistake this file exists to stop, made
    inside the fix for it. Saturation is held at 0.75: brand colours are
    saturated, and a desaturated ramp would be a sweep of greys wearing the
    name of a sweep of brands.

    The range stops short of black and white. A brand at luminance 0.99 is not
    a brand anyone picks, and including it would put the boundary this sweep is
    looking for in the middle of a region nobody uses.
    """
    out = []
    for i in range(steps):
        target = 0.02 + (0.90 - 0.02) * i / (steps - 1)
        hue = (i * 360.0 / steps * 1.618) % 360 / 360.0   # irrational-ish turn
        out.append((f"ramp{i:02d}", _at_luminance(target, hue)))
    return out


def live_themes():
    """The renderer's registry, not a list in this file."""
    from worker.theme_registry import THEME_TEMPLATES
    return dict(sorted(THEME_TEMPLATES.items()))


#: BOTH GENERATIONS OF ROLE NAME, and the first version had only one.
#:
#: `linen` and `harbor` take the brand as `theme_color*`, which is what the
#: property builder has always handed a template. `atlas` renders through
#: Design's shared `_v2/report.jinja2`, which names the same values
#: `primary`, `on_primary`, `tint`, `display_ink`, `primary_on_dark`,
#: `primary_ink`, `primary_dark`. Reading only the first set recorded
#: `roles_used: []` for atlas — a theme whose cover the sweep then measured
#: failing for one brand in the ramp, which is not what "no brand-derived
#: roles" means.
#:
#: A list of names that knew one vintage of the thing it names: §0.6, and the
#: fourth instance of that family inside this one file.
ROLE_NAMES = (
    # the property builder's own
    "theme_color", "theme_color_light", "theme_color_dark",
    "theme_color_on_dark", "theme_color_on_light", "theme_color_text",
    # Design's shared page
    "primary", "primary_dark", "primary_ink", "on_primary", "tint",
    "primary_on_dark", "display_ink",
)


PROPERTY_ROOT = REPO / "apps/worker/src/worker/templates/property"

#: `{% include %}`, `{% extends %}`, `{% import %}`, `{% from … import %}`.
_PULLS_IN = re.compile(r"\{%-?\s*(?:include|extends|import|from)\s+[\"\']([^\"\']+)[\"\']")


def _template_closure(template_rel, seen=None):
    """`template_rel` and every template it pulls in, transitively.

    THIS FOLLOWS INCLUDES, AND THE FIRST VERSION DID NOT — which made it wrong
    on the only theme it mattered for. `atlas` was rewired onto Design's shared
    page: its entry file is thirty-odd lines of `{% set %}` and one
    `{% include %}`, so reading that file alone found **no** brand roles and
    recorded `roles_used: []`. The gate built on it would then have asserted
    `[] == []` forever and never noticed atlas becoming brand-dependent.

    An assertion scoped to one file, named as if scoped to the construct —
    §0.6, and inside the fix for two other instances of it.
    """
    seen = seen if seen is not None else set()
    rel = template_rel.lstrip("/")
    if rel in seen:
        return seen
    path = PROPERTY_ROOT / rel
    if not path.exists():
        # A path that does not resolve under property/ is recorded rather than
        # guessed at: the caller asserts on the closure, so a silent miss here
        # is a narrower claim wearing the same name.
        seen.add(rel + "  [NOT FOUND]")
        return seen
    seen.add(rel)
    for ref in _PULLS_IN.findall(path.read_text(encoding="utf-8")):
        _template_closure(ref, seen)
    return seen


def roles_used(template_rel):
    """Which brand-derived roles this theme's templates name, read off the files.

    The point of reading rather than listing: a template that stops putting the
    brand behind its cover stops being swept, and a template that starts gets
    swept without anyone remembering to add it.

    Matched as a WORD anywhere in the closure rather than only inside `{{ }}`,
    because a role reaches a shared page through `{% set accent = theme_color %}`
    as often as through an interpolation, and an expression is a use.
    """
    found = set()
    for rel in sorted(_template_closure(template_rel)):
        if rel.endswith("[NOT FOUND]"):
            continue
        body = (PROPERTY_ROOT / rel).read_text(encoding="utf-8")
        found |= {r for r in ROLE_NAMES if re.search(r"\b" + r + r"\b", body)}
    return sorted(found)


def template_closure(template_rel):
    """The files `roles_used` read, so the record can name them."""
    return sorted(_template_closure(template_rel))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--steps", type=int, default=32)
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    ap.add_argument("--themes", default="", help="comma-separated subset, for a quick pass")
    args = ap.parse_args()

    corpus = _load(REPO / "scripts/measure_pdf_contrast.py", "_corpus")
    measure = _load(REPO / "scripts/measure_contrast_by_pixel.py", "_pixel")
    from worker.property_builder import PropertyReportBuilder

    themes = live_themes()
    if args.themes:
        wanted = set(args.themes.split(","))
        themes = {k: v for k, v in themes.items() if k in wanted}

    brands = ramp(args.steps) + list(corpus.BRANDS)
    base = corpus.property_documents.__wrapped__() if hasattr(
        corpus.property_documents, "__wrapped__") else None

    # HAND CALCULATIONS SURVIVE A REGENERATION — D-206.
    #
    # A surface whose glyphs are painted by a clipped gradient cannot be
    # measured by this instrument, and is excluded from the contrast gate. That
    # exclusion has to be excused by arithmetic done by a person, and the thing
    # that went wrong is that the arithmetic lived in a commit message while
    # the element it described changed template and colour model underneath it.
    # So it lives HERE, next to the exclusion, and a regeneration carries it
    # forward rather than dropping it:
    # `test_every_declined_surface_carries_the_calculation_that_excuses_it`
    # fails on a declined surface with nothing recorded.
    previous = {}
    out_path = Path(args.out)
    if out_path.exists():
        try:
            prior = json.loads(out_path.read_text(encoding="utf-8"))
            previous = {k: v.get("hand_calculations") or {}
                        for k, v in (prior.get("themes") or {}).items()}
        except (ValueError, AttributeError):
            previous = {}

    record = {
        "steps": args.steps,
        "themes": {},
        "brands": [{"name": n, "hex": h, "luminance": round(luminance(h), 4)}
                   for n, h in brands],
    }

    for theme, template in themes.items():
        used = roles_used(template)
        docs = {}
        for name, primary in brands:
            data = dict(corpus.PROPERTY_BASE) if hasattr(corpus, "PROPERTY_BASE") else None
            if data is None:
                data = _property_base()
            data["theme"] = theme
            data["branding"] = {"primary_color": primary, "company_name": "Coastal Realty"}
            docs[f"property__{theme}__{name}"] = PropertyReportBuilder(data).render_html()
        rows = measure.score(measure.measure_docs(docs))
        # Group by selector first, so "did this move with the brand?" is asked
        # of the selector rather than of a (selector, colour) pair — a pair
        # whose colour varies IS the variation, so keying on it before the
        # question is asked would answer it by construction.
        by_selector = {}
        for r in rows:
            by_selector.setdefault(r["selector"] or "", []).append(r)

        per = {}
        for selector, runs in by_selector.items():
            fgs = {r["fg_hex"] for r in runs}
            bgs = {r["bg_hex"] for r in runs}
            declined = any(r["unmeasurable"] for r in runs)
            if len(fgs) == 1 and len(bgs) == 1 and not declined:
                continue                      # the same pairing on every brand
            # KEYED ON THE SELECTOR ALONE, AND THE FIRST VERSION KEYED ON
            # (selector, foreground). Where the FOREGROUND is the brand-derived
            # half — harbor's cover titles and contents numbers — every brand
            # produces a different one, so every slot held exactly one brand and
            # the output was one row per brand instead of a curve across them.
            # A key that includes the thing being varied cannot describe the
            # variation.
            for r in runs:
                brand = r["doc"].rsplit("__", 1)[1]
                per.setdefault(selector, {})[brand] = {
                    "fg": r["fg_hex"], "bg": r["bg_hex"],
                    "ratio": round(r["ratio"], 2),
                    "needs": r["needs"], "declined": bool(r["unmeasurable"]),
                }
        declined_slots = sorted(s for s, b in per.items()
                                if any(v["declined"] for v in b.values()))
        hand = {s: (previous.get(theme, {}).get(s) or SEED_CALCULATIONS.get(s))
                for s in declined_slots}
        record["themes"][theme] = {"template": template, "roles_used": used,
                                   "templates_read": template_closure(template),
                                   "surfaces": per, "hand_calculations": hand}
        print(f"{theme}: {len(docs)} documents, {len(rows)} runs, "
              f"{len(per)} brand-dependent surfaces, {len(declined_slots)} declined, "
              f"roles {used}")
        for s in declined_slots:
            if not hand[s]:
                print(f"    DECLINED WITH NO CALCULATION: {s.replace(chr(9), ' ')}")

    Path(args.out).write_text(json.dumps(record, indent=1, sort_keys=True))
    print(f"\nwrote {args.out}")
    _summarise(record)


#: The one declined surface as of 2026-10-21, with the arithmetic that excuses
#: excluding it — recomputed per brand, which is what D-206 was: the original
#: figures (4.47 worst / 9.28 best) were correct and were computed on `#FF6B5B`,
#: the template default used only when no brand is set.
#:
#: Seeded here so the first regeneration does not start red. Everything after
#: that is carried forward from the previous record, and a NEW declined surface
#: has to be worked out by whoever adds it.
#:
#: KEYED BY SELECTOR, NOT BY THEME — and the first version named the theme.
#: `tests/test_rename_scope_numbers_are_current.py` refused it: a quoted theme
#: name in a scanned tree is a site a future rename has to visit, and its own
#: failure message offers the better remedy rather than the constant — *"derive
#: the name from the registry instead, which is what the other fifteen do."*
#: The mechanism here is the selector's rather than the theme's anyway, and that
#: is the more honest statement, since this element has already moved once.
SEED_CALCULATIONS = {
    "span": {
        # The selector AS THE TEMPLATE WRITES IT, because `span` is what the
        # measurer reports and "harbor span" is not something a person can go
        # and look at. The build's red names this.
        "element": ".cover-title span — harbor_report.jinja2:52",
        "why_unmeasurable": (
            "the cover title's inner span is painted by a gradient clipped to "
            "the glyphs via -webkit-text-fill-color:transparent, which is the "
            "property the measurer uses to blank text. Blanking changes "
            "nothing, so the sampled backdrop is the element's own gradient "
            "and the reported foreground is not what the reader sees."
        ),
        "glyphs": "linear-gradient(135deg, theme_color 0%, theme_color_light 50%, #FFB199 100%)",
        "backdrop": "--gradient-dark #1A1F36 -> #2D3348, plus brand circles at 0.10 and 0.08 opacity",
        "threshold": 3.0,
        # WHICH OF THE THREE READINGS THE VERDICT IS TAKEN ON, stated as data
        # rather than left to be inferred from `method`. The gate fails the
        # build on this reading, so a judgement about which one is authoritative
        # has to be made in a diff instead of in prose nobody re-reads.
        "authoritative_reading": "lighter_stop_with_tint",
        "method": (
            "worst glyph stop against the worst backdrop point. Conservative: "
            "the glyphs are a gradient, so part of the word clears the "
            "threshold even where the first stop does not, and WCAG has no "
            "rule for 'some of the letters pass'."
        ),
        "computed_2026_10_21": {
            "violet":         {"lighter_stop_with_tint": 2.07, "lighter_stop": 2.20, "darker_stop": 2.85},
            "coastal":        {"lighter_stop_with_tint": 2.16, "lighter_stop": 2.33, "darker_stop": 3.03},
            "demo_title":     {"lighter_stop_with_tint": 2.49, "lighter_stop": 2.59, "darker_stop": 3.36},
            "luxury_estates": {"lighter_stop_with_tint": 2.99, "lighter_stop": 3.34, "darker_stop": 4.34},
            "amber":          {"lighter_stop_with_tint": 4.91, "lighter_stop": 5.82, "darker_stop": 7.56},
            "lime":           {"lighter_stop_with_tint": 5.27, "lighter_stop": 6.33, "darker_stop": 8.22},
        },
        "verdict": (
            "FAILS. violet on every reading; coastal and demo_title on all but "
            "the darkest backdrop point with no tint; luxury_estates only with "
            "the tint. D-206."
        ),
        "superseded_by": (
            "the original excuse, '4.47:1 at the worst pair of stops, 9.28:1 at "
            "the best' (3ac024e4), which is #FF6B5B on #2D3348 and #FFB199 on "
            "#1A1F36 — the template default, not any brand."
        ),
    },
}


def _property_base():
    """The corpus's own property fixture, minus the theme and the brand."""
    return {
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


def _summarise(record):
    lum = {b["name"]: b["luminance"] for b in record["brands"]}
    print("\nwhere each surface crosses its threshold, by brand luminance:")
    for theme, info in sorted(record["themes"].items()):
        for sel, brands in sorted(info["surfaces"].items()):
            fails = sorted((lum[b] for b, v in brands.items()
                            if not v["declined"] and v["ratio"] < v["needs"]))
            passes = sorted((lum[b] for b, v in brands.items()
                             if not v["declined"] and v["ratio"] >= v["needs"]))
            declined = [b for b, v in brands.items() if v["declined"]]
            if declined:
                print(f"  {theme:<8} {sel:<34}  DECLINED for "
                      f"{len(declined)} brand(s) — measured by hand or not at all")
                continue
            if not fails:
                continue
            band = (f"fails from L={fails[0]:.3f} to L={fails[-1]:.3f}; "
                    f"passes {('up to L=%.3f' % max(p for p in passes if p < fails[0])) if any(p < fails[0] for p in passes) else 'nowhere below'}")
            print(f"  {theme:<8} {sel:<34}  {len(fails)}/{len(fails)+len(passes)}  {band}")


if __name__ == "__main__":
    main()
