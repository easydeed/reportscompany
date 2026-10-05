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
    counts = {v["self_references"] for v in derived["inside_live_templates"].values()}
    assert len(counts) == 1, (
        f"the live templates no longer agree on how often they name themselves: "
        f"{derived['inside_live_templates']} — the document states one number"
    )
    n = counts.pop()
    assert f"**{n} times**" in text, f"each theme names itself {n} times"
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
