"""
D-155 — the lead page collects a name and used the assessor roll's instead.

`payload.name or payload.owner_name` wrote the person who OWNS the house into
the CRM as the person who ASKED about it — a different human whenever the
requester is a neighbour, a buyer, or another agent. Same defect as the
report's owner block (D-116), in the customer record, and the source of the
two delivery-side defects: the worker had no requester name to use because
this route never sent one.

AST, NOT A SUBSTRING. Both assertions match the CONSTRUCT — a `BoolOp` whose
branches are `payload.name` and `payload.owner_name`, and a dict key — rather
than text that contains it. §0.6: the tell is that a text needle would still
match if the surrounding characters were anything at all, and this file's
whole subject is two names that look alike.
"""
import ast
from pathlib import Path

import pytest

ROUTE = Path(__file__).resolve().parents[1] / "src/api/routes/lead_pages.py"
TREE = ast.parse(ROUTE.read_text(encoding="utf-8"))


def _attr(node):
    """`payload.name` for an attribute chain, else None."""
    if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
        return f"{node.value.id}.{node.attr}"
    return None


def test_the_lead_record_does_not_fall_back_to_the_owner():
    offenders = []
    for node in ast.walk(TREE):
        if not (isinstance(node, ast.BoolOp) and isinstance(node.op, ast.Or)):
            continue
        names = {_attr(v) for v in node.values}
        if "payload.name" in names and "payload.owner_name" in names:
            offenders.append(node.lineno)
    assert not offenders, (
        f"lead_pages.py:{offenders} falls back from the requester's name to "
        f"the assessor roll. A form that collects a name uses it or nothing — "
        f"the fallback records a third party as the lead."
    )


def test_the_requester_name_is_forwarded_to_the_worker():
    """The other half: killing the fallback is only useful if the name it
    should have used actually reaches the report.

    `property_data` is stored as jsonb on `consumer_reports` and read back by
    the worker, so a key absent here is a key the greeting cannot use — which
    is exactly why the greeting used `owner_name`.
    """
    keys = set()
    for node in ast.walk(TREE):
        if isinstance(node, ast.Dict):
            keys |= {k.value for k in node.keys
                     if isinstance(k, ast.Constant) and isinstance(k.value, str)}
    assert "requester_name" in keys, (
        "no dict in lead_pages.py carries `requester_name`, so the worker has "
        "no name for the person who asked and will reach for the owner's"
    )


def test_the_owner_name_is_still_forwarded_because_the_agent_path_uses_it():
    """The inverse, so this file does not read as "remove every owner name".

    The agent report shows the owner of record deliberately. What must not
    happen is the CONSUMER path using it as a person's identity — which is
    asserted on the rendered consumer document in the worker's own suite.
    """
    keys = set()
    for node in ast.walk(TREE):
        if isinstance(node, ast.Dict):
            keys |= {k.value for k in node.keys
                     if isinstance(k, ast.Constant) and isinstance(k.value, str)}
    assert "owner_name" in keys
