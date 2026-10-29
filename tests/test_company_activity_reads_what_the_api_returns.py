"""Company Activity reads only what the API returns (D-317).

/app/company/reports and /app/company/schedules typed their rows by hand —
`created_at`, `user_type: "rep"`, `status: "complete"`, `run_count`, `rep_id`
— against an API that returned none of them. tsc passed; every report read
"Generating" with no name, date or PDF. The types in lib/company-activity.ts
are held to the dict keys the routes build, and the old paths only redirect.
"""
import ast
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB = ROOT / "apps/web/lib/company-activity.ts"
PAGE = ROOT / "apps/web/app/app/company/activity/page.tsx"
COMPANY = ROOT / "apps/api/src/api/routes/company.py"
OLD = {"reports": ROOT / "apps/web/app/app/company/reports/page.tsx",
       "schedules": ROOT / "apps/web/app/app/company/schedules/page.tsx"}
LAYOUT = ROOT / "apps/web/app/app-layout.tsx"


def _row_keys(fn_name):
    """The keys of the dict a route builds per row (`[{...} for r in ...]`)."""
    tree = ast.parse(COMPANY.read_text(encoding="utf-8"))
    fn = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == fn_name)
    comps = [c for c in ast.walk(fn) if isinstance(c, ast.ListComp) and isinstance(c.elt, ast.Dict)]
    assert comps, f"{fn_name} builds no [{{...}} for ...]"
    return {k.value for c in comps for k in c.elt.keys if isinstance(k, ast.Constant)}


def _ts_type_fields(name):
    m = re.search(rf"export type {name} = \{{\n(.*?)\n\}}", LIB.read_text(encoding="utf-8"), re.S)
    assert m, f"type {name} not found"
    return set(re.findall(r"^\s*([a-z_]+)\??\s*:", m.group(1), re.M))


def test_the_report_type_is_what_get_company_reports_returns():
    missing = _ts_type_fields("ActivityReport") - _row_keys("get_company_reports")
    assert not missing, f"ActivityReport reads {sorted(missing)}, which GET /v1/company/reports never returns"


def test_the_schedule_type_is_what_get_company_schedules_returns():
    missing = _ts_type_fields("ActivitySchedule") - _row_keys("get_company_schedules")
    assert not missing, f"ActivitySchedule reads {sorted(missing)}, which GET /v1/company/schedules never returns"


def test_the_scan_sees_the_fields_it_should():
    """POSITIVE CONTROL."""
    assert {"generated_at", "rep_name", "user_type"} <= _row_keys("get_company_reports")
    assert {"weekly_dow", "next_run_at", "rep_id"} <= _row_keys("get_company_schedules")
    assert {"generated_at", "rep_id"} <= _ts_type_fields("ActivityReport")


def test_the_page_types_its_rows_from_the_lib():
    src = PAGE.read_text(encoding="utf-8")
    assert "@/lib/company-activity" in src
    assert not re.search(r"^\s*(export\s+)?(type|interface)\s+\w*(Row|Report|Schedule)\b\s*[={]", src, re.M), \
        "the page declares its own row type"


def test_the_old_pages_only_redirect():
    for name, path in OLD.items():
        src = path.read_text(encoding="utf-8")
        assert 'redirect("/app/company/activity' in src, f"/app/company/{name} does not redirect"
        assert "interface" not in src and "fetch(" not in src, f"/app/company/{name} still renders its own table"


def test_the_rail_leads_here_and_stays_lit_on_the_old_paths():
    src = LAYOUT.read_text(encoding="utf-8")
    assert '{ name: "Activity", href: "/app/company/activity"' in src
    assert 'also: ["/app/company/reports", "/app/company/schedules"]' in src
