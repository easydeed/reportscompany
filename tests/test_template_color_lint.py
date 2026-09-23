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
    plus a working ratchet. There are 111 today; this fails when the migration
    is finished, and deleting it then is the right response.
    """
    n = sum(lint.read_baseline().values())
    assert n > 0, "nothing baselined — has the rule stopped matching?"
    assert n == 111, (
        f"the baseline holds {n} entries, not the 111 measured against main on "
        f"2026-09-23. Fewer is progress: update this number. More is a new "
        f"violation that was baselined instead of fixed."
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
