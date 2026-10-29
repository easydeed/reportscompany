"""The API imports the worker's MarketReportBuilder — it must install its deps.

`/v1/report-preview/{kind}` and the branding page's sample PDF render the
worker's builder inside the API process. The builder imports jinja2; the API
never declared it. Every test passed anyway, because the backend workflow
installs both projects into ONE virtualenv and the worker's jinja2 covered for
the API's missing one. Production, which installs `apps/api` alone, answered
503 "No module named 'jinja2'" on every preview the day they shipped.

So this does not import the builder and trust the result (the shared venv
would make that pass). It records which third-party packages the import
pulls in, in a fresh interpreter, and checks each against `apps/api`'s OWN
lockfile — the file production installs from.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
API_LOCK = REPO / "apps/api/poetry.lock"

PROBE = r"""
import importlib.metadata as md, json, sys
sys.path[:0] = [sys.argv[1]]
before = set(sys.modules)
import worker.market_builder  # noqa: F401
tops = {m.split('.')[0] for m in set(sys.modules) - before}
tops = {t for t in tops if t not in sys.stdlib_module_names and t != 'worker' and not t.startswith('_')}
dists = md.packages_distributions()
print(json.dumps(sorted({d for t in tops for d in dists.get(t, [t])})))
"""


def _norm(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def test_every_package_the_builder_imports_is_in_the_api_lockfile():
    out = subprocess.run(
        [sys.executable, "-c", PROBE, str(REPO / "apps/worker/src")],
        capture_output=True, text=True, check=True,
    ).stdout.strip().splitlines()[-1]
    needed = {_norm(d) for d in json.loads(out)}
    assert needed, "the probe found no third-party imports at all; it has stopped measuring"
    locked = {_norm(n) for n in re.findall(r'^name = "([^"]+)"', API_LOCK.read_text(), re.M)}
    missing = sorted(needed - locked)
    assert missing == [], (
        f"worker.market_builder imports {missing}, which apps/api does not install; "
        "every report preview and sample PDF would 503 in production"
    )
