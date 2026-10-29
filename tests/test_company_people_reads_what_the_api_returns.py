"""The company People pages read only what the API returns, and every menu item
does something.

Two failures this guards, both found on the pages it replaced:

  * D-311 / D-276: /app/company/agents typed its rows as `{name, brokerage,
    rep_id, last_active}` against an API that returns `agent_name`,
    `last_activity` and (until now) no `rep_id`, so it crashed on its first row
    and its ?rep= filter matched nothing. `tsc` passed: a type written by hand
    is a claim about the API, not a check of it.
  * D-302: the reps and agents tables rendered "Deactivate", "Remove",
    "Remove from Company" and "Resend Invite" with no handler.

So: the `Rep`, `Agent` and `SeatSummary` types in lib/company-people.ts are
held to the dict keys `list_reps`, `list_agents` and `seats.seat_summary`
return, and every `<DropdownMenuItem>` under app/app/company has a handler.
"""
import ast
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB = ROOT / "apps/web/lib/company-people.ts"
COMPANY = ROOT / "apps/api/src/api/routes/company.py"
SEATS = ROOT / "apps/api/src/api/services/seats.py"
PAGES = ROOT / "apps/web/app/app/company"


def _appended_keys(path, fn_name, list_name):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    fn = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == fn_name)
    for call in ast.walk(fn):
        if (isinstance(call, ast.Call) and isinstance(call.func, ast.Attribute)
                and call.func.attr == "append" and getattr(call.func.value, "id", "") == list_name
                and call.args and isinstance(call.args[0], ast.Dict)):
            return {k.value for k in call.args[0].keys if isinstance(k, ast.Constant)}
    raise AssertionError(f"{fn_name} builds no {list_name}.append({{...}})")


def _returned_dict_keys(path, fn_name):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    fn = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == fn_name)
    for ret in ast.walk(fn):
        if isinstance(ret, ast.Return) and isinstance(ret.value, ast.Dict):
            keys = {k.value for k in ret.value.keys if isinstance(k, ast.Constant)}
            if keys:
                return keys
    raise AssertionError(f"{fn_name} returns no dict literal")


def _ts_type_fields(name):
    src = LIB.read_text(encoding="utf-8")
    m = re.search(rf"export type {name} = \{{([^}}\n]*)\}}", src) or \
        re.search(rf"export type {name} = \{{\n(.*?)\n\}}", src, re.S)
    assert m, f"type {name} not found in {LIB.name}"
    return set(re.findall(r"\b([a-z_]+)\??\s*:", m.group(1)))


def test_the_rep_type_is_what_list_reps_returns():
    missing = _ts_type_fields("Rep") - _appended_keys(COMPANY, "list_reps", "reps")
    assert not missing, f"lib/company-people.ts Rep reads {sorted(missing)}, which GET /v1/company/reps never returns"


def test_the_agent_type_is_what_list_agents_returns():
    missing = _ts_type_fields("Agent") - _appended_keys(COMPANY, "list_agents", "agents")
    assert not missing, f"lib/company-people.ts Agent reads {sorted(missing)}, which GET /v1/company/agents never returns"


def test_the_seat_type_is_what_seat_summary_returns():
    missing = _ts_type_fields("SeatSummary") - _returned_dict_keys(SEATS, "seat_summary")
    assert not missing, f"SeatSummary reads {sorted(missing)}, which seats.seat_summary never returns"


def test_the_pages_type_their_rows_from_the_lib():
    """A page that declares its own row type is back to a hand-written claim."""
    for page in ("reps/page.tsx", "agents/page.tsx"):
        src = (PAGES / page).read_text(encoding="utf-8")
        assert '@/lib/company-people' in src, page
        assert not re.search(r"^\s*(export\s+)?(type|interface)\s+(Rep|Agent)\b\s*[={]", src, re.M), \
            f"{page} declares its own row type"


def test_the_scan_sees_the_fields_it_should():
    """POSITIVE CONTROL: the parsers find the fields they exist to compare."""
    assert {"holds_seat", "agent_count", "status"} <= _appended_keys(COMPANY, "list_reps", "reps")
    assert {"rep_id", "agent_name", "last_activity"} <= _appended_keys(COMPANY, "list_agents", "agents")
    assert {"holds_seat", "agent_count"} <= _ts_type_fields("Rep")


def test_every_menu_item_in_the_company_pages_does_something():
    """D-302. A DropdownMenuItem must have onSelect/onClick, or be asChild
    around a link."""
    dead = []
    for page in PAGES.rglob("*.tsx"):
        src = page.read_text(encoding="utf-8")
        for m in re.finditer(r"<DropdownMenuItem\b([^>]*)>", src):
            attrs = m.group(1)
            if not re.search(r"\b(onSelect|onClick)=|\basChild\b", attrs):
                dead.append(f"{page.relative_to(ROOT)}:{src[:m.start()].count(chr(10)) + 1}")
    assert not dead, f"menu items with no handler (D-302): {dead}"


def test_people_offers_admin_actions_only_to_the_admin():
    """D-280: the API refuses a non-admin; the page must not offer them the
    button. Its actions are gated on `can_manage`, which /v1/company/reps
    returns."""
    src = (PAGES / "reps/page.tsx").read_text(encoding="utf-8")
    assert "repsData?.can_manage === true" in src
    assert "{canManage && <ConsequenceMenu" in src
    assert "{canManage && <div" in src, "the invite form is not gated"
    assert "canManage ? repActions(r) : []" in src, "Resend is not gated"
    tree = ast.parse(COMPANY.read_text(encoding="utf-8"))
    fn = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "list_reps")
    assert "can_manage" in ast.unparse(fn), "list_reps does not say who can act"
