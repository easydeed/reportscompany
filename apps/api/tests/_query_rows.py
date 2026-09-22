"""
Build a fake cursor row FROM the query it stands in for (D-091).

THE PROBLEM THIS REPLACES
-------------------------
`apps/api/tests` contributed 34 failures and 5 errors, and 29 of them were one
mistake: a `Mock()` cursor handed a tuple somebody typed out by reading the
SELECT, which then fell behind it.

    services/usage.py:90    ValueError: not enough values to unpack
                            (expected 15, got 7)      -> 12 failures
    services/branding.py:60 ValueError: too many values to unpack
                            (expected 3)              -> 11 failures
    routes/auth.py          StopIteration: 2 rows supplied, 3 fetchone calls
                                                      -> 6 failures

Note the two directions. `usage.py` GAINED eight columns when per-product limits
landed; `branding.py` LOST one when the sponsor fallback was removed. A
transcribed tuple is wrong either way and says nothing about which side moved —
the failure surfaces in the production module, at the unpack, which is why these
read like product bugs and are not.

D-089 fixed the same class in the worker's template tests by rendering through
the real builder. There is no builder here: the shape is defined by a SQL string
inside a function. So the double is derived from that string.

HOW IT WORKS, AND WHAT IT WILL AND WILL NOT CATCH
-------------------------------------------------
`columns_of(module, function, index)` reads the function's source with
`inspect.getsource`, finds its `index`-th SQL literal, and returns the SELECT
list in order — the alias when there is an `AS`, otherwise the last dotted
segment. `row_for(...)` then builds a tuple of that width, so a test says what it
means by NAME and the arity comes from the query.

**It catches arity and order drift, which is the whole of what broke here.** It
does NOT check that the column names are real, that the types match, or that the
query runs — nothing here touches a database. A test using this still asserts
against a hand-written *value*; what it no longer does is hand-write the SHAPE.

The parse is deliberately narrow, and it RAISES rather than guessing. A query it
cannot read is a loud failure in one place, not a silently wrong tuple in twenty
tests — which is the failure mode this module exists to end.
"""
from __future__ import annotations

import inspect
import re
from typing import Any, Dict, List

# A triple-quoted SQL literal inside a function body.
_SQL_LITERAL = re.compile(r'"""(.*?)"""', re.S)
_SELECT_BLOCK = re.compile(r"\bSELECT\b(.*?)\bFROM\b", re.S | re.I)


def _split_columns(select_body: str) -> List[str]:
    """
    Split a SELECT list on top-level commas — top-level because a column can be
    `COALESCE(a, b) AS x`, and splitting naively on every comma turns one column
    into three.
    """
    out, depth, current = [], 0, ""
    for ch in select_body:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        if ch == "," and depth == 0:
            out.append(current)
            current = ""
        else:
            current += ch
    if current.strip():
        out.append(current)
    return out


def _name_of(column: str) -> str:
    """`p.monthly_report_limit AS plan_limit` -> `plan_limit`; `a.id::text` -> `id`."""
    col = " ".join(column.split())
    m = re.search(r"\bAS\s+([A-Za-z_][A-Za-z0-9_]*)\s*$", col, re.I)
    if m:
        return m.group(1)
    col = re.split(r"::", col)[0].strip()
    col = re.sub(r"\s+IS\s+NOT\s+NULL$", "", col, flags=re.I)
    return col.split(".")[-1].strip()


def columns_of(func, index: int = 0) -> List[str]:
    """
    The SELECT columns of the `index`-th SQL literal in `func`, in order.

    Raises rather than returning a guess. A query this cannot parse must stop
    the test that asked for it, because the alternative — an empty or partial
    column list — produces a tuple of the wrong width and lands us back at the
    unpack error this module exists to remove.
    """
    source = inspect.getsource(func)
    literals = _SQL_LITERAL.findall(source)
    selects = [l for l in literals if _SELECT_BLOCK.search(l)]
    if index >= len(selects):
        raise AssertionError(
            f"{func.__qualname__} has {len(selects)} SELECT literal(s); "
            f"index {index} was requested. The function's queries changed — "
            f"update the caller rather than padding the row."
        )
    body = _SELECT_BLOCK.search(selects[index]).group(1)
    cols = [_name_of(c) for c in _split_columns(body) if c.strip()]
    if not cols:
        raise AssertionError(
            f"could not read any columns out of {func.__qualname__}'s query "
            f"#{index}. Parsing it is this module's job and it failed loudly "
            f"on purpose."
        )
    return cols


def row_for(func, index: int = 0, defaults: Any = None, **values) -> tuple:
    """
    A tuple shaped like one row of `func`'s `index`-th query.

    Name the columns you care about; everything else is `defaults` (None unless
    given). Naming a column the query does not have raises — that is the drift
    detector, and it fires on the TEST, pointing at the name, rather than inside
    the production module at an unpack.
    """
    cols = columns_of(func, index)
    unknown = sorted(set(values) - set(cols))
    if unknown:
        raise AssertionError(
            f"{func.__qualname__} query #{index} has no column(s) {unknown}. "
            f"It selects: {cols}"
        )
    return tuple(values.get(c, defaults) for c in cols)


def row_dict(func, index: int = 0, **values) -> Dict[str, Any]:
    """`row_for` as a dict, for asserting on what a row means rather than where it sits."""
    return dict(zip(columns_of(func, index), row_for(func, index, **values)))
