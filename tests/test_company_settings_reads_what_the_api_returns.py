"""The company Settings page reads only what GET /v1/company/settings returns,
offers no control the API lacks, and lets only the admin set the address (D-079)."""
import ast
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB = ROOT / "apps/web/lib/company-settings.ts"
PAGE = ROOT / "apps/web/app/app/company/settings/page.tsx"
COMPANY = ROOT / "apps/api/src/api/routes/company.py"
LAYOUT = ROOT / "apps/web/app/app-layout.tsx"


def _settings_fn():
    return next(n for n in ast.walk(ast.parse(COMPANY.read_text(encoding="utf-8")))
                if isinstance(n, ast.FunctionDef) and n.name == "get_settings")


def _keys(node):
    return {k.value for d in ast.walk(node) if isinstance(d, ast.Dict) for k in d.keys if isinstance(k, ast.Constant)}


def _code(path):
    return re.sub(r"^\s*//.*$", "", path.read_text(encoding="utf-8"), flags=re.M)


def _ts_fields(src_block):
    return set(re.findall(r"\b([a-z_]+)\??\s*:", src_block))


def test_the_types_are_what_get_settings_returns():
    lib = LIB.read_text(encoding="utf-8")
    settings = re.search(r"export type CompanySettings = \{\n(.*?)\n\}", lib, re.S).group(1)
    person = re.search(r"export type Person = \{([^}]*)\}", lib).group(1)
    returned = _keys(_settings_fn())
    missing = (_ts_fields(settings) | _ts_fields(person)) - returned - {"people", "company"} | ({"people", "company"} - returned)
    assert not missing, f"the page reads {sorted(missing)}, which GET /v1/company/settings never returns"


def test_the_scan_sees_the_fields_it_should():
    """POSITIVE CONTROL."""
    assert {"postal_address", "website_url", "role", "can_manage", "you"} <= _keys(_settings_fn())


def test_no_control_the_api_does_not_have():
    """No Add an admin, no Remove, no Email me toggles: there are no endpoints."""
    code = _code(PAGE)
    assert not re.search(r">\s*(Add an admin|Remove|Invite)\b", code)
    assert 'type="checkbox"' not in code and "Switch" not in code


def test_the_admin_sets_the_address_through_the_account_endpoint():
    """D-079 (Jerry, 2026-10-30): the company's admin sets its postal address,
    through PUT /v1/account/postal-address — the PUT body is built by
    `addressPut`, so an emptied field is sent as a clear. A member still only
    sees it. Design's mock address is never on the page."""
    code = _code(PAGE)
    assert "TODO(B5)" not in PAGE.read_text(encoding="utf-8")
    assert re.search(r'send\("/v1/account/postal-address", "PUT", addr\)', code)
    assert "addressPut(s?.company.postal_address" in code
    assert re.search(r"action=\{canManage && addr &&", code)
    assert re.search(r"\{canManage\s*\?\s*<span[^>]*>\s*<input aria-label=\"Address\"", code)
    assert "18575 Jamboree" not in PAGE.read_text(encoding="utf-8")


def test_only_the_admin_edits_the_company():
    code = _code(PAGE)
    assert "s?.can_manage === true" in code
    assert re.search(r"action=\{canManage && site &&", code)
    assert re.search(r"\{canManage\s*\?\s*<input aria-label=\"Website\"", code)


def test_the_rail_leads_here():
    assert '{ name: "Settings", href: "/app/company/settings"' in LAYOUT.read_text(encoding="utf-8")
