"""The cover sweep still describes the themes and roles that exist now.

D-205 and D-206 are both one defect seen twice: a property cover derives a
contrast pair from `theme_color`, which is the account's brand, and nothing
puts a floor under it. Neither was caught, for two different reasons, and both
reasons are about the GATE rather than the documents:

  * the contrast gate measures **six brands**, chosen because the email audit
    uses them. On those six, `linen`'s cover footer passes at brand luminance
    0.230 and below and fails at 0.439 and above — and the corpus contains
    nothing in between, so the six cannot say where the boundary is. A brand an
    agent picks tomorrow lands anywhere in that gap and the build reports it as
    a regression although no template changed.

  * `EXPECTED_DECLINED = 1` counted the elements the measurer cannot read, and
    was right about the number for twenty days while the element it covered
    changed template, page architecture and colour model. The justification for
    declining it — a hand calculation on `#FF6B5B`, the default accent no
    customer has — was never recomputed. **A count cannot express "and it is
    still the thing the reasoning was about."** (§0.6, 2026-10-21.)

So this file gates the RECORD that `scripts/sweep_cover_brand_space.py` writes,
and the two things that record has to keep being true of:

  1. it describes the themes the renderer actually has, and
  2. it describes the roles those templates actually interpolate.

Neither is a list kept beside the thing it describes. Both are read from the
registry and from the templates on every run, so a cut, a rename, or a template
that stops putting the brand behind its cover fails here rather than going
quiet.

WHY A RECORD AND NOT A LIVE MEASUREMENT
---------------------------------------
The sweep renders 3 themes x 38 brands and measures every text run in each — a
few minutes. That belongs in a script whose output is reviewed in a diff, the
same contract as `golden/themes.json` and the contrast baseline. What belongs in
the suite is the question a record cannot answer about itself: **is it still
about this codebase?**
"""
import json
import re
import sys
import warnings
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "apps/worker/src"))

RECORD = REPO / "apps/worker/tests/cover_brand_sweep.json"
SWEEP = REPO / "scripts/sweep_cover_brand_space.py"

#: The gap the six presets leave. Any boundary inside it is invisible to them.
PRESET_GAP = (0.230, 0.439)


def _record():
    if not RECORD.exists():
        pytest.fail(
            f"{RECORD.relative_to(REPO)} is missing. Build it with\n"
            f"    python3 {SWEEP.relative_to(REPO)}\n"
            f"It is the brand-space sweep D-205 and D-206 were filed for; the "
            f"suite reads it rather than re-rendering 114 documents."
        )
    return json.loads(RECORD.read_text(encoding="utf-8"))


def _sweep_module():
    import importlib.util
    spec = importlib.util.spec_from_file_location("_sweep", SWEEP)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_the_record_names_the_themes_the_renderer_has():
    """A cut, an addition or a rename invalidates the sweep, loudly.

    This is the assertion `EXPECTED_DECLINED = 1` could not make. It did not
    know which theme it was about, so the theme it covered being renamed and
    rebuilt on a new page architecture cost it nothing. (The former name is
    left out on purpose: `test_no_live_code_path_names_a_retired_theme` reads
    this file, and it is right to.)
    """
    from worker.theme_registry import THEME_TEMPLATES
    live = set(THEME_TEMPLATES)
    recorded = set(_record()["themes"])
    assert recorded == live, (
        f"the sweep describes {sorted(recorded)} and the renderer has "
        f"{sorted(live)}. Re-run scripts/sweep_cover_brand_space.py — a theme "
        f"that was cut, added or RENAMED makes this record about a different "
        f"codebase, which is D-206's mechanism exactly."
    )


def test_the_record_names_the_template_each_theme_uses():
    from worker.theme_registry import THEME_TEMPLATES
    rec = _record()["themes"]
    for theme, template in sorted(THEME_TEMPLATES.items()):
        assert rec[theme]["template"] == template, (
            f"{theme} renders {template} and the sweep measured "
            f"{rec[theme]['template']}"
        )


def test_the_recorded_roles_are_the_roles_the_live_template_interpolates():
    """Read off the template, not listed anywhere.

    The surfaces in this sweep are brand-dependent because the template puts a
    `theme_*` value behind them. If a template stops doing that — which is what
    the structural fix for D-205/D-206 amounts to — this test is how the record
    finds out, and the sweep for that theme should come back empty rather than
    stale.
    """
    sweep = _sweep_module()
    for theme, info in sorted(_record()["themes"].items()):
        now = sweep.roles_used(info["template"])
        assert info["roles_used"] == now, (
            f"{theme}'s template interpolates {now} and the sweep recorded "
            f"{info['roles_used']}. Re-run the sweep: the surfaces it measured "
            f"are derived from these roles, so a change here changes what is "
            f"brand-dependent."
        )


def test_the_sweep_covers_the_gap_the_presets_leave():
    """The reason the sweep exists. Six brands cannot locate a boundary that
    sits between two of them."""
    lums = sorted(b["luminance"] for b in _record()["brands"])
    inside = [l for l in lums if PRESET_GAP[0] < l < PRESET_GAP[1]]
    assert len(inside) >= 3, (
        f"only {len(inside)} swept brand(s) fall between luminance "
        f"{PRESET_GAP[0]} and {PRESET_GAP[1]}, which is the band the six "
        f"presets leave empty and the band D-205's boundary is in. Raise "
        f"--steps."
    )


def test_every_declined_surface_carries_the_calculation_that_excuses_it():
    """D-206, made structural.

    A surface the measurer cannot read is excluded from the contrast gate. That
    is correct — a number that means nothing is worse than an absence. What was
    missing is that the hand calculation excusing it lived in a COMMIT MESSAGE
    while the element it described changed underneath it.

    So the record carries the calculation next to the exclusion, per brand, and
    a declined surface with nothing recorded fails here. The next person to add
    gradient-clipped text is told to do the arithmetic rather than inheriting
    somebody else's.
    """
    rec = _record()
    missing = []
    for theme, info in sorted(rec["themes"].items()):
        for slot, brands in sorted(info["surfaces"].items()):
            if not any(v["declined"] for v in brands.values()):
                continue
            hand = (info.get("hand_calculations") or {}).get(slot)
            if not hand:
                missing.append(f"{theme} {slot}")
    assert not missing, (
        "declined surface(s) with no recorded calculation:\n  "
        + "\n  ".join(missing)
        + "\n\nThe measurer cannot read these, so the gate excludes them. Work "
          "out the real contrast by hand FOR EACH BRAND and record it in "
          f"{RECORD.name} under the theme's `hand_calculations`. A count of "
          "declined elements is what let D-206 sit for twenty days: it was "
          "right about the number and silent about the reasoning."
    )


def test_the_sweep_script_reads_the_registry_rather_than_a_list():
    """A gate on the gate. If the sweep ever hard-codes its themes, the two
    assertions above compare a list with itself."""
    body = SWEEP.read_text(encoding="utf-8")
    assert "from worker.theme_registry import THEME_TEMPLATES" in body, (
        "the sweep no longer reads the theme registry, so "
        "test_the_record_names_the_themes_the_renderer_has would be comparing "
        "a hard-coded list against itself"
    )
    assert not re.search(r'^\s*THEMES\s*=\s*[\[(]', body, re.M), (
        "the sweep has grown a literal theme list"
    )


# ── D-206 · a decline that REPORTS ─────────────────────────────────────────────
#
# Declining the MEASUREMENT must not decline the FINDING. `EXPECTED_DECLINED = 1`
# failed by being silent, not by declining: it was right about the number for
# twenty days while the surface it covered was unreadable for four of six
# brands.
#
# WCAG has no model for a text surface whose contrast varies across the glyph
# run — a gradient clipped to the letters is one ratio at the first stop and
# another at the last, and there is no rule for "some of the letters pass". So
# the instrument cannot answer this and should not pretend to. What it can do is
# carry the answer a person worked out, and **fail on it**.
#
# THIS TURNS THE BUILD RED ON PURPOSE. Jerry, 2026-10-21: *"Harbor at 2.07:1 for
# a violet-branded customer is a cover a real agent would send and cannot read.
# Red is the correct colour."* It goes green when the cover is fixed, not when
# the exclusion is widened. See D-206.

#: A dated block of per-brand figures. Exactly one, so a second calculation has
#: to retire the first in a diff rather than sit beside it — which is how the
#: original excuse outlived the template it described.
FIGURES_KEY = re.compile(r"^computed_\d{4}_\d{2}_\d{2}$")


def _calculations():
    """(theme, selector, calculation) for every declined surface."""
    out = []
    for theme, info in sorted(_record()["themes"].items()):
        hand = info.get("hand_calculations") or {}
        for selector, brands in sorted(info["surfaces"].items()):
            if any(v["declined"] for v in brands.values()):
                out.append((theme, selector, hand.get(selector)))
    return out


def _figures(calc):
    """The one dated block, its reading, and the threshold — or an explanation."""
    dated = sorted(k for k in calc if FIGURES_KEY.match(k))
    if len(dated) != 1:
        return None, f"{len(dated)} dated figure block(s), expected exactly one: {dated}"
    reading = calc.get("authoritative_reading")
    if not reading:
        return None, "no `authoritative_reading`, so nothing says which of the readings the verdict is taken on"
    threshold = calc.get("threshold")
    if not isinstance(threshold, (int, float)):
        return None, f"threshold is {threshold!r}, not a number"
    figures = calc[dated[0]]
    missing = [b for b, v in figures.items() if reading not in v]
    if missing:
        return None, f"brand(s) {sorted(missing)} have no `{reading}` figure"
    return (dated[0], reading, threshold, figures), None


def test_a_declined_surfaces_figures_are_readable_as_data():
    """The contract the next calculation has to meet.

    Prose is not parsed anywhere here — `verdict` and `method` are for people.
    The build's colour comes from the numbers and from the key that names which
    numbers count, because a gate that greps an explanation measures the
    explanation (§0.6, eight instances).
    """
    for theme, selector, calc in _calculations():
        assert calc, f"{theme} {selector} is declined with no calculation at all"
        parsed, why = _figures(calc)
        assert parsed, f"{theme} {selector}: {why}"


def test_a_declined_surface_whose_calculation_fails_fails_the_build():
    """D-206. The finding is not excused by the instrument's inability to read it.

    Reported per BRAND and per RATIO rather than per element, because
    "declined surface fails" is another red line nobody reads, and
    "harbor .cover-title span, violet, 2.07:1 against 3.0" is a finding.
    """
    failures = []
    for theme, selector, calc in _calculations():
        parsed, why = _figures(calc)
        if not parsed:
            continue                      # the test above owns that case
        dated, reading, threshold, figures = parsed
        for brand, readings in sorted(figures.items()):
            ratio = readings[reading]
            if ratio < threshold:
                failures.append(
                    f"{theme} {calc.get('element') or selector}, {brand}, "
                    f"{ratio:.2f}:1 against {threshold} ({reading}, {dated})")
    assert not failures, (
        f"{len(failures)} unmeasured contrast failure(s) — a surface this "
        f"instrument cannot read, whose hand calculation says it fails:\n  "
        + "\n  ".join(failures)
        + "\n\nTHIS RED IS DELIBERATE (Jerry, 2026-10-21). The gradient-clipped "
          "cover title is unreadable for the darker brands and WCAG has no model "
          "for a surface whose contrast varies across the glyph run, so the "
          "measurement is declined and the FINDING is not. It goes green when "
          "the cover is fixed — not by widening the exclusion, and not by "
          "regenerating anything. See D-206 and "
          "docs/THEME_MAPPING_AND_FOOTER_FOR_DESIGN_2026-10-21.md."
    )


def test_the_figures_are_reported_on_every_run_not_only_on_failure():
    """Reporting, which is the half `EXPECTED_DECLINED` lacked.

    A warning rather than a print: pytest prints a warnings summary whether the
    run passed or failed, so the figures reach CI's log on a green build too.
    When this surface is fixed and nothing is declined any more, there is
    nothing to report and the warning stops — which is the right silence.
    """
    lines = []
    for theme, selector, calc in _calculations():
        parsed, _ = _figures(calc)
        if not parsed:
            continue
        dated, reading, threshold, figures = parsed
        for brand, readings in sorted(figures.items(), key=lambda kv: kv[1][reading]):
            verdict = "FAILS" if readings[reading] < threshold else "ok"
            lines.append(f"{theme} {calc.get('element') or selector} {brand} "
                         f"{readings[reading]:.2f}:1/{threshold} {verdict}")
    if lines:
        warnings.warn(
            "declined contrast surfaces, hand-calculated (D-206):\n  "
            + "\n  ".join(lines), stacklevel=1)
    # The assertion is about the reporting, not about the figures: if something
    # is declined, this run said so.
    assert bool(lines) == bool(_calculations()), (
        "a declined surface produced no reported figures")
