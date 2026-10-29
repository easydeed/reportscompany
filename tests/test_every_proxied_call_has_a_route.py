"""Every /v1 path the web app calls through /api/proxy has a proxy route.

The proxy is one route file per endpoint (apps/web/app/api/proxy/v1/**/route.ts),
not a catch-all. A page that calls a path nobody wrote a route for gets
Next's 404 page back; `res.json()` on that throws, and the button quietly does
nothing. Found building the company People page: #224 shipped the seat API
(`/v1/company/seats`, `/reps/{id}/reassign`, `/reps/{id}/cancel-invite`) with no
proxy routes, so no browser could reach it — and four more calls already in
production had the same gap (D-314): the admin lead delete, the admin lead
CSV export, the admin property-report retry, and the mobile report's PDF
status poll.

The scan reads every literal `/v1/...` path passed to fetch / apiFetch /
apiFetchRQ / post in apps/web (outside app/api), turns `${...}` into a path
segment, and requires a route directory that matches it, `[id]` matching any
one segment.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "apps/web"
PROXY = WEB / "app/api/proxy"

CALL = re.compile(r"""(?:apiFetchRQ|apiFetch|post|fetch)\(\s*[`"'](?:/api/proxy)?(/v1/[^`"'\s]*)""")


def _routes():
    out = []
    for f in PROXY.rglob("route.ts"):
        rel = f.parent.relative_to(PROXY).as_posix()
        rel = re.sub(r"\[\.\.\.[^\]]+\]", ".+", rel)
        rel = re.sub(r"\[[^\]]+\]", "[^/]+", rel)
        out.append(re.compile(f"^/{rel}$"))
    return out


def _calls():
    found = {}
    for f in [*WEB.rglob("*.ts"), *WEB.rglob("*.tsx")]:
        parts = f.relative_to(WEB).parts
        if parts[0] in ("node_modules", ".next") or f.relative_to(WEB).as_posix().startswith("app/api/"):
            continue
        text = f.read_text(encoding="utf-8", errors="ignore")
        for m in CALL.finditer(text):
            path = m.group(1).split("?")[0]
            # `${params}` glued to the end is a query string, not a segment.
            path = re.sub(r"(?<=[A-Za-z0-9_-])\$\{[^}]+\}$", "", path)
            path = re.sub(r"\$\{[^}]+\}", "X", path).rstrip("/")
            found.setdefault(path, f"{f.relative_to(ROOT)}:{text[:m.start()].count(chr(10)) + 1}")
    return found


def test_every_proxied_call_has_a_proxy_route():
    routes = _routes()
    missing = {p: where for p, where in _calls().items() if not any(r.match(p) for r in routes)}
    assert not missing, (
        "the web app calls these through /api/proxy and no proxy route exists — the browser "
        "gets a 404 page and the action silently fails:\n  "
        + "\n  ".join(f"{p}  ({w})" for p, w in sorted(missing.items())))


def test_the_scan_sees_the_calls_it_should():
    """POSITIVE CONTROL: the People page's seat calls are found, and a path with
    no route would be reported."""
    calls = _calls()
    assert "/v1/company/seats" in calls
    assert "/v1/company/reps/X/reassign" in calls and "/v1/company/reps/X/cancel-invite" in calls
    assert len(calls) > 100, f"only {len(calls)} calls found; the scan has stopped reading"
    assert not any(r.match("/v1/company/reps/X/no-such-action") for r in _routes())
