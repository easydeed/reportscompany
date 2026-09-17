"""
A multi-value query parameter must be a list, not a comma-separated string.

THE DEFECT (D-076)
------------------
SimplyRETS takes several statuses as repeated parameters. Given a comma string
it returns **HTTP 200 and silently discards everything after the first value**.
Measured against api.simplyrets.com:

    status=Active                              42 rows   {Active: 42}
    status=Closed                              13 rows   {Closed: 13}
    status=Active,Closed                       42 rows   {Active: 42}   <-- !
    status=Active&status=Closed                55 rows   {Active, Closed}
    status=Active&status=Pending&status=Closed 78 rows   all three

No error. No warning. A smaller answer than the one asked for.

WHY THAT PARTICULAR SILENCE MATTERS HERE
----------------------------------------
Every caller of a multi-status query is computing something *across* statuses —
a ratio, a split, a rate. Drop the second status and the denominator is zero,
and nothing anywhere says so. `calc.py:snapshot_metrics` splits rows by status
and computes `moi = active/closed`; with an empty closed bucket it returns the
sentinel 999.0. That is D-056's failure arriving through the transport layer
instead of the query builder.

WHAT IS ASSERTED, AND WHAT IS NOT
---------------------------------
These tests do not call SimplyRETS. They assert the thing this repo controls:
that the parameters it *builds* encode to the repeated form. The encoding was
checked end to end once, by hand, through the same httpx the vendor module
uses — a list produces `status=Active&status=Pending&status=Closed`, a string
produces `status=Active%2CPending%2CClosed`. It is the second of those that the
live API answered with one status.
"""
import ast
import re
from pathlib import Path

import pytest


VENDORS = Path(__file__).resolve().parents[1] / "src" / "worker" / "vendors"
QUERY_BUILDERS = Path(__file__).resolve().parents[1] / "src" / "worker" / "query_builders.py"
SIMPLYRETS = (VENDORS / "simplyrets.py").read_text()

# Statuses this API understands. A value containing a comma AND one of these is
# a multi-value parameter written the broken way.
STATUSES = ("Active", "Pending", "Closed", "ActiveUnderContract")

# Query parameters SimplyRETS accepts more than one of. A comma-packed value
# under any of these is the defect; the same text in a comment is not.
MULTI_VALUE_KEYS = ("status", "type", "subtype", "cities", "postalCodes", "agent", "brokers")

SEARCHED = [
    VENDORS / "simplyrets.py",
    QUERY_BUILDERS,
    Path(__file__).resolve().parents[1] / "src" / "worker" / "compute" / "market_trends.py",
]


def _multi_value_param_values(path):
    """
    Every value assigned to a known multi-value query key, structurally.

    NOT "every string literal containing a comma and two statuses", which is
    what this was first written as — and which matched the prose in this very
    module's own comments explaining the bug, plus the narrative comments in
    market_trends.py. Three files "failing" on their own documentation.

    The construct is a *parameter value*, so the search has to be over dict
    values under the parameter's key, not over text that mentions it.
    """
    tree = ast.parse(path.read_text())
    out = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Dict):
            continue
        for k, v in zip(node.keys, node.values):
            if isinstance(k, ast.Constant) and k.value in MULTI_VALUE_KEYS:
                out.append((getattr(v, "lineno", node.lineno), k.value, v))
    return out


# ── the construct, wherever it is (§0.6 rule 4) ─────────────────────────────

@pytest.mark.parametrize("path", SEARCHED, ids=lambda p: p.name)
def test_no_query_parameter_packs_several_values_into_one_string(path):
    """
    Searched by construct — a value under a multi-value parameter key — rather
    than by grepping for the one literal that was wrong. The symptom was
    `'Active,Pending,Closed'`; the construct is any comma-packed value under
    any of those keys.
    """
    offenders = []
    for lineno, key, node in _multi_value_param_values(path):
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and "," in node.value:
            offenders.append(f"{path.name}:{lineno}  {key}={node.value!r}")
    assert not offenders, (
        "comma-packed multi-value parameter(s) — SimplyRETS returns 200 and "
        f"keeps only the first value: {offenders}. Pass a list instead."
    )


def test_the_helper_that_had_it_now_passes_a_list():
    """
    Forbidding the old form is not enough: deleting the parameter entirely
    would also pass, and would quietly change what the helper asks for.
    """
    src = SIMPLYRETS
    fn = [
        n for n in ast.walk(ast.parse(src))
        if isinstance(n, ast.FunctionDef) and n.name == "build_market_snapshot_params"
    ]
    assert len(fn) == 1
    returned = [n for n in ast.walk(fn[0]) if isinstance(n, ast.Dict)]
    assert returned, "build_market_snapshot_params no longer returns a dict literal"

    status_values = [
        v for d in returned
        for k, v in zip(d.keys, d.values)
        if isinstance(k, ast.Constant) and k.value == "status"
    ]
    assert len(status_values) == 1, f"expected one status key, found {len(status_values)}"
    node = status_values[0]
    assert isinstance(node, (ast.List, ast.Tuple)), (
        f"status is {ast.unparse(node)}, which httpx encodes as a single "
        f"parameter; SimplyRETS would keep only the first value"
    )
    values = {c.value for c in node.elts if isinstance(c, ast.Constant)}
    assert values == {"Active", "Pending", "Closed"}, (
        f"the helper now asks for {sorted(values)} — it asked for all three "
        f"before, and narrowing it silently changes every caller's metrics"
    )


# ── the documented idiom, which is what gets copied ─────────────────────────

def test_the_docstring_does_not_teach_the_broken_form():
    """
    The comma form was in `fetch_properties`'s docstring as the worked example.
    That is how it would have reached the next multi-status query — this one.
    A test on the code alone would not have covered the thing being copied.
    """
    tree = ast.parse(SIMPLYRETS)
    docs = [
        ast.get_docstring(n) or ""
        for n in ast.walk(tree)
        if isinstance(n, (ast.FunctionDef, ast.Module, ast.ClassDef))
    ]
    for doc in docs:
        for line in doc.splitlines():
            # An example line, not the explanation of why it is wrong.
            if "->" in line or "does not work" in line or "NOT" in line:
                continue
            packed = re.findall(r"""['"]([A-Za-z]+(?:,[A-Za-z]+)+)['"]""", line)
            offenders = [p for p in packed if sum(s in p for s in STATUSES) >= 2]
            assert not offenders, (
                f"a docstring still shows the comma form as an example: {line.strip()!r}"
            )


def test_the_reason_is_recorded_where_someone_would_look():
    """
    A fix with no explanation gets reverted by the next person who finds the
    comma form more readable. The measurement belongs beside the code.
    """
    assert "status=Active%2CClosed" in SIMPLYRETS or "status=Active,Closed" in SIMPLYRETS, (
        "the vendor module no longer records what the comma form actually did"
    )
    assert "D-076" in SIMPLYRETS, "no pointer back to the defect entry"
