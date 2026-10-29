"""Plan & Seats reads only what GET /v1/company/seats returns (D-315).

The types in lib/company-plan.ts are held to the dict keys the route and
`services/seats.py` build — the same check the People page has
(test_company_people_reads_what_the_api_returns.py), because a hand-written
type is a claim about the API, not a check of it.
"""
import ast
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB = ROOT / "apps/web/lib/company-plan.ts"
PAGE = ROOT / "apps/web/app/app/company/plan/page.tsx"
COMPANY = ROOT / "apps/api/src/api/routes/company.py"
SEATS = ROOT / "apps/api/src/api/services/seats.py"
BILLING = ROOT / "apps/web/app/app/settings/billing/page.tsx"
LAYOUT = ROOT / "apps/web/app/app-layout.tsx"


def _fn(path, name):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == name)


def _dict_keys(node):
    """Every constant key of every dict literal under `node`."""
    return {k.value for d in ast.walk(node) if isinstance(d, ast.Dict)
            for k in d.keys if isinstance(k, ast.Constant)}


def _ts_type_fields(name):
    src = LIB.read_text(encoding="utf-8")
    m = re.search(rf"export type {name} = \{{([^}}\n]*)\}}", src) or \
        re.search(rf"export type {name} = \{{\n(.*?)\n\}}", src, re.S)
    assert m, f"type {name} not found in {LIB.name}"
    return set(re.findall(r"\b([a-z_]+)\??\s*:", m.group(1)))


def test_agent_plan_is_what_seats_agent_plan_returns():
    missing = _ts_type_fields("AgentPlan") - _dict_keys(_fn(SEATS, "agent_plan"))
    assert not missing, f"AgentPlan reads {sorted(missing)}, which seats.agent_plan never returns"


def test_seat_period_is_what_seat_history_returns():
    missing = _ts_type_fields("SeatPeriod") - _dict_keys(_fn(SEATS, "seat_history"))
    assert not missing, f"SeatPeriod reads {sorted(missing)}, which seats.seat_history never returns"


def test_the_page_reads_only_keys_get_seats_returns():
    returned = _dict_keys(_fn(COMPANY, "get_seats"))
    read = set(re.findall(r"seatsData\?\.([a-z_]+)", PAGE.read_text(encoding="utf-8")))
    assert read, "the page reads nothing from /v1/company/seats"
    assert read <= returned, f"the page reads {sorted(read - returned)}, which GET /v1/company/seats never returns"


def test_the_scan_sees_the_fields_it_should():
    """POSITIVE CONTROL."""
    assert {"market_reports", "plan_name"} <= _ts_type_fields("AgentPlan")
    assert {"agent_plan", "history", "can_manage"} <= _dict_keys(_fn(COMPANY, "get_seats"))
    assert {"ended_reason", "successor_name"} <= _dict_keys(_fn(SEATS, "seat_history"))


def test_the_page_types_no_limit():
    """The agents' numbers come from `agent_plan`; a digit followed by
    'report' in the page source is a number typed in."""
    src = re.sub(r"^\s*//.*$", "", PAGE.read_text(encoding="utf-8"), flags=re.M)   # code, not comments
    assert not re.search(r"\b\d+\s+(market |property )?reports?\b", src), "a report limit is typed into the page"


def test_open_seats_offer_an_invite_only_to_the_admin():
    src = PAGE.read_text(encoding="utf-8")
    assert "seatsData?.can_manage === true" in src
    assert re.search(r"\{canManage\s*\?\s*<Link href=\"/app/company/reps\"", src)


def test_the_rail_and_the_old_link_lead_here():
    assert '{ name: "Plan & Seats", href: "/app/company/plan"' in LAYOUT.read_text(encoding="utf-8")
    billing = BILLING.read_text(encoding="utf-8")
    assert 'router.replace("/app/company/plan")' in billing, "a company on the agent billing page is not sent to its own"
    assert "plans[0].features" not in billing, "an unknown plan still shows the Free plan's features"
