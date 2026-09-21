"""
D-037 — the bridge stops shredding jobs it cannot dispatch.

WHAT WAS WRONG
--------------
`run_redis_consumer_forever` took an item with `blpop`, which REMOVES it, and
then parsed it, subscripted it three times, and handed it to Celery. The
catch-all at the bottom of the loop logged one line and continued. Anything
going wrong in that window — a malformed payload, a missing key, a broker
publish failure — destroyed the job permanently. The `report_generations` row
stayed `pending` forever, nothing sweeps that table, and `/admin/health` counted
it as `idle_with_pending`: a number that goes up and never comes down.

Same user-visible symptom as D-036, opposite recovery property. An outage
self-heals when the bridge returns; this did not.

WHY THESE TESTS USE A REAL REDIS
--------------------------------
The fix is a claim about Redis semantics — that `blmove` takes and places in one
atomic step, and that `lrem`/`lmove` put things back where this code thinks they
do. A fake that implements those operations implements my BELIEF about them,
and would agree with the code for exactly the reasons the code might be wrong.
§0.6: where the behaviour belongs to somebody else's software, the experiment is
the citation.

Redis 7.0.15 locally; `BLMOVE` needs 6.2+. The bridge prints the server version
at startup so a deployment log answers "does this apply here" without anyone
reproducing it.

Run:
    BRIDGE_TEST_REDIS_URL=redis://localhost:6379/15 \
      PYTHONPATH=apps/worker/src pytest apps/worker/tests/test_bridge_durability.py -v
"""
import json
import os
import sys
import threading
import time
import uuid
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

REDIS_URL = os.getenv("BRIDGE_TEST_REDIS_URL")

redis = pytest.importorskip("redis", reason="redis-py is required")
pytestmark = pytest.mark.skipif(
    not REDIS_URL,
    reason="Set BRIDGE_TEST_REDIS_URL to a throwaway Redis to run the bridge tests",
)

os.environ.setdefault("DATABASE_URL", "postgresql://fake/fake")
os.environ.setdefault("REDIS_URL", REDIS_URL or "redis://localhost:6379/0")

from worker import tasks  # noqa: E402


def job(run_id="run-1", **over):
    body = {
        "run_id": run_id,
        "account_id": "acct-1",
        "report_type": "market_snapshot",
        "params": {"city": "Glendora"},
    }
    body.update(over)
    return json.dumps(body)


@pytest.fixture
def bridge(monkeypatch):
    """
    A real Redis, a unique key prefix per test, and a recording stand-in for
    `generate_report.delay`.

    The keys are namespaced by uuid rather than flushed, so a test cannot wipe a
    database somebody is using — this connects to whatever URL it is given.
    """
    r = redis.from_url(REDIS_URL, decode_responses=True)
    prefix = f"bridgetest:{uuid.uuid4().hex[:8]}"

    monkeypatch.setattr(tasks, "QUEUE_KEY", prefix)
    monkeypatch.setattr(tasks, "PROCESSING_KEY", f"{prefix}:processing")
    monkeypatch.setattr(tasks, "DEAD_LETTER_KEY", f"{prefix}:dead")

    dispatched = []
    failures = {"raise_times": 0}

    class FakeDelay:
        def delay(self, *args):
            if failures["raise_times"] > 0:
                failures["raise_times"] -= 1
                raise RuntimeError("broker unavailable")
            dispatched.append(args)

    monkeypatch.setattr(tasks, "generate_report", FakeDelay())

    marked = []
    monkeypatch.setattr(
        tasks, "_mark_run_failed",
        lambda run_id, reason: marked.append((run_id, reason)) or True,
    )

    state = {
        "r": r, "q": prefix, "p": f"{prefix}:processing", "d": f"{prefix}:dead",
        "dispatched": dispatched, "marked": marked, "failures": failures,
    }
    try:
        yield state
    finally:
        r.delete(prefix, f"{prefix}:processing", f"{prefix}:dead")


def take_one(b):
    """The bridge's own first step, so the tests exercise the real entry state."""
    return b["r"].blmove(b["q"], b["p"], 1, "LEFT", "RIGHT")


# ── nothing is lost ─────────────────────────────────────────────────────────

def test_a_good_job_is_dispatched_and_the_lists_end_empty(bridge):
    b = bridge
    b["r"].rpush(b["q"], job())
    assert tasks._handle_payload(b["r"], take_one(b)) == "dispatched"

    assert len(b["dispatched"]) == 1
    assert b["dispatched"][0][0] == "run-1"
    assert b["r"].llen(b["p"]) == 0, "a dispatched job was left in the processing list"
    assert b["r"].llen(b["q"]) == 0
    assert b["r"].llen(b["d"]) == 0


def test_an_unparseable_payload_is_dead_lettered_not_destroyed(bridge):
    """
    THE REGRESSION. `json.loads` on `{not json` raised inside the loop's try,
    the catch-all printed one line, and the job — already removed by `blpop` —
    was gone.
    """
    b = bridge
    b["r"].rpush(b["q"], "{not json")
    assert tasks._handle_payload(b["r"], take_one(b)) == "unreadable"

    assert b["r"].llen(b["d"]) == 1, "the unreadable job was not preserved anywhere"
    assert b["r"].lrange(b["d"], 0, -1) == ["{not json"]
    assert b["r"].llen(b["p"]) == 0, "it was left stuck in the processing list"


def test_a_payload_missing_a_key_is_dead_lettered_and_the_row_is_marked(bridge):
    """
    `data["account_id"]` on a payload without one. The producer always sends it
    today (api/worker_client.py:15) — which is exactly the kind of guarantee
    that holds until somebody adds a second producer.
    """
    b = bridge
    payload = json.dumps({"run_id": "run-9", "report_type": "market_snapshot"})
    b["r"].rpush(b["q"], payload)
    assert tasks._handle_payload(b["r"], take_one(b)) == "unreadable"

    assert b["r"].llen(b["d"]) == 1
    assert b["marked"] == [("run-9", b["marked"][0][1])], "the row was not marked failed"
    assert "account_id" in b["marked"][0][1], (
        f"the recorded reason does not say what was missing: {b['marked'][0][1]!r}"
    )


def test_a_payload_with_no_run_id_is_still_kept(bridge):
    """
    Nothing to mark — there is no row to reach. The item must still survive,
    because "we cannot identify it" is not a reason to destroy it.
    """
    b = bridge
    b["r"].rpush(b["q"], json.dumps({"account_id": "a", "report_type": "t"}))
    assert tasks._handle_payload(b["r"], take_one(b)) == "unreadable"
    assert b["r"].llen(b["d"]) == 1
    assert b["marked"] == [], "a row was marked failed without a run_id to identify it"


# ── dispatch failures retry, then give up loudly ────────────────────────────

def test_a_dispatch_failure_is_requeued_with_an_attempt_count(bridge):
    b = bridge
    b["failures"]["raise_times"] = 1
    b["r"].rpush(b["q"], job())
    assert tasks._handle_payload(b["r"], take_one(b)) == "requeued"

    assert b["r"].llen(b["p"]) == 0, "the failed job was left in the processing list"
    assert b["r"].llen(b["d"]) == 0, "a first failure went straight to dead letters"
    back = json.loads(b["r"].lrange(b["q"], 0, -1)[0])
    assert back[tasks.ATTEMPTS_FIELD] == 1
    assert back["run_id"] == "run-1"


def test_a_blip_recovers_on_the_retry(bridge):
    """The point of retrying at all: one failure then success dispatches once."""
    b = bridge
    b["failures"]["raise_times"] = 1
    b["r"].rpush(b["q"], job())

    tasks._handle_payload(b["r"], take_one(b))     # fails, re-queues
    tasks._handle_payload(b["r"], take_one(b))     # succeeds

    assert len(b["dispatched"]) == 1
    assert b["r"].llen(b["q"]) == 0
    assert b["r"].llen(b["p"]) == 0
    assert b["r"].llen(b["d"]) == 0


def test_it_gives_up_after_the_attempt_limit_rather_than_looping(bridge):
    """
    The other half. An unbounded retry is the same hot loop in slower motion,
    and a payload that will never dispatch would occupy the bridge forever.
    """
    b = bridge
    b["failures"]["raise_times"] = 99
    b["r"].rpush(b["q"], job())

    outcomes = []
    for _ in range(tasks.MAX_DISPATCH_ATTEMPTS + 2):
        payload = take_one(b)
        if payload is None:
            break
        outcomes.append(tasks._handle_payload(b["r"], payload))

    assert outcomes[-1] == "given_up", outcomes
    assert len(outcomes) == tasks.MAX_DISPATCH_ATTEMPTS, (
        f"expected {tasks.MAX_DISPATCH_ATTEMPTS} attempts, got {outcomes}"
    )
    assert b["r"].llen(b["d"]) == 1, "the abandoned job was not preserved"
    assert b["r"].llen(b["q"]) == 0
    assert b["r"].llen(b["p"]) == 0
    assert b["marked"] and b["marked"][0][0] == "run-1", (
        "the row was not marked failed, so the report stays 'pending' forever — "
        "which is the defect, arriving three attempts later"
    )


# ── the crash window ────────────────────────────────────────────────────────

def test_a_job_taken_but_never_handled_is_recovered(bridge):
    """
    THE CASE THE OLD CODE COULD NOT SURVIVE, and the reason `blmove` rather than
    a try/except around `blpop`: this simulates the process dying between taking
    the item and doing anything with it. No Python runs. No handler fires.

    With `blpop` the item existed only in a local variable in a dead process.
    """
    b = bridge
    b["r"].rpush(b["q"], job("run-crash"))
    take_one(b)                                  # taken, then "the process dies"

    assert b["r"].llen(b["q"]) == 0, "precondition: it is off the queue"
    assert b["r"].llen(b["p"]) == 1, "precondition: it is in the processing list"

    assert tasks._recover_processing(b["r"]) == 1
    assert b["r"].llen(b["p"]) == 0
    assert json.loads(b["r"].lrange(b["q"], 0, -1)[0])["run_id"] == "run-crash"


def test_recovery_restores_order_rather_than_reversing_it(bridge):
    """
    `LMOVE ... RIGHT LEFT` — from the end of processing to the head of the
    queue. Taking from the left of processing instead would hand the jobs back
    in reverse, which is a silent correctness bug in a queue whose producer
    (`rpush`) and consumer (`blmove ... LEFT`) are otherwise strictly FIFO.
    """
    b = bridge
    for i in range(3):
        b["r"].rpush(b["q"], job(f"run-{i}"))
    for _ in range(3):
        take_one(b)

    tasks._recover_processing(b["r"])
    order = [json.loads(p)["run_id"] for p in b["r"].lrange(b["q"], 0, -1)]
    assert order == ["run-0", "run-1", "run-2"], order


def test_recovery_on_an_empty_list_does_nothing(bridge):
    assert tasks._recover_processing(bridge["r"]) == 0


# ── the real loop, end to end ───────────────────────────────────────────────

def test_the_real_loop_drains_the_queue_and_recovers_a_stranded_job(bridge, monkeypatch):
    """
    The real `run_redis_consumer_forever`, in a thread, against the real Redis,
    with a job pre-stranded in the processing list.

    WHAT THIS PROVES, EXACTLY: that `_recover_processing` is wired into startup
    rather than merely present in the file, and that the loop reaches
    `_handle_payload`. It does **not** prove the loop's take is atomic — see
    `test_the_loop_does_not_lose_a_job_it_is_holding` below, which is the test
    that does, and which exists because this one was written believing it
    already did.
    """
    b = bridge
    monkeypatch.setattr(tasks, "REDIS_URL", REDIS_URL)
    monkeypatch.setattr(tasks, "create_redis_connection", lambda url: b["r"])

    b["r"].rpush(b["p"], job("run-stranded"))    # left behind by a previous life
    b["r"].rpush(b["q"], job("run-new"))

    t = threading.Thread(target=tasks.run_redis_consumer_forever, daemon=True)
    t.start()

    deadline = time.time() + 10
    while time.time() < deadline and len(b["dispatched"]) < 2:
        time.sleep(0.1)

    ids = sorted(d[0] for d in b["dispatched"])
    assert ids == ["run-new", "run-stranded"], (
        f"the loop dispatched {ids}; the stranded job is the one that proves "
        f"recovery runs at startup"
    )
    assert b["r"].llen(b["p"]) == 0
    assert b["r"].llen(b["q"]) == 0


def test_the_loop_does_not_lose_a_job_it_is_holding(bridge, monkeypatch):
    """
    THE TEST THAT ACTUALLY CATCHES `blpop`, and the reason this file has two
    end-to-end tests instead of one.

    Everything else here either calls `_handle_payload` directly or drives the
    loop to completion. Reverting the loop's `blmove` back to the original
    `blpop` left ALL OF THEM GREEN — because the `_handle_payload` tests do
    their own atomic take in the `take_one` helper (so they were testing Redis,
    not the bridge), and the drain test only observes the loop after it has
    finished, when a destructive take and a non-destructive one look identical.

    Fifth instance of §0.6's "a test you have not seen fail". Found by applying
    the regression, which is the only thing that finds it: the test was written
    with a docstring claiming it proved the take was atomic, and it did not.

    This one parks the loop INSIDE the window. `delay` blocks, so the loop is
    frozen between having taken the item and having dispatched it — exactly
    where a `kill -9` used to destroy the job. While it is parked, the item must
    be findable in Redis. With `blpop` it exists only in a local variable in the
    loop's thread, and both lists are empty.
    """
    b = bridge
    entered = threading.Event()
    release = threading.Event()

    class BlockingDelay:
        def delay(self, *args):
            entered.set()
            release.wait(timeout=10)
            b["dispatched"].append(args)

    monkeypatch.setattr(tasks, "REDIS_URL", REDIS_URL)
    monkeypatch.setattr(tasks, "create_redis_connection", lambda url: b["r"])
    monkeypatch.setattr(tasks, "generate_report", BlockingDelay())

    b["r"].rpush(b["q"], job("run-inflight"))

    t = threading.Thread(target=tasks.run_redis_consumer_forever, daemon=True)
    t.start()
    assert entered.wait(timeout=10), "the loop never reached the dispatch"

    # The loop is now parked mid-window. The job must exist in Redis.
    in_queue = b["r"].llen(b["q"])
    in_processing = b["r"].llen(b["p"])
    try:
        assert in_queue + in_processing == 1, (
            f"the loop is holding a job and Redis has no record of it "
            f"(queue={in_queue}, processing={in_processing}). A crash here "
            f"destroys the report permanently — that is D-037."
        )
        assert in_processing == 1, (
            "the job is not in the processing list; the take was not the "
            "atomic blmove this fix depends on"
        )
    finally:
        release.set()

    deadline = time.time() + 10
    while time.time() < deadline and not b["dispatched"]:
        time.sleep(0.05)
    assert b["dispatched"], "the loop never completed the dispatch after release"
