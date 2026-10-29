"""The rep's pages read only what /v1/affiliate/* returns (D-324), and the
leads page reads no homeowner's contact details.

The pages these replace typed their rows by hand — `created_at`,
`status: "complete"`, `zip_codes`, `run_count`, an `agent` block from
/usage — against endpoints that returned none of it; every report read
"Generating", schedules had no agent or area, an agent's page had no name.
"""
import ast
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB = ROOT / "apps/web/lib/rep-book.ts"
AFF = ROOT / "apps/api/src/api/routes/affiliates.py"
PAGES = ROOT / "apps/web/app/app/affiliate"
LAYOUT = ROOT / "apps/web/app/app-layout.tsx"


def _fn(name):
    return next(n for n in ast.walk(ast.parse(AFF.read_text(encoding="utf-8")))
                if isinstance(n, ast.FunctionDef) and n.name == name)


def _keys(node):
    return {k.value for d in ast.walk(node) if isinstance(d, ast.Dict) for k in d.keys if isinstance(k, ast.Constant)}


def _row_keys(name):
    comps = [c for c in ast.walk(_fn(name)) if isinstance(c, ast.ListComp) and isinstance(c.elt, ast.Dict)]
    assert comps, name
    return {k.value for c in comps for k in c.elt.keys if isinstance(k, ast.Constant)}


def _ts(name):
    src = LIB.read_text(encoding="utf-8")
    m = re.search(rf"export type {name} = \{{\n(.*?)\n\}}", src, re.S) or re.search(rf"export type {name} = \{{([^}}\n]*)\}}", src)
    assert m, name
    return set(re.findall(r"\b([a-z_]+)\??\s*:", m.group(1)))


def _code(path):
    return re.sub(r"^\s*//.*$", "", path.read_text(encoding="utf-8"), flags=re.M)


PAIRS = [
    ("RepReport", lambda: _row_keys("get_all_agent_reports")),
    ("RepSchedule", lambda: _row_keys("get_all_agent_schedules")),
    ("AgentReport", lambda: _row_keys("get_agent_reports")),
    ("AgentSchedule", lambda: _row_keys("get_agent_schedules")),
    ("BookAgent", lambda: _keys(_fn("get_book_agent"))),
    ("LeadCounts", lambda: _keys(_fn("get_book_agent"))),
    ("AgentLeadCount", lambda: _keys(_fn("get_book_leads"))),
    ("BookLead", lambda: _keys(_fn("get_book_leads"))),
]


def test_every_rep_type_is_what_its_endpoint_returns():
    bad = {t: sorted(_ts(t) - keys()) for t, keys in PAIRS if _ts(t) - keys()}
    assert not bad, f"rep-book types read fields their endpoints never return: {bad}"


def test_the_scan_sees_the_fields_it_should():
    """POSITIVE CONTROL."""
    assert {"generated_at", "source", "agent_account_id"} <= _row_keys("get_all_agent_reports")
    assert {"came_from", "agent_name", "this_month"} <= _keys(_fn("get_book_leads"))
    assert {"generated_at", "source"} <= _ts("RepReport")


def test_the_leads_feed_carries_no_homeowner_detail():
    """The API side: the feed's row dict has no contact field; the SELECT
    reads none either, so a later edit to the dict cannot leak one."""
    fn = _fn("get_book_leads")
    src = ast.unparse(fn)
    assert not {"name", "email", "phone", "message"} & _keys(fn) - {"agent_name"}
    select = re.search(r"SELECT l\.id::text.*?FROM leads l", src, re.S).group(0)
    assert not re.search(r"\bl\.(name|email|phone|message|notes|ip_address)\b", select), select


def test_the_pages_type_their_rows_from_the_lib():
    for page in ("reports/page.tsx", "schedules/page.tsx", "agents/[agentId]/page.tsx", "leads/page.tsx"):
        src = (PAGES / page).read_text(encoding="utf-8")
        assert "@/lib/rep-book" in src, page
        assert not re.search(r"^\s*(export\s+)?(interface|type)\s+\w+\s*[={]", src, re.M), f"{page} declares its own row type"


def test_no_page_reads_a_homeowners_contact_details():
    for page in ("leads/page.tsx", "agents/[agentId]/page.tsx"):
        code = _code(PAGES / page)
        assert not re.search(r"\bl\.(email|phone|message|name)\b", code), page


def test_the_rail_has_leads():
    assert '{ name: "Leads", href: "/app/affiliate/leads"' in LAYOUT.read_text(encoding="utf-8")
