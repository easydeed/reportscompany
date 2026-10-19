"""What the API accepts as proof of identity.

`AuthContextMiddleware` resolves an account three ways, and the third is the
`X-Demo-Account` header — an account id, accepted as a credential. Until
2026-10-19 it was accepted unconditionally, in production (D-200).

WHY THESE TESTS LIVE IN THE ROOT SUITE AND NOT UNDER apps/api/tests/
--------------------------------------------------------------------
Because they run. `apps/api`'s own suite needs `pydantic_settings`, `httpx`,
`redis` and `psycopg`, none of which this container has — the whole reason
D-200 was filed rather than fixed on the first pass. A control nobody can
exercise is the thing this board keeps finding, so the predicate is tested
HERE, from the real source text, with a stub standing in for `settings`.

That is a deliberate trade and it has a limit worth stating: this proves the
decision function, and `test_the_header_read_is_inside_the_guard` proves the
call site is wired to it. It does not prove a live 401. Only CI, or a
deployment, can do that.
"""
import ast
import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
AUTHN = REPO / "apps/api/src/api/middleware/authn.py"
SETTINGS = REPO / "apps/api/src/api/settings.py"
API_CONFTEST = REPO / "apps/api/tests/conftest.py"


class _Settings:
    def __init__(self, env):
        self.ENVIRONMENT = env


def _predicate(env):
    """Exec the REAL `_DEMO_HEADER_ENVIRONMENTS` and `_demo_header_allowed`
    out of `authn.py` against a stub settings, and call it.

    Lifted by AST rather than imported, because importing that module pulls in
    four packages this container does not have — and rather than copied, because
    a copy of a security predicate is a second implementation that will drift
    from the one that ships.
    """
    tree = ast.parse(AUTHN.read_text(encoding="utf-8"))
    wanted = []
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
                getattr(t, "id", None) == "_DEMO_HEADER_ENVIRONMENTS"
                for t in node.targets):
            wanted.append(node)
        if isinstance(node, ast.FunctionDef) and node.name == "_demo_header_allowed":
            wanted.append(node)
    assert len(wanted) == 2, (
        "the demo-header allowlist and its predicate are no longer both "
        "module-level in authn.py, so this test is not reading the control "
        "that ships"
    )
    ns = {"settings": _Settings(env), "frozenset": frozenset}
    exec(compile(ast.Module(body=wanted, type_ignores=[]), "<authn>", "exec"), ns)
    return ns["_demo_header_allowed"]()


# ─────────────────────────────────────────────────────────────────────────────
# The control itself
# ─────────────────────────────────────────────────────────────────────────────

def test_the_header_read_is_inside_the_guard():
    """The predicate is worthless if the call site does not consult it."""
    src = AUTHN.read_text(encoding="utf-8")
    idx = src.index('request.headers.get("X-Demo-Account")')
    preceding = src[max(0, idx - 400):idx]
    assert "_demo_header_allowed()" in preceding, (
        "X-Demo-Account is read without the guard between it and the request. "
        "D-200: this header is an identity assertion."
    )


@pytest.mark.parametrize("env", [
    "production",      # the default, and what an unset variable resolves to
    "Production",      # why this is an allowlist and not `!= "production"`
    "PRODUCTION",
    "prod",
    "staging",
    "development",     # settings.py:11 — staging and local dev use this
    "dev",
    "",
    "testing",         # a near miss is a miss
    "test,dev",
    None,
])
def test_the_demo_header_is_refused_everywhere_but_the_test_environment(env):
    assert _predicate(env) is False, (
        f"ENVIRONMENT={env!r} allows X-Demo-Account to stand in for a "
        f"credential. Every value that is not exactly a test environment must "
        f"fail CLOSED — that is the whole of D-200."
    )


@pytest.mark.parametrize("env", ["test", "TEST", " test "])
def test_the_test_environment_keeps_the_header_so_the_api_suite_still_runs(env):
    """Eight files under `apps/api/tests/` authenticate with this header. The
    guard has to be narrow, not absent.

    Case and surrounding whitespace are normalised, which cannot widen the
    allowlist — `" production "` still refuses — and keeps the control from
    turning on a trailing space pasted into a deploy variable.
    """
    assert _predicate(env) is True, (
        f"ENVIRONMENT={env!r} refuses the header, which breaks the eight API "
        f"test files that use it as their login"
    )


def test_the_api_test_suite_sets_the_environment_before_settings_is_built():
    """`settings` is a pydantic-settings object built at import time, so this
    has to happen in conftest and before the first `from api.settings import
    settings`. Setting it later would hand eight files a 401 with nothing to
    say why."""
    src = API_CONFTEST.read_text(encoding="utf-8")
    assert 'os.environ.setdefault("ENVIRONMENT", "test")' in src, (
        "apps/api/tests/conftest.py no longer sets ENVIRONMENT=test, so every "
        "test that authenticates with X-Demo-Account gets 401"
    )
    set_at = src.index('os.environ.setdefault("ENVIRONMENT"')
    first_api_import = min(
        [m.start() for m in re.finditer(r"^(?:from|import) api\b", src, re.M)]
        or [len(src)])
    assert set_at < first_api_import, (
        "ENVIRONMENT is set after the first `api` import in conftest, which is "
        "after settings has already read the environment"
    )


# ─────────────────────────────────────────────────────────────────────────────
# The defaults the guard rests on
# ─────────────────────────────────────────────────────────────────────────────

def test_settings_environment_still_defaults_to_production():
    """The guard fails closed only because an unset variable resolves to
    "production". If that default changes, the control silently weakens."""
    assert re.search(r'^\s*ENVIRONMENT:\s*str\s*=\s*"production"',
                     SETTINGS.read_text(encoding="utf-8"), re.M), (
        "settings.ENVIRONMENT no longer defaults to production"
    )


def test_the_guard_is_not_written_against_os_getenv():
    """D-201: `os.getenv("ENVIRONMENT", "dev")` at routes/unsubscribe.py:180
    defaults to dev and therefore fails OPEN when the variable is unset. That
    form must not spread into the authentication path."""
    src = AUTHN.read_text(encoding="utf-8")
    body = src[src.index("def _demo_header_allowed"):][:400]
    assert "os.getenv" not in body, (
        "the demo-header guard reads os.getenv rather than settings. Any "
        "default other than production fails open on an unset variable."
    )
