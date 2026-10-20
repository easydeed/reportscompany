"""Every read of a report's area falls back to the column that always holds it.

D-202. `report_generations.cities text[]` is set when the report is created.
`input_params jsonb` is written by exactly one statement in the codebase —
`apps/worker/src/worker/tasks.py`, when the job starts processing — so a
queued report, or one that failed before processing, has `cities` and no
`input_params`. Six places read the area and three of them had no fallback,
including the one feeding the dashboard, which shows the most recent report
WHATEVER its status.

COMMENTS ARE STRIPPED BEFORE ANYTHING IS SCANNED
------------------------------------------------
The fix writes a `-- D-202: …` note at each site, and those notes talk about
`input_params`. A scan that counted them would be measuring the explanation
rather than the code — which has happened eight times in this repository in a
week, three of them in tests written against exactly that family (§0.6). SQL
`--` lines and Python `#` lines go before the first match is looked for.
"""
import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
API = REPO / "apps/api/src/api"
WORKER = REPO / "apps/worker/src/worker"

#: The read being guarded.
READ = "input_params->>'city'"

#: Each read must be inside a COALESCE that also offers the array column.
GOOD = re.compile(
    r"COALESCE\(\s*input_params->>'city'\s*,\s*(?:rg\.)?cities\[1\]", re.S)
GOOD_QUALIFIED = re.compile(
    r"COALESCE\(\s*rg\.input_params->>'city'\s*,\s*rg\.cities\[1\]", re.S)


def _without_comments(text: str) -> str:
    """Strip SQL `--` and Python `#` line comments.

    Not a parser — but the thing being removed is whole lines, and a line
    beginning with `--` or `#` after optional whitespace cannot be the SQL
    projection this file is about.
    """
    out = []
    for line in text.splitlines():
        stripped = line.lstrip()
        if stripped.startswith("--") or stripped.startswith("#"):
            continue
        out.append(line)
    return "\n".join(out)


def _sites():
    """{path: [line numbers]} for every live read of the area."""
    found = {}
    for f in sorted(API.rglob("*.py")):
        body = _without_comments(f.read_text(encoding="utf-8"))
        hits = [i for i, l in enumerate(body.splitlines(), 1) if READ in l]
        if hits:
            found[f.relative_to(REPO).as_posix()] = (hits, body)
    return found


def test_there_are_sites_to_check():
    """The guard. A scan that finds nothing passes every assertion below."""
    sites = _sites()
    assert len(sites) >= 3, (
        f"only {len(sites)} file(s) read {READ}. If the read was removed "
        f"entirely that is the better fix — delete this file and close D-202."
    )


@pytest.mark.parametrize("path", sorted(_sites()))
def test_every_read_of_the_area_falls_back_to_the_cities_column(path):
    _, body = _sites()[path]
    # Each occurrence, with enough context to see its COALESCE.
    for m in re.finditer(re.escape(READ), body):
        window = body[max(0, m.start() - 120): m.end() + 120]
        assert GOOD.search(window) or GOOD_QUALIFIED.search(window), (
            f"{path}: a read of the report area with no fallback to "
            f"cities[1]. A queued or failed report has no input_params, so "
            f"this returns Unknown or null for it (D-202):\n"
            f"...{window.strip()}..."
        )


def test_input_params_still_has_exactly_one_writer():
    """The premise. If something else starts writing `input_params` at
    creation time, the fallback stops being load-bearing and this entry's
    reasoning needs re-reading rather than its code."""
    # FILES AND A COUNT, NOT LINE NUMBERS. `_without_comments` renumbers
    # everything it strips, so a line pinned here would be a line in a text
    # this test invented. What the entry actually rests on is "one statement,
    # in the worker" — which is what is asserted.
    writers = []
    for root in (API, WORKER):
        for f in sorted(root.rglob("*.py")):
            body = _without_comments(f.read_text(encoding="utf-8"))
            for line in body.splitlines():
                if "input_params" in line and re.search(r"\bSET\b|\bINSERT\b|\bVALUES\b", line):
                    writers.append(f.relative_to(REPO).as_posix())
    assert writers == ["apps/worker/src/worker/tasks.py"], (
        f"the writers of input_params are now {writers}. D-202 rests on there "
        f"being exactly ONE, in the worker, after the job starts — if "
        f"something now writes it at creation the fallback stops being "
        f"load-bearing and the entry needs re-reading, not the code."
    )


def test_the_cities_column_is_what_creation_sets():
    """The other half of the premise, asserted where it is written."""
    body = _without_comments((API / "routes/reports.py").read_text(encoding="utf-8"))
    assert "cities" in body, (
        "routes/reports.py no longer mentions `cities`, so the column the "
        "fallback reads may not be the one creation sets"
    )
