"""
The template-colour lint, and the guards that keep it from matching nothing.

WHY THE GUARDS ARE THE POINT
----------------------------
A lint that finds zero violations is indistinguishable from a lint that is
broken, and this repository has been bitten by exactly that shape before: three
branches in a row updated the defect board with a `str.replace` whose anchor no
longer existed. Each one silently did nothing, and the summary drifted for a
week. Nothing reports "I matched nothing" unless you ask it to.

So the rule was run against `main` before a single template was touched. It
reported 111 findings across 26 of 30 files — on code we know is full of brand
literals, which is the only result that means the regex is alive. Both
directions are pinned below: a dirty fixture must produce findings, and a clean
fixture must produce none.
"""
import pathlib
import subprocess
import sys

import pytest

REPO = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

import lint_template_colors as lint  # noqa: E402


def lint_text(tmp_path, text, name="t.jinja2"):
    p = tmp_path / name
    p.write_text(text)
    return lint.lint_file(p) + lint.bare_suppressions(p)


# ---------------------------------------------------------------------------
# The two controls
# ---------------------------------------------------------------------------

DIRTY = """
<style>
  :root {
    --primary-color: #0d9488;
    --accent-light: #a6e4de;
    --color-accent: {{ accent_color | default('#0D9488', true) }};
  }
  .hero { background: linear-gradient(135deg, var(--color-accent) 0%, #0c5c54 100%); }
</style>
"""

CLEAN = """
<style>
  :root {
    --primary-color: {{ tokens.primary }};
    --primary-ink: {{ tokens.primary_ink }};
    --canvas: #ffffff;
    --card: #f8fafc;
    --rule: #e2e8f0;
    --ink: #0f172a;
  }
  .hero { background: linear-gradient(135deg, var(--primary), var(--primary-dark)); }
  .delta--bad { color: #dc2626; }
</style>
"""


def test_the_rule_finds_brand_literals_when_they_are_there(tmp_path):
    """
    POSITIVE CONTROL. If this ever passes with zero findings the rule has
    stopped matching, and every green run of it since is worthless.
    """
    found = lint_text(tmp_path, DIRTY)
    assert found, "the rule reported nothing on a template that is nothing but brand literals"
    rules = {f.rule for f in found}
    assert "BRAND-ROLE" in rules
    assert "BRAND-ADJACENT" in rules
    assert {f.hex_value for f in found} >= {"#0d9488", "#a6e4de", "#0c5c54"}


def test_the_rule_is_silent_on_a_template_that_uses_tokens(tmp_path):
    """
    NEGATIVE CONTROL. A rule that flags everything is as useless as one that
    flags nothing, and it is the reason a migrated template can ever be green.
    Fixed neutrals and a status red must pass untouched — §3.2 and §3.3 specify
    them as literals.
    """
    assert lint_text(tmp_path, CLEAN) == []


# ---------------------------------------------------------------------------
# BRAND-ROLE
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("decl", [
    "--primary-color: #0d9488;",
    "--accent-color:#0D9488;",
    "--color-primary: #0d9488;",
    "--color-primary-dark: #21c7b7;",
    "--color-accent-light: #2a3875;",
    "--pct-blue: #7c3aed;",
    "--theme-cover: #7c3aed;",
    "--brand-rule: #7c3aed;",
    "--navy: {{ theme_color | default('#15216E', true) }};",
    "--x: {{ accent_on_dark | default('#5eead4', true) }};",
])
def test_brand_role_declarations_are_caught(tmp_path, decl):
    found = [f for f in lint_text(tmp_path, ":root{%s}" % decl) if f.rule == "BRAND-ROLE"]
    assert found, f"missed a brand literal in {decl!r}"


def test_the_three_digit_form_is_recognised(tmp_path):
    """
    `#0d9488` and `#0D9` are the same kind of mistake and CSS accepts both.
    Added because the differential run found this: narrowing the pattern to six
    digits broke nothing in the suite, which meant the short form was riding on
    an untested branch.
    """
    found = lint_text(tmp_path, ":root{--primary-color:#0a9;}")
    assert [(f.rule, f.hex_value) for f in found] == [("BRAND-ROLE", "#00aa99")]


def test_a_status_colour_in_a_brand_role_is_still_a_violation(tmp_path):
    """
    Exemption is by ROLE, not by value. #dc2626 is a legitimate status red and
    an illegitimate hardcoded primary, and which one it is depends entirely on
    where it sits.
    """
    found = lint_text(tmp_path, ":root{--primary-color: #dc2626;}")
    assert [f.rule for f in found] == ["BRAND-ROLE"]


def test_a_neutral_role_holding_a_neutral_is_not_a_violation(tmp_path):
    assert lint_text(tmp_path, ":root{--canvas:#ffffff; --ink:#0f172a; --rule:#e2e8f0;}") == []


# ---------------------------------------------------------------------------
# BRAND-ADJACENT
# ---------------------------------------------------------------------------

def test_a_hand_picked_relative_of_the_files_own_brand_is_caught(tmp_path):
    """
    The real shape: half the gradient comes from the token, the other end was
    eyeballed. `var(--color-accent)` is fine; `#0f1a45` is the affiliate's navy
    frozen at one particular darkness.
    """
    text = (":root{--color-accent: {{ theme_color | default('#18235C', true) }};}\n"
            ".c{background: linear-gradient(135deg, var(--color-accent) 0%, #0f1a45 100%);}")
    adj = [f for f in lint_text(tmp_path, text) if f.rule == "BRAND-ADJACENT"]
    assert [f.hex_value for f in adj] == ["#0f1a45"]


def test_a_colour_unrelated_to_the_files_brand_is_left_alone(tmp_path):
    """
    Keyed on the file's own declared hue, so an unrelated colour is not swept
    in just for being colourful.
    """
    text = (":root{--color-accent: #18235C;}\n"
            ".c{background:#f59e0b;}")
    adj = [f for f in lint_text(tmp_path, text) if f.rule == "BRAND-ADJACENT"]
    assert adj == []


def test_the_chroma_floor_keeps_off_whites_out(tmp_path):
    """
    `#f2f4f8` has a nominal hue of 220 — the same as the navy above it — and is
    a page background. Hue alone would flag it; chroma is what says it is a
    neutral. Stated as a deliberate under-inclusion, not an oversight.
    """
    text = ":root{--color-accent: #18235C;}\n.c{background:#f2f4f8; border-color:#eef1f7;}"
    assert [f for f in lint_text(tmp_path, text) if f.rule == "BRAND-ADJACENT"] == []


def test_a_file_with_no_brand_role_has_no_reference_point(tmp_path):
    """
    The other stated limitation: BRAND-ADJACENT measures against hues the file
    declares, so a file declaring none finds nothing. Pinned so it is a known
    gap rather than a surprise, and so BRAND-ROLE is understood to be the rule
    that carries the acceptance criterion.
    """
    assert [f for f in lint_text(tmp_path, ".c{color:#0d9488;}")
            if f.rule == "BRAND-ADJACENT"] == []


# ---------------------------------------------------------------------------
# Suppression
# ---------------------------------------------------------------------------

def test_a_suppression_with_a_reason_silences_the_line(tmp_path):
    text = ":root{--primary-color: #0d9488;} /* lint-allow-hex: print fallback, see D-0XX */"
    assert lint_text(tmp_path, text) == []


def test_a_suppression_on_the_line_above_also_works(tmp_path):
    text = "{# lint-allow-hex: the PDF engine cannot resolve custom properties #}\n:root{--primary-color:#0d9488;}"
    assert lint_text(tmp_path, text) == []


def test_a_bare_suppression_is_itself_an_error(tmp_path):
    """
    The reason is the whole value of the mechanism. Without it the rule
    degrades into a comment people paste to make CI quiet.
    """
    found = lint_text(tmp_path, ":root{--primary-color:#0d9488;} /* lint-allow-hex */")
    # Both: the suppression is reported AND it does not suppress. A bare marker
    # that silenced the line while being flagged would still have silenced it.
    assert {f.rule for f in found} == {"BRAND-ROLE", "BARE-SUPPRESSION"}


# ---------------------------------------------------------------------------
# The baseline ratchet
# ---------------------------------------------------------------------------

def test_the_baseline_matches_the_repository_exactly_today():
    """
    Generated from a real run, so it is a record and not a wish. If this fails,
    either a template changed (retire the line) or the rule changed (regenerate
    and read the diff).
    """
    findings = lint.run(lint.TEMPLATE_ROOTS)
    new = lint.check_baseline(findings, lint.read_baseline())
    assert not new, f"findings not in the baseline: {sorted(new)[:5]}"


def test_the_baseline_is_not_empty():
    """
    An empty baseline plus a working ratchet looks identical to a broken rule
    plus a working ratchet. There are 98 today; this fails when the migration
    is finished, and deleting it then is the right response.

    111 -> 98 on 2026-09-29 (D-112). The market templates' fallback palette was
    a shade of one affiliate's teal in thirteen places; replacing it with the
    platform default retired all thirteen. The replacements are annotated
    `lint-allow-hex` rather than baselined, because a platform default IS a
    brand literal and pretending otherwise is what the annotation is for.

    98 -> 70 on 2026-10-05 (the theme cut). 28 entries named the four
    classic and teal template files, which are deleted. This is the one kind
    of shrink that is NOT progress on the rule — the violations went away
    with the files, not because anyone fixed a colour — so it is recorded
    separately rather than read as 28 fixes.

    70 -> 65 on 2026-10-21, and it is the SAME non-progress as the line above.
    The five entries named `atlas/atlas_report.jinja2`, whose literals went with
    the 1,290 lines that file lost when atlas moved onto `_v2/report.jinja2`
    (#146, 2026-10-06). **They had been stale for fifteen days**: the lint reports
    retirements only alongside a `--write-baseline`, and nothing had run one, so
    `--check-baseline` stayed green while five of its 70 rows described a file
    that no longer contained them. Retired here because D-205's cover fix forced
    a regeneration and `--write-baseline` cannot retire one file's rows and not
    another's.

    D-205's own fix added nothing: linen's white `--burgundy-on-dark` fallback is
    annotated in the template rather than baselined, because white as the fallback
    for text on dark is not a brand value.
    """
    n = sum(lint.read_baseline().values())
    assert n > 0, "nothing baselined — has the rule stopped matching?"
    assert n == 65, (
        f"the baseline holds {n} entries, not the 65 left after the atlas rows "
        f"were retired on 2026-10-21. Fewer is progress: update this number. "
        f"More is a new violation that was baselined instead of fixed."
    )


def test_every_baselined_path_still_exists():
    """A stale entry silently tolerates a violation in a file that came back."""
    missing = sorted({k.split("\t")[0] for k in lint.read_baseline()
                      if not (REPO / k.split("\t")[0]).exists()})
    assert not missing, f"baseline names files that are gone: {missing}"


def test_a_new_violation_fails_the_check(tmp_path):
    """
    THE RATCHET ITSELF. The baseline tolerates what is there; it must not
    tolerate one more of the same thing in the same file.
    """
    baseline = lint.read_baseline()
    key = "apps/web/templates/trendy-inventory.html\tBRAND-ROLE\t#7c3aed"
    assert baseline[key] == 1, "fixture assumption changed; pick another baselined key"

    real = lint.run(lint.TEMPLATE_ROOTS)
    assert not lint.check_baseline(real, baseline)

    extra = lint.Finding("apps/web/templates/trendy-inventory.html", 999,
                         "BRAND-ROLE", "#7c3aed", "--pct-blue: #7C3AED;")
    assert lint.check_baseline(real + [extra], baseline) == {key: 1}


def test_the_cli_exits_nonzero_on_a_new_violation(tmp_path):
    """
    End to end through the process boundary, because CI runs the script and not
    the functions — and an exit code is the only part of this CI can see.
    """
    dirty = tmp_path / "new.jinja2"
    dirty.write_text(DIRTY)
    r = subprocess.run([sys.executable, str(REPO / "scripts/lint_template_colors.py"),
                        "--check-baseline", str(dirty)],
                       capture_output=True, text=True)
    assert r.returncode == 1, r.stdout
    assert "NEW" in r.stdout

    clean = tmp_path / "ok.jinja2"
    clean.write_text(CLEAN)
    r = subprocess.run([sys.executable, str(REPO / "scripts/lint_template_colors.py"),
                        "--check-baseline", str(clean)],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stdout


# ── THE OTHER DIRECTION — a baseline row the templates no longer produce ───────
#
# `--check-baseline` validated the rows the baseline HAD and could not see a row
# whose source stopped containing it. Five rows naming `atlas/atlas_report.jinja2`
# sat here for FIFTEEN DAYS after that file lost 1,290 lines moving onto
# `_v2/report.jinja2`; the command reported green throughout, and they surfaced
# only because D-205's cover fix forced a `--write-baseline`.
#
# A ratchet that only counts upward is half a ratchet. `test_pdf_contrast.py` has
# had both directions since D-153 and says in its docstring why they must share a
# predicate; this is the lint catching up to it.


def test_a_retired_violation_also_fails_the_check():
    """A row with no finding behind it is reported, not tolerated.

    The mirror of `test_a_new_violation_fails_the_check`, and it uses the same
    function on the same inputs in the opposite direction so the two cannot
    drift apart.
    """
    real = lint.run(lint.TEMPLATE_ROOTS)
    baseline = lint.read_baseline()
    assert not lint.stale_baseline(real, baseline), (
        "the live baseline already has stale rows — fix those before reading "
        "this test's result as evidence about the mechanism"
    )

    gone = "apps/worker/src/worker/templates/property/atlas/atlas_report.jinja2\tBRAND-ROLE\t#15216e"
    assert gone not in baseline, (
        "fixture assumption changed: this key was retired on 2026-10-21 and is "
        "used here precisely because nothing produces it any more"
    )
    with_ghost = lint.Counter(baseline)
    with_ghost[gone] = 1
    assert lint.stale_baseline(real, with_ghost) == {gone: 1}


def test_the_two_directions_are_symmetric_on_the_same_input():
    """One predicate, two directions. Written as a property rather than as two
    expectations, because the way a forward and a reverse check drift is that
    somebody edits one of them."""
    real = lint.run(lint.TEMPLATE_ROOTS)
    # A baseline that over-tolerates EVERY finding has stale rows and no new
    # ones. Inflating one key would leave every other finding unbaselined, which
    # is the new direction and not the one under test.
    generous = lint.Counter({f.key: 99 for f in real})
    assert lint.stale_baseline(real, generous)
    assert not lint.check_baseline(real, generous)
    # An empty baseline has new rows and no stale ones.
    assert lint.check_baseline(real, lint.Counter())
    assert not lint.stale_baseline(real, lint.Counter())


def test_the_check_returns_nonzero_on_a_stale_row(tmp_path, monkeypatch, capsys):
    """The exit code, which is the only part of this CI can see.

    Through `main()` with a substituted baseline rather than through
    `subprocess`, and the reason is the flaw this test found in its own first
    version: the reverse direction is only asked on a FULL scan, so a test that
    pointed the CLI at one temp file was exercising the partial path and
    passing for the wrong reason. A full scan needs the real roots, and making
    one of its rows stale needs a different baseline — so the baseline is what
    gets substituted.

    The process boundary is still covered for the forward direction by
    `test_the_cli_exits_nonzero_on_a_new_violation`.
    """
    ghost = tmp_path / "baseline.txt"
    real = lint.run(lint.TEMPLATE_ROOTS)
    rows = sorted(f.key for f in real)
    ghost.write_text(
        "# fixture: every real row, plus one nothing produces\n"
        + "\n".join(rows)
        + "\napps/worker/src/worker/templates/property/atlas/atlas_report.jinja2"
          "\tBRAND-ROLE\t#15216e\n")
    monkeypatch.setattr(lint, "BASELINE_PATH", ghost)

    rc = lint.main(["--check-baseline"])
    out = capsys.readouterr().out
    assert rc == 1, f"exited {rc} with a stale row present\n{out}"
    assert "STALE" in out and "#15216e" in out, f"stale row not named\n{out}"
    assert "0 new" in out, f"the forward direction should be clean here\n{out}"


def test_a_partial_scan_says_it_did_not_check_the_reverse_direction(tmp_path, capsys):
    """Scope is part of a claim.

    `--check-baseline <path>` cannot speak to retirement, because every row it
    did not cover would look retired. It must not quietly report `0 stale`,
    which would read as "asked and found nothing".
    """
    clean = tmp_path / "clean.jinja2"
    clean.write_text("<style>.x{color:var(--primary);}</style>")
    rc = lint.main(["--check-baseline", str(clean)])
    out = capsys.readouterr().out
    assert rc == 0, f"a clean partial scan should pass\n{out}"
    assert "stale NOT CHECKED (partial scan)" in out, out
