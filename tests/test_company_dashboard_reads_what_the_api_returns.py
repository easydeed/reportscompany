"""Every field the company dashboard reads is one /v1/company/overview returns.

The shape this guards: a page that reads `metrics.leads_this_month` from an
API that never sends it compiles, deploys, renders `undefined` as nothing, and
says so to nobody. Design's sponsor package drew lead counts with no field
behind them; this is the check that would have failed.

Both sides are read from source — the page's `m.<field>` / `r.<field>` /
`o?.company.<field>` reads, and the dict literals `get_overview` returns.
"""
import ast
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PAGE = REPO / "apps/web/app/app/company/page.tsx"
ROUTE = REPO / "apps/api/src/api/routes/company.py"


def _returned_keys():
    tree = ast.parse(ROUTE.read_text(encoding="utf-8"))
    fn = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "get_overview")
    out = {}
    ret = next(n for n in ast.walk(fn) if isinstance(n, ast.Return) and isinstance(n.value, ast.Dict))
    for k, v in zip(ret.value.keys, ret.value.values):
        if isinstance(v, ast.Dict):
            out[k.value] = {kk.value for kk in v.keys if isinstance(kk, ast.Constant)}
    # The rep rows are built by `reps.append({...})` inside the function.
    for call in ast.walk(fn):
        if (isinstance(call, ast.Call) and isinstance(call.func, ast.Attribute)
                and call.func.attr == "append" and getattr(call.func.value, "id", "") == "reps"
                and call.args and isinstance(call.args[0], ast.Dict)):
            out["reps"] = {kk.value for kk in call.args[0].keys if isinstance(kk, ast.Constant)}
    return out


def test_the_page_reads_only_fields_the_api_sends():
    src = PAGE.read_text(encoding="utf-8")
    keys = _returned_keys()
    reads = {
        "metrics": set(re.findall(r"\bm\.([a-z_0-9]+)", src)),
        "reps": set(re.findall(r"\br\.([a-z_0-9]+)", src)),
        "company": set(re.findall(r"o\?\.company\.([a-z_0-9]+)", src)),
    }
    assert reads["metrics"], "the scan found no metric reads; it has stopped measuring"
    missing = {group: sorted(fields - keys.get(group, set())) for group, fields in reads.items()}
    missing = {g: f for g, f in missing.items() if f}
    assert missing == {}, f"the dashboard reads fields /v1/company/overview never returns: {missing}"


def test_the_lead_counts_are_a_read_of_existing_rows():
    """The lead figures select from `leads`; nothing on this route writes one."""
    body = ast.get_source_segment(ROUTE.read_text(encoding="utf-8"), next(
        n for n in ast.walk(ast.parse(ROUTE.read_text(encoding="utf-8")))
        if isinstance(n, ast.FunctionDef) and n.name == "get_overview"))
    assert "FROM leads" in body
    assert not re.search(r"\b(INSERT|UPDATE|DELETE)\b", body), "get_overview must stay read-only"
