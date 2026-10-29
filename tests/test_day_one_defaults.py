"""A fresh account's first session: signed in, and in a colour.

Two defects a new customer met before anything else, each with one cause:

* D-241 — `POST /v1/auth/register` set its cookie on its own response, which
  the Next proxy cannot pass on, and returned no `access_token` for the proxy
  to write `mr_token` from. Signing up landed on /login.
* D-243 / D-256 — `accounts.secondary_color` defaulted to '#ffffff', and every
  reader takes that column as the accent. A new account asked for white.

Read from source, like the rest of the root suite: the API's own suite needs
a database this container does not have.
"""
import ast
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
AUTH = REPO / "apps/api/src/api/routes/auth.py"
PROXY = REPO / "apps/web/app/api/proxy/v1/auth/register/route.ts"
MIGRATIONS = REPO / "db/migrations"


def _function(src: str, name: str) -> ast.FunctionDef:
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    raise AssertionError(f"no function {name!r} in {AUTH}")


def test_register_hands_the_proxy_the_token_it_writes_the_cookie_from():
    fn = _function(AUTH.read_text(encoding="utf-8"), "register")
    success = [
        r for r in ast.walk(fn)
        if isinstance(r, ast.Return) and isinstance(r.value, ast.Dict)
        and any(isinstance(k, ast.Constant) and k.value == "ok" for k in r.value.keys)
    ]
    assert success, "register's success return was not found"
    for r in success:
        keys = {k.value for k in r.value.keys if isinstance(k, ast.Constant)}
        assert "access_token" in keys, (
            "register returns no access_token, so the proxy sets no mr_token "
            "and a new account is bounced to /login (D-241)"
        )
    # ...and the proxy still writes the cookie from it.
    assert "data.access_token" in PROXY.read_text(encoding="utf-8")


def _default_statements():
    """Every statement that sets or drops accounts.secondary_color's default,
    in the order the runner applies them (filename order)."""
    out = []
    pat = re.compile(
        r"secondary_color\s+VARCHAR\(\d+\)\s+DEFAULT\s+'([^']*)'"
        r"|ALTER\s+COLUMN\s+secondary_color\s+(DROP\s+DEFAULT|SET\s+DEFAULT\s+'([^']*)')",
        re.IGNORECASE,
    )
    for f in sorted(MIGRATIONS.glob("[0-9]*.sql")):
        sql = "\n".join(l for l in f.read_text(encoding="utf-8").splitlines()
                        if not l.lstrip().startswith("--"))
        for m in pat.finditer(sql):
            value = m.group(1) if m.group(1) is not None else (m.group(3) if m.group(3) is not None else None)
            out.append((f.name, value))
    return out


def test_the_accent_column_does_not_default_to_white():
    statements = _default_statements()
    assert statements, "the scan found no default for secondary_color at all"
    name, value = statements[-1]
    assert value is None or value.lower() not in {"#ffffff", "#fff", "white"}, (
        f"{name} leaves accounts.secondary_color defaulting to {value!r}; every "
        "reader takes that column as the accent, so a new account renders in white"
    )
