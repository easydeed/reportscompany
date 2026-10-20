"""The plan's display name comes from the `plans` row, not from Python.

D-203. `services/usage.py` carried `_PLAN_DISPLAY_NAMES`, a slug -> name
literal consulted BEFORE the `plans.plan_name` the same function already
selected. It disagreed with the table on four of eight rows, so an account on
`team` was told "PRO PLAN" in the sidebar — `app-layout.tsx` renders
`{plan.plan_name} Plan` under `uppercase` — and one on `solo` was told
"Starter".

This is D-093 one column over: there, an account with no plan row got a
hard-coded `100` while the table said `3`, and the answer was to resolve from
the row at runtime with no literal anywhere.

WHAT IS DERIVED AND WHAT IS WRITTEN DOWN
----------------------------------------
The slugs and display names this file reasons about are PARSED OUT OF THE
MIGRATIONS, not typed here. A test that hard-codes `{"team": "Team"}` to prove
the code does not hard-code `{"team": "Pro"}` has moved the literal, not
removed it — and would drift the same way the map did.

THE SCAN IS STRUCTURAL, NOT TEXTUAL
-----------------------------------
Everything below reads the parsed AST. The fix writes a comment block that
names the deleted map, quotes "PRO PLAN", and lists the four rows that
disagreed; a text scan would be measuring that explanation. Eight
substring-is-not-a-construct defects have been filed in this repository in six
days, three of them in tests written against this exact family (§0.6), so
comments are not stripped here — they are never read.
"""
import ast
import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
API = REPO / "apps/api/src/api"
SERVICE = API / "services/usage.py"
MIGRATIONS = REPO / "db/migrations"


# ─── WHAT THE TABLE SAYS ──────────────────────────────────────────────────────

def _plan_inserts() -> list[str]:
    """Every `INSERT INTO plans ...;` statement in the migrations."""
    out = []
    for f in sorted(MIGRATIONS.glob("*.sql")):
        out += re.findall(r"INSERT INTO plans\b.*?;", f.read_text(encoding="utf-8"),
                          re.S | re.I)
    return out


def _slugs_and_names() -> tuple[set[str], set[str]]:
    """({slug}, {display name}) as the seeds write them.

    Slugs are the lowercase-and-underscore literals; display names are the
    capitalised word sequences. Stripe price ids carry digits and descriptions
    carry punctuation, so neither falls in either bucket.
    """
    slugs, names = set(), set()
    for stmt in _plan_inserts():
        for lit in re.findall(r"'([^']*)'", stmt):
            if re.fullmatch(r"[a-z][a-z_]*", lit):
                slugs.add(lit)
            elif re.fullmatch(r"[A-Z][A-Za-z]*(?: [A-Z][A-Za-z]*)*", lit):
                names.add(lit)
    return slugs, names


SLUGS, NAMES = _slugs_and_names()


def test_the_migrations_are_still_parseable_as_plan_seeds():
    """The guard. Empty sets make every assertion below vacuous, and the
    parser is a regex over SQL someone else is free to reformat."""
    assert len(_plan_inserts()) >= 3, "no plan seed statements found in db/migrations"
    assert len(SLUGS) >= 5, f"only parsed slugs {sorted(SLUGS)} out of the seeds"
    assert len(NAMES) >= 5, f"only parsed names {sorted(NAMES)} out of the seeds"


def test_the_plans_table_owns_a_display_name_column():
    """The ticket's precondition: if `plans` had no display-name column one
    had to be added. It has `plan_name`, and 0013 documents it as the name
    shown in the UI — which is why the Python map was drift and not a
    second source of truth."""
    sql = "\n".join(f.read_text(encoding="utf-8") for f in sorted(MIGRATIONS.glob("*.sql")))
    assert re.search(r"\bplan_name\b", sql), (
        "db/migrations no longer defines plans.plan_name. The display name has "
        "to live in the table — if the column is gone, add it back rather than "
        "resolving the name in a service (D-203)."
    )


# ─── WHAT THE CODE DOES ───────────────────────────────────────────────────────

def _tree(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def _api_modules():
    for f in sorted(API.rglob("*.py")):
        yield f, _tree(f)


def test_the_service_still_reads_plan_name_off_the_row():
    """The other guard. `display_name = plan_name` is only correct because
    `plan_name` is selected from the `plans` row this account points at. If
    that SELECT loses the column the assignment starts resolving to None and
    the sidebar goes blank, which is a different defect wearing this fix."""
    body = SERVICE.read_text(encoding="utf-8")
    assert re.search(r"p\.plan_name", body), (
        "services/usage.py no longer selects p.plan_name from plans, so there "
        "is no row value for the display name to come from (D-203)"
    )


def test_the_display_name_is_assigned_with_no_string_literal():
    """The fix itself. `display_name` is the row value or the slug — both
    names, no constants. `... or "Free"` is what made an account on an
    unknown slug claim a plan it was not on."""
    found = []
    for node in ast.walk(_tree(SERVICE)):
        if isinstance(node, ast.Assign):
            targets = [t.id for t in node.targets if isinstance(t, ast.Name)]
            if "display_name" not in targets:
                continue
            found.append(node)
            literals = [n.value for n in ast.walk(node.value)
                        if isinstance(n, ast.Constant) and isinstance(n.value, str)]
            assert not literals, (
                f"display_name is assigned from a string literal {literals!r} at "
                f"services/usage.py:{node.lineno}. An unknown slug shows the "
                f"slug, or nothing — not a guess (D-203)."
            )
    assert found, (
        "no `display_name = ...` assignment in services/usage.py. If the name "
        "is now resolved somewhere else, point this test at it rather than "
        "deleting it (D-203)."
    )


def test_no_module_maps_plan_slugs_to_display_names():
    """The map, under any name, anywhere in the API.

    Keyed on the SHAPE — a dict literal whose keys are plan slugs and whose
    values look like names — so renaming `_PLAN_DISPLAY_NAMES` does not evade
    it. "Look like names" is letters and spaces only, which keeps the
    slug -> Stripe-price-id dicts this codebase legitimately has (`price_1SO4…`
    carries digits and underscores) and the slug -> limit dicts (ints) out of
    it. WHAT IT WOULD STILL CATCH is a slug -> single-word-string dict that is
    not a display name at all; there is none today, and if one arrives the
    right move is to narrow this to the names the migrations write rather than
    to widen the exemption.
    """
    WORDS_ONLY = re.compile(r"[A-Za-z][A-Za-z ]*$")
    for path, tree in _api_modules():
        for node in ast.walk(tree):
            if not isinstance(node, ast.Dict):
                continue
            pairs = [
                (k.value, v.value)
                for k, v in zip(node.keys, node.values)
                if isinstance(k, ast.Constant) and isinstance(k.value, str)
                and isinstance(v, ast.Constant) and isinstance(v.value, str)
            ]
            slug_keyed = [(k, v) for k, v in pairs
                          if k in SLUGS and WORDS_ONLY.fullmatch(v)]
            assert len(slug_keyed) < 2, (
                f"{path.relative_to(REPO).as_posix()}:{node.lineno} maps plan "
                f"slugs to strings: {slug_keyed!r}. The display name lives in "
                f"plans.plan_name; a literal here is the thing that drifted on "
                f"four of eight rows (D-203). If two plans should share a name, "
                f"that is a value in the table."
            )


@pytest.mark.parametrize("name", sorted(NAMES))
def test_the_service_quotes_no_plan_display_name(name):
    """And not in a non-dict shape either — an `if slug == "team": "Pro"`
    chain is the same defect with different syntax.

    Docstrings are excluded because this file's own explanation is one, and
    `#` comments were never in the AST. The value asserted is the one the
    migrations write, so a name added to the table arrives here on its own.
    """
    tree = _tree(SERVICE)
    docstrings = {
        id(n.body[0].value)
        for n in ast.walk(tree)
        if isinstance(n, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
        and n.body and isinstance(n.body[0], ast.Expr)
        and isinstance(n.body[0].value, ast.Constant)
        and isinstance(n.body[0].value.value, str)
    }
    hits = [
        n.lineno for n in ast.walk(tree)
        if isinstance(n, ast.Constant) and isinstance(n.value, str)
        and n.value == name and id(n) not in docstrings
    ]
    assert not hits, (
        f"services/usage.py quotes the display name {name!r} at line(s) {hits}. "
        f"That string belongs in plans.plan_name, where the admin panel can see "
        f"it and this service cannot disagree with it (D-203)."
    )
