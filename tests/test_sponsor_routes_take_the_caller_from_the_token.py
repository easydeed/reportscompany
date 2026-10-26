"""Every sponsor route takes its caller from the token, and checks every id it is handed.

D-005 (August) was one mechanism: `/v1/company/reports` accepted a `rep_id`
from the query string and used it without asking whether that rep was the
caller's. The fix was an ownership check on that one parameter. Nothing stopped
the next route on these routers from doing the same thing with a different
name. This does.

For every route in `company.py` and `affiliates.py`:

  1. the caller comes from exactly one approved token dependency —
     `Depends(get_company_admin)` or `Depends(require_account_id)`; and
  2. every other parameter that names an account (path, query, or a field of
     the request body) is in `ALLOWED`, with a reason, and the route's body
     contains the ownership predicate that bounds it.

A new route that takes `affiliate_id=` from the client, or a route whose
caller parameter loses its `Depends(...)` and so becomes a query parameter,
fails here. `scripts/regressions/sponsor_route_ids.json` adds both, and removes
one ownership predicate, and each goes red.

This is a static read, so it runs in CI, where the database-backed isolation
suites (`apps/api/tests/test_*_tenant_isolation.py`) skip.
"""
import ast
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
ROUTES = REPO / "apps/api/src/api/routes"

CALLER_DEPENDENCIES = {"get_company_admin", "require_account_id"}

#: Client-supplied ids that are allowed, each with why, and the text the route
#: must contain to bound it to the caller.
ALLOWED = {
    ("company.py", "rep_id"): (
        "a filter on the company's own feed; it must be one of this company's reps (D-005)",
        "matched_rep is None",
    ),
    ("affiliates.py", "sponsored_account_id"): (
        "the agent being read or acted on; only one the caller currently sponsors",
        "sponsor_account_id = %s::uuid",
    ),
    ("affiliates.py", "agent_account_id"): (
        "the agent being read; only one the caller currently sponsors",
        "sponsor_account_id = %s::uuid",
    ),
}

NOT_IDS = {"request", "background_tasks", "file", "body", "limit", "offset"}
#: A parameter or body field that names a row: `rep_id`, `affiliate_id`, `account_id`, `id`.
ID_LIKE = re.compile(r"(^|_)id$")


def _routes(path):
    src = path.read_text(encoding="utf-8")
    tree = ast.parse(src)
    models = {
        n.name: [t.target.id for t in n.body if isinstance(t, ast.AnnAssign) and isinstance(t.target, ast.Name)]
        for n in tree.body if isinstance(n, ast.ClassDef)
    }
    for fn in tree.body:
        if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if not any(isinstance(d, ast.Call) and getattr(d.func, "attr", "") in {"get", "post", "put", "patch", "delete"}
                   for d in fn.decorator_list):
            continue
        yield fn, ast.get_source_segment(src, fn), models


def _depends_on(default):
    if isinstance(default, ast.Call) and getattr(default.func, "id", "") == "Depends" and default.args:
        return getattr(default.args[0], "id", None)
    return None


def test_the_scan_finds_the_routers():
    found = {f: sum(1 for _ in _routes(ROUTES / f)) for f in ("company.py", "affiliates.py")}
    assert found["company.py"] >= 10 and found["affiliates.py"] >= 15, found


def test_every_sponsor_route_takes_the_caller_from_the_token_and_bounds_every_id():
    problems = []
    for name in ("company.py", "affiliates.py"):
        for fn, body, models in _routes(ROUTES / name):
            args = fn.args.args
            defaults = [None] * (len(args) - len(fn.args.defaults)) + list(fn.args.defaults)
            callers = [a.arg for a, d in zip(args, defaults) if _depends_on(d) in CALLER_DEPENDENCIES]
            if len(callers) != 1:
                problems.append(f"{name}:{fn.name} has {len(callers)} caller dependencies; needs exactly one of {sorted(CALLER_DEPENDENCIES)}")
            supplied = []
            for a, d in zip(args, defaults):
                if a.arg in callers or a.arg in NOT_IDS or _depends_on(d):
                    if a.arg == "body" and a.annotation is not None:
                        supplied += [f for f in models.get(ast.unparse(a.annotation), []) if ID_LIKE.search(f)]
                    continue
                if ID_LIKE.search(a.arg):
                    supplied.append(a.arg)
            for param in supplied:
                rule = ALLOWED.get((name, param))
                if rule is None:
                    problems.append(f"{name}:{fn.name} takes {param!r} from the client and it is not in ALLOWED")
                elif rule[1] not in body:
                    problems.append(f"{name}:{fn.name} takes {param!r} but lacks its ownership check {rule[1]!r}")
    assert problems == [], "\n".join(problems)
