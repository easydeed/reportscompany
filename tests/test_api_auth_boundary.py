"""What the API accepts as proof of identity.

`AuthContextMiddleware` resolves an account three ways, and the third is a bare
`X-Demo-Account` header with no guard of any kind — no environment check, no
flag, no signature. It exists because it is the test suite's way of being
logged in, and it ships.

Gated rather than fixed because this is the production authentication path and
nothing in this container can run the API. The marker is strict, so the day a
guard lands the build says so and D-200 can be closed.
"""
import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
AUTHN = REPO / "apps/api/src/api/middleware/authn.py"
SETTINGS = REPO / "apps/api/src/api/settings.py"

_D200_GATED = pytest.mark.xfail(
    strict=True,
    reason="D-200: the X-Demo-Account header is accepted as an account id "
           "with no environment guard, so an unauthenticated request is "
           "served as any account it names. Not fixed here: a change to the "
           "production auth path, in a container that cannot run the API.",
)


def test_the_header_fallback_is_still_where_this_test_looks():
    """The guard on the test below — an assertion about a block that has moved
    would pass by checking nothing."""
    src = AUTHN.read_text(encoding="utf-8")
    assert 'request.headers.get("X-Demo-Account")' in src, (
        "the demo-header fallback is gone from authn.py. If it was removed "
        "rather than guarded, delete this file and close D-200."
    )


def test_the_safe_default_for_the_guard_is_still_available():
    """`settings.ENVIRONMENT` defaults to production, which is the only safe
    default for a security guard. `os.getenv("ENVIRONMENT", "dev")` — used at
    routes/unsubscribe.py:180 — fails OPEN when the variable is unset."""
    assert re.search(r'^\s*ENVIRONMENT:\s*str\s*=\s*"production"',
                     SETTINGS.read_text(encoding="utf-8"), re.M), (
        "settings.ENVIRONMENT no longer defaults to production, so a guard "
        "written against it would fail open where the variable is unset"
    )


@_D200_GATED
def test_the_demo_account_header_is_refused_outside_development():
    src = AUTHN.read_text(encoding="utf-8")
    block = src[src.index("# ── 3) Demo header fallback"):][:600]
    guarded = (
        "ENVIRONMENT" in block
        or "settings.ENVIRONMENT" in block
        or "DEBUG" in block
    )
    assert guarded, (
        "X-Demo-Account is accepted with no environment guard:\n" + block
    )
