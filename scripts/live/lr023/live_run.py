"""LR-023 live handoff proof: real Redis, a real Celery worker process, the real
ticker and sweep, real PostgreSQL. Prints a transcript; exits non-zero on the
first broken expectation. Design §8, "Handoff proof".
"""
import json
import os
import signal
import subprocess
import sys
import time
import uuid
from pathlib import Path

HERE = Path(__file__).parent
DB = os.environ["DATABASE_URL"]
REDIS_PORT, SG_PORT = 6391, 8925
os.environ["REDIS_URL"] = f"redis://127.0.0.1:{REDIS_PORT}/0"
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "apps/worker/src"))

import psycopg  # noqa: E402
from worker import schedules_tick  # noqa: E402

schedules_tick.DATABASE_URL = DB
R1, R2 = "live-first@example.com", "live-second@example.com"
procs = {}


def say(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def check(cond, msg):
    if not cond:
        say(f"FAILED: {msg}")
        stop_all()
        sys.exit(1)
    say(f"ok  {msg}")


def q(sql, *p):
    with psycopg.connect(DB, autocommit=True) as c:
        cur = c.execute(sql, p)
        return cur.fetchall() if cur.description else None


def control(**kw):
    (HERE / "control.json").write_text(json.dumps(kw))


def posts():
    f = HERE / "posts.log"
    return [line.split("\t")[0] for line in f.read_text().splitlines()] if f.exists() else []


def redis(up):
    if up:
        subprocess.run(["redis-server", "--port", str(REDIS_PORT), "--save", "", "--appendonly", "no",
                        "--daemonize", "yes"], check=True)
        time.sleep(0.5)
    else:
        subprocess.run(["redis-cli", "-p", str(REDIS_PORT), "shutdown", "nosave"], capture_output=True)
        time.sleep(0.5)


def start_worker(tag):
    env = dict(os.environ, FAKE_SENDGRID_PORT=str(SG_PORT), NO_PROXY="127.0.0.1,localhost",
               no_proxy="127.0.0.1,localhost", PYTHONUNBUFFERED="1")
    log = open(HERE / f"worker-{tag}.log", "w")
    p = subprocess.Popen([sys.executable, str(HERE / "worker_live.py")], env=env, stdout=log, stderr=subprocess.STDOUT)
    procs[f"worker-{tag}"] = p
    for _ in range(60):
        if "ready." in (HERE / f"worker-{tag}.log").read_text():
            return p
        time.sleep(0.5)
    raise SystemExit(f"worker {tag} did not start")


def stop_all():
    for p in procs.values():
        if p.poll() is None:
            p.kill()
    redis(False)


def run_row(run_id):
    cols = ["status", "error", "dispatch_attempts", "dispatched_at", "last_dispatch_error", "owner_token",
            "send_claimed_at", "send_outcomes"]
    return dict(zip(cols, q("SELECT status, error, dispatch_attempts, dispatched_at, last_dispatch_error, "
                            "owner_token::text, send_claimed_at, send_outcomes FROM schedule_runs "
                            "WHERE report_run_id = %s", run_id)[0]))


def wait_for(run_id, statuses, secs=90):
    for _ in range(secs * 2):
        row = run_row(run_id)
        if row["status"] in statuses:
            return row
        time.sleep(0.5)
    return run_row(run_id)


def recipients(schedule, *emails):
    q("UPDATE schedules SET recipients = %s WHERE id = %s",
      [json.dumps({"type": "manual_email", "email": e}) for e in emails], schedule)


def posts_to(*emails):
    return [p for p in posts() if p in emails]


def tick(schedule):
    q("UPDATE schedules SET next_run_at = now() - interval '1 minute', processing_locked_at = NULL WHERE id = %s",
      schedule)
    others = q("SELECT id::text, processing_locked_at FROM schedules WHERE id <> %s AND active "
               "AND (next_run_at IS NULL OR next_run_at <= now())", schedule)
    try:
        for sid, _ in others:
            q("UPDATE schedules SET processing_locked_at = now() WHERE id = %s", sid)
        schedules_tick.process_due_schedules()
    finally:
        for sid, locked in others:
            q("UPDATE schedules SET processing_locked_at = %s WHERE id = %s", locked, sid)
    return q("SELECT report_run_id::text FROM schedule_runs WHERE schedule_id = %s ORDER BY created_at DESC "
             "LIMIT 1", schedule)[0][0]


def age(run_id, **ago):
    for col, minutes in ago.items():
        q(f"UPDATE schedule_runs SET {col} = now() - make_interval(mins => %s) WHERE report_run_id = %s",
          minutes, run_id)


def sweep():
    schedules_tick.sweep_stale_runs()


def main():
    (HERE / "posts.log").unlink(missing_ok=True)
    control(mode="202")
    procs["sendgrid"] = subprocess.Popen([sys.executable, str(HERE / "fake_sendgrid.py"), str(SG_PORT)])
    redis(False)

    tag = uuid.uuid4().hex[:8]
    acct, user, sched = str(uuid.uuid4()), str(uuid.uuid4()), str(uuid.uuid4())
    q("INSERT INTO accounts (id, name, slug, account_type, plan_slug) VALUES (%s, 'LR-023 live', %s, 'REGULAR', 'free')",
      acct, f"lr023-live-{tag}")
    q("INSERT INTO users (id, account_id, email, first_name, last_name, email_verified) "
      "VALUES (%s, %s, %s, 'Live', 'Run', TRUE)", user, acct, f"agent-{tag}@example.com")
    q("INSERT INTO schedules (id, account_id, name, report_type, city, lookback_days, cadence, weekly_dow, send_hour, "
      "send_minute, recipients, active, next_run_at, timezone) VALUES (%s, %s, 'Live Glendora', 'market_snapshot', "
      "'Glendora', 30, 'weekly', 1, 9, 0, %s, TRUE, now(), 'America/Los_Angeles')",
      sched, acct, [json.dumps({"type": "manual_email", "email": e}) for e in (R1, R2)])
    say(f"account {acct}, schedule {sched}")

    say("── 1. Redis is down; the ticker commits the occurrence and the publish fails")
    run1 = tick(sched)
    row = run_row(run1)
    check(row["status"] == "queued" and row["dispatch_attempts"] == 1 and row["dispatched_at"] is None,
          f"run {run1[:8]} is queued, 1 publish attempted, none acknowledged")
    check(bool(row["last_dispatch_error"]), f"the publish failure is recorded: {row['last_dispatch_error'][:90]}")

    say("── 2. Redis comes back; the sweep republishes; one worker runs it once")
    redis(True)
    start_worker("a")
    sweep()
    check(run_row(run1)["dispatch_attempts"] == 1, "a sweep inside 2 minutes does not republish (backoff)")
    age(run1, created_at=3, last_dispatch_at=3)
    sweep()
    row = run_row(run1)
    check(row["dispatch_attempts"] == 2 and row["dispatched_at"] is not None,
          "after 2 minutes the sweep republishes, and the broker acknowledges it")
    row = wait_for(run1, {"completed", "failed", "needs_review"})
    check(row["status"] == "completed", f"the worker completed run {run1[:8]}")
    check(sorted(posts_to(R1, R2)) == sorted([R1, R2]), f"one POST per recipient: {posts_to(R1, R2)}")

    say("── 3. The worker is killed mid-run; the sweep takes over; the redelivery does nothing")
    A3, B3 = "live3-first@example.com", "live3-second@example.com"
    recipients(sched, A3, B3)
    control(mode="202", render_sleep=25)
    run2 = tick(sched)
    for _ in range(60):
        if run_row(run2)["owner_token"]:
            break
        time.sleep(0.5)
    first_owner = run_row(run2)["owner_token"]
    check(bool(first_owner), f"worker A holds the lease on run {run2[:8]}")
    time.sleep(2)
    procs["worker-a"].send_signal(signal.SIGKILL)
    procs["worker-a"].wait()
    say("worker A killed with SIGKILL while rendering")
    control(mode="202")
    start_worker("b")
    say("worker B started; waiting for Redis to hand back A's unacknowledged message (visibility 20 s)")
    for i in range(240):
        if i % 15 == 0:
            r = subprocess.run(["redis-cli", "-p", str(REDIS_PORT), "eval",
                                "return {redis.call('hlen','unacked'), redis.call('zcard','unacked_index'), redis.call('llen','celery')}", "0"],
                               capture_output=True, text=True).stdout.split()
            say(f"redis: unacked={r[0] if r else '?'} unacked_index={r[1] if len(r)>1 else '?'} queue={r[2] if len(r)>2 else '?'}")
        if "not run (duplicate_message)" in (HERE / "worker-b.log").read_text():
            break
        time.sleep(1)
    check("not run (duplicate_message)" in (HERE / "worker-b.log").read_text(),
          "the redelivered message found a live lease and did nothing")
    check(run_row(run2)["status"] == "processing" and run_row(run2)["owner_token"] == first_owner,
          "the run is still processing under worker A's (now dead) lease")
    age(run2, lease_at=7, started_at=7, last_dispatch_at=7)
    sweep()
    check(run_row(run2)["dispatch_attempts"] == 2, "at 6 minutes the sweep republishes the dead owner's run, not fails it")
    row = wait_for(run2, {"completed", "failed", "needs_review"})
    check(row["status"] == "completed" and row["owner_token"] != first_owner,
          "worker B took the lease and completed it")
    check(sorted(posts_to(A3, B3)) == sorted([A3, B3]), f"still one POST per recipient for this run: {posts_to(A3, B3)}")

    say("── 4. SendGrid accepts the first POST and the answer is lost")
    A4, B4 = "live4-first@example.com", "live4-second@example.com"
    recipients(sched, A4, B4)
    control(mode="drop_first")
    run3 = tick(sched)
    row = wait_for(run3, {"completed", "failed", "needs_review"})
    check(row["status"] == "needs_review", f"run {run3[:8]} is needs_review: {row['error'][:110]}")
    outcomes = {o["email"]: o["outcome"] for o in row["send_outcomes"]}
    check(sorted(outcomes.values()) == ["accepted", "unknown"], f"per-recipient outcomes: {outcomes}")
    check(q("SELECT status FROM email_log WHERE report_id = %s", run3) == [("needs_review",)],
          "email_log records needs_review")
    check(sorted(posts_to(A4, B4)) == sorted([A4, B4]), f"one POST per recipient: {posts_to(A4, B4)}")
    before = len(posts_to(A4, B4))
    age(run3, lease_at=60, last_dispatch_at=60)
    sweep()
    time.sleep(25)
    check(len(posts_to(A4, B4)) == before, "nothing was sent again: no further POST after a sweep and 25 s")
    check(len(posts()) == len(posts_to(R1, R2, A3, B3, A4, B4)), f"no POST to anyone outside these runs: {posts()}")
    check(run_row(run3)["status"] == "needs_review", "the run stays needs_review")

    say("ALL STEPS PASSED")
    stop_all()


if __name__ == "__main__":
    try:
        main()
    finally:
        stop_all()
