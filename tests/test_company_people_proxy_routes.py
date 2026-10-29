"""Each proxy route added for the People page and D-314 forwards the method it
exports to the API path it is named for.

`test_every_proxied_call_has_a_route.py` proves a route FILE exists for every
call. This proves the file does what its path says: the same method, the same
backend path, the `[id]` segment passed through. A route that exports GET where
the page POSTs, or forwards to the wrong path, would pass the existence check
and fail every click.
"""
import re
from pathlib import Path

import pytest

PROXY = Path(__file__).resolve().parents[1] / "apps/web/app/api/proxy"

ROUTES = [
    ("v1/company/seats", "GET", "/v1/company/seats"),
    ("v1/company/reps/[id]/reassign", "POST", "/v1/company/reps/${encodeURIComponent(id)}/reassign"),
    ("v1/company/reps/[id]/cancel-invite", "POST", "/v1/company/reps/${encodeURIComponent(id)}/cancel-invite"),
    ("v1/admin/leads/[id]", "DELETE", "/v1/admin/leads/${encodeURIComponent(id)}"),
    ("v1/admin/leads/export", "GET", "/v1/admin/leads/export"),
    ("v1/admin/property-reports/[id]/retry", "POST", "/v1/admin/property-reports/${encodeURIComponent(id)}/retry"),
]


@pytest.mark.parametrize("path,method,backend", ROUTES, ids=[r[0] for r in ROUTES])
def test_the_route_forwards_its_method_to_its_path(path, method, backend):
    src = (PROXY / path / "route.ts").read_text(encoding="utf-8")
    assert re.search(rf"export async function {method}\(", src), f"{path} does not export {method}"
    assert f"${{API_BASE}}{backend}" in src, f"{path} does not forward to {backend}"
    if method != "GET":
        assert f"method: '{method}'" in src or f'method: "{method}"' in src, f"{path} forwards with the wrong method"
    assert "mr_token" in src, f"{path} does not pass the session"
