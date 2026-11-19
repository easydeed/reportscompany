"""The API reads the heartbeat keys the worker writes (LR-027).

apps/api/src/api/routes/ready.py and apps/worker/src/worker/ops_heartbeat.py
are separately deployed and cannot import each other, so each names the keys.
A rename on one side alone would leave /ready reading a key nothing writes, and
every deployment would report itself not ready.
"""
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API = ROOT / "apps/api/src/api/routes/ready.py"
WORKER = ROOT / "apps/worker/src/worker/ops_heartbeat.py"
SHARED = ("TICKER_KEY", "WORKER_KEY", "CELERY_QUEUE")


def constants(path):
    found = {}
    for node in ast.parse(path.read_text()).body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            if isinstance(node.value, ast.Constant):
                found[node.targets[0].id] = node.value.value
    return found


def test_both_services_name_the_same_heartbeat_keys_and_queue():
    api, worker = constants(API), constants(WORKER)
    for name in SHARED:
        assert api[name] == worker[name], name


def test_the_worker_key_outlives_the_backlog_horizon_the_api_allows():
    # /ready calls a 5-30 minute old worker heartbeat with a queue a backlog.
    # If the key expired first, a backlog would read as a dead worker.
    assert constants(WORKER)["WORKER_TTL_S"] > constants(API)["WORKER_BACKLOG_LIMIT_S"]


def test_the_ticker_key_outlives_the_ticker_staleness_threshold():
    assert constants(WORKER)["TICKER_TTL_S"] > constants(API)["TICKER_STALE_S"]


MONITOR = ROOT / "apps/worker/src/worker/ops_monitor.py"


def test_the_monitor_judges_heartbeats_by_the_same_thresholds_as_ready():
    # /ready and the monitor must agree on "stale" and "backlog", or the
    # pinger and the operator alert would contradict each other.
    api, monitor = constants(API), constants(MONITOR)
    for name in ("TICKER_STALE_S", "WORKER_STALE_S", "WORKER_BACKLOG_LIMIT_S"):
        assert api[name] == monitor[name], name
