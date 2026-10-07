"""
The numbers in `docs/THEME_RENAME_SCOPE.md`, recomputed.

WHY THIS EXISTS
---------------
The document answers a question Jerry has not decided yet — whether to rename
the themes once Design's packages are wired — and its whole value is that the
numbers in it are measured rather than estimated. A scoping document whose
numbers have gone stale is worse than none, because the decision gets taken
against them.

This is the same gate as `apps/worker/tests/test_handover_numbers_are_current.py`,
for the same reason: **the first version of a count in this repository was
15,628, from a `wc -l` whose glob listed one file twice, and it reached two
defect entries, a pull request and a handover before anything recomputed it.**
§0.6's first rule — a number in a tool's output is a property of the tool until
you check it.

The derivation lives in `scripts/derive_theme_name_scope.py`. This module runs
it and asserts the document agrees. If the cut's successor changes any of
these, this fails and the document has to be rewritten rather than quietly
becoming wrong.
"""
import importlib.util
import io
import json
import re
import sys
from contextlib import redirect_stdout
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
DOC = REPO / "docs/THEME_RENAME_SCOPE.md"
DERIVE = REPO / "scripts/derive_theme_name_scope.py"


@pytest.fixture(scope="module")
def derived():
    """Run the derivation in-process and take its JSON."""
    spec = importlib.util.spec_from_file_location("_derive_theme_name_scope", DERIVE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = module.main()
    assert rc == 0, "the derivation script failed"
    return json.loads(buf.getvalue())


@pytest.fixture(scope="module")
def text():
    return DOC.read_text(encoding="utf-8")


def test_the_name_occurrence_total_and_file_count_match(derived, text):
    total, files = derived["name_in_code_total"], derived["name_in_code_files"]
    assert f"**{total} name occurrences across {files} files**" in text, (
        f"the derivation finds {total} occurrences across {files} files; the "
        f"document states something else"
    )


def test_the_group_table_adds_up_to_that_total(derived, text):
    """The table is the argument. A table that does not sum to the headline is
    a table somebody edited one row of."""
    rows = re.findall(r"^\| \*\*[^|]+\|\s*(\d+)\s*\|\s*(\d+)\s*\|", text, re.M)
    assert len(rows) >= 7, f"found {len(rows)} grouped rows, expected at least 7"
    files = sum(int(f) for f, _ in rows)
    occurrences = sum(int(o) for _, o in rows)
    assert occurrences == derived["name_in_code_total"], (
        f"the group table sums to {occurrences} occurrences; the derivation "
        f"finds {derived['name_in_code_total']}"
    )
    assert files == derived["name_in_code_files"], (
        f"the group table sums to {files} files; the derivation finds "
        f"{derived['name_in_code_files']}"
    )


def test_the_baseline_row_counts_match(derived, text):
    base = derived["contrast_baseline"]
    lint = derived["color_lint_baseline_lines_naming_a_theme_path"]
    assert f"{base['entries']} entries" in text
    for theme, n in base["by_theme"].items():
        if n:
            assert f"{theme} {n}" in text, f"{theme}'s {n} baseline entries are not stated"
    assert f"{lint} lines naming a `property/<theme>/` path" in text
    assert f"**{base['entries'] + lint} baseline rows**" in text, (
        f"the document should state {base['entries'] + lint} theme-keyed rows "
        f"({base['entries']} contrast + {lint} colour-lint)"
    )
    live_rows = sum(base["by_theme"][t] for t in derived["live"])
    assert f"carry {live_rows} between them" in text, (
        f"the three live themes carry {live_rows} contrast entries"
    )


def test_the_self_reference_count_inside_a_template_matches(derived, text):
    """TWO NUMBERS NOW, one per architecture, and that is the finding.

    Every theme named itself 9 times while all of them were self-contained.
    bold's chain names it 3 — its entry file's own commentary, with the
    `<title>` moved into the shared file and built from the context. So the
    one-number assertion this replaces was correct until the moment a theme
    migrated, and it failed with "the live templates no longer agree", which
    is true and is the thing worth saying.
    """
    inside = derived["inside_live_templates"]
    self_contained = {k: v["self_references"] for k, v in inside.items()
                      if v["files"] == 1}
    shared = {k: v["self_references"] for k, v in inside.items()
              if v["files"] > 1}

    if self_contained:
        counts = set(self_contained.values())
        assert len(counts) == 1, (
            f"the self-contained templates disagree on how often they name "
            f"themselves: {self_contained}"
        )
        n = counts.pop()
        assert f"**{n} times**" in text, (
            f"a self-contained theme names itself {n} times; the document "
            f"states something else"
        )
    if shared:
        counts = set(shared.values())
        assert len(counts) == 1, f"the shared-architecture themes disagree: {shared}"
        n = counts.pop()
        assert f"names itself {n} times" in text, (
            f"a theme on the shared architecture names itself {n} times; the "
            f"document states something else"
        )
    assert all(v["title_tag"] for v in inside.values()), (
        f"a theme's chain has no <title> at all: {inside}"
    )
    custom = {v["css_custom_properties"] for v in derived["inside_live_templates"].values()}
    assert custom == {0}, (
        f"a live template has gained theme-named CSS custom properties "
        f"({derived['inside_live_templates']}) — that is the thing §2 says makes "
        f"a rename a sweep, and the document says there are none"
    )


def test_the_live_and_retired_sets_are_the_ones_the_document_names(derived, text):
    for name in derived["live"]:
        assert name in text, f"{name} is live and the document does not name it"
    for name in derived["retired"]:
        assert name in text, f"{name} is retired and the document does not name it"
    assert "modern, elegant, bold" in text or "bold, elegant, modern" in text


def test_the_document_still_names_the_one_thing_that_makes_it_cheap(text):
    """D-164. If `theme_id` ever gains a consumer, §3's answer changes from
    "nothing" to "a data migration" — and the document would be wrong in the
    direction that matters."""
    assert "D-164" in text
    assert "read by nothing" in text.lower()


# ─── THE ACCRUAL RATCHET ──────────────────────────────────────────────────────
#
# Jerry, 2026-10-06: defer the rename until the three designs are rendered and
# comparable. The scope document says that is affordable. **The risk of
# deferring is not that the answer changes — it is that new call sites accrue
# quietly while the templates land**, so that the decision taken in three weeks
# is taken against a number measured today.
#
# So it is a ratchet. The count may SHRINK freely. It may grow only by editing
# the number below, which puts the growth in a diff next to the file that
# caused it. That is the whole mechanism: adding a call site is allowed, adding
# one silently is not.
#
# Measured 2026-10-06. 16/82 at the theme cut; 16/85 once bold moved to the
# shared architecture — one new occurrence in `property_builder`'s migration
# seam and two in the single-source gate. The ratchet refused the change until
# this number was edited, which is what it is for.
MAX_FILES_NAMING_A_THEME = 15
MAX_NAME_OCCURRENCES = 73


def test_the_number_of_places_naming_a_theme_has_not_grown(derived):
    """A rename's cost is this number. It may fall; it may not drift up."""
    files = derived["name_in_code_files"]
    occurrences = derived["name_in_code_total"]
    assert files <= MAX_FILES_NAMING_A_THEME, (
        f"{files} files name a theme, against the {MAX_FILES_NAMING_A_THEME} "
        f"measured when the rename was deferred. Each one is a site a rename "
        f"has to visit. Raise MAX_FILES_NAMING_A_THEME deliberately and say "
        f"which file was added — or derive the name from the registry instead, "
        f"which is what the other fifteen do.\n"
        f"Current: {chr(10).join(f'  {n:3d}  {f}' for f, n in derived['name_in_code'].items())}"
    )
    assert occurrences <= MAX_NAME_OCCURRENCES, (
        f"{occurrences} theme-name occurrences, against "
        f"{MAX_NAME_OCCURRENCES} when the rename was deferred"
    )


def test_a_shrink_is_recorded_rather_than_tolerated(derived):
    """The other half of a ratchet, and the half that usually rots.

    A ratchet nobody tightens stops constraining anything — the same reason
    `pdf_contrast_baseline.txt` and `template_color_baseline.txt` both carry a
    staleness test. If the count has fallen, the two constants above are stale
    and the rename just got cheaper than the document claims.
    """
    files = derived["name_in_code_files"]
    assert files == MAX_FILES_NAMING_A_THEME, (
        f"{files} files name a theme, fewer than the "
        f"{MAX_FILES_NAMING_A_THEME} recorded. That is progress: tighten the "
        f"constant and update docs/THEME_RENAME_SCOPE.md, so the decision is "
        f"taken against what is true now."
    )


def test_no_live_template_has_gained_a_theme_named_css_variable(derived):
    """The one thing that would make a rename expensive rather than cheap.

    `teal_report.jinja2` carried 39 `--teal-*` custom properties; renaming THAT
    theme would have been a sweep through its own stylesheet. The three
    survivors have none, and §2 of the scope document rests on it. Design's
    rewrite is the moment this could change, which is exactly when the estimate
    would quietly stop being true.
    """
    offenders = {
        name: v["css_custom_properties"]
        for name, v in derived["inside_live_templates"].items()
        if v["css_custom_properties"]
    }
    assert not offenders, (
        f"{offenders} — a live template now names a CSS custom property after "
        f"its own theme. A rename is no longer four edits and three file moves; "
        f"re-derive docs/THEME_RENAME_SCOPE.md §2 before anyone takes the "
        f"decision against it."
    )
