"""
A committed scheduled send survives a broker failure, and is sent at most once
per recipient (LR-023, D-381; D-332).

Design: docs/plans/launch-readiness-2026-11-06/LR-023_DURABLE_DISPATCH.md, rev 3
(Codex design PASS on #286). Section numbers in the test names refer to it.

Everything runs for real against a database built from every migration: the
ticker (`process_due_schedules`), the worker task (`generate_report`), the
sweep and SendGrid's HTTP client. The outside world is faked at its edges only:
  * the MLS result comes from the report cache (no SimplyRETS);
  * the PDF renderer and R2 upload are stubs;
  * Celery's publish is a recorder (or a failure);
  * SendGrid is a local HTTP server that counts every POST it receives, per
    recipient, and answers 202, a status code, or nothing at all.
"""
import json
import os
import socket
import threading
import time
import uuid
from datetime import timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from test_consumer_failures_are_recorded import db  # noqa: F401  (fixture)

psycopg = pytest.importorskip("psycopg")

R1, R2 = "first@example.com", "second@example.com"

RESULT = {
    "matched": 12,
    "report_type": "market_snapshot",
    "city": "Glendora",
    "counts": {"Active": 12, "Closed": 8, "Pending": 3},
    "metrics": {"median_close_price": 905000, "avg_dom": 21, "months_of_supply": 1.9},
    "total_listings": 12,
    "total_shown": 3,
}


# ── SendGrid at its HTTP boundary ───────────────────────────────────────────

class FakeSendGrid(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self):
        super().__init__(("127.0.0.1", 0), _Handler)
        self.posts = []            # one recipient per POST, in arrival order
        self.behaviour = {}        # recipient -> "202" | "400" | "503" | "drop" | "hang"
        self.hang_seconds = 2.0

    def count(self, email=None):
        return len([p for p in self.posts if email is None or p == email])


class _Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        email = body["personalizations"][0]["to"][0]["email"]
        self.server.posts.append(email)
        how = self.server.behaviour.get(email, "202")
        if len(self.server.posts) == 1 and "__first__" in self.server.behaviour:
            how = self.server.behaviour["__first__"]
        if how == "drop":
            # Read in full, then close with no answer: accepted, answer lost.
            self.close_connection = True
            return
        if how == "hang":
            time.sleep(self.server.hang_seconds)
            self.close_connection = True
            return
        self.send_response(int(how))
        self.send_header("Content-Length", "2")
        self.end_headers()
        self.wfile.write(b"{}")


@pytest.fixture
def sendgrid(monkeypatch):
    from worker.email.providers import sendgrid as provider
    server = FakeSendGrid()
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    monkeypatch.setenv("NO_PROXY", "127.0.0.1,localhost")
    monkeypatch.setenv("no_proxy", "127.0.0.1,localhost")
    monkeypatch.setattr(provider, "SENDGRID_API_URL", f"http://127.0.0.1:{server.server_port}/v3/mail/send")
    monkeypatch.setattr(provider, "SENDGRID_API_KEY", "SG.test-not-a-real-key")
    monkeypatch.setattr(provider, "SENDGRID_TIMEOUT", 1.0)
    monkeypatch.setattr(provider, "RETRY_DELAY_BASE", 0.0)
    yield server
    server.shutdown()
    server.server_close()


# ── the world: one account, one schedule, the task and the ticker ───────────

def _q(db, sql, *params):
    with psycopg.connect(db, autocommit=True) as conn:
        cur = conn.execute(sql, params)
        return cur.fetchall() if cur.description else None


class World:
    def __init__(self, db, tasks, tick, sweep_mod, hooks, published, notices):
        self.db, self.tasks, self.tick_mod, self.sr = db, tasks, tick, sweep_mod
        self.hooks, self.published, self.notices = hooks, published, notices
        self.publish_ok = True
        tag = uuid.uuid4().hex[:8]
        self.account, self.user = str(uuid.uuid4()), str(uuid.uuid4())
        self.schedule = str(uuid.uuid4())
        _q(db, "INSERT INTO accounts (id, name, slug, account_type, plan_slug) "
               "VALUES (%s, 'LR-023 Test', %s, 'REGULAR', 'free')", self.account, f"lr023-{tag}")
        _q(db, "INSERT INTO users (id, account_id, email, first_name, last_name, email_verified) "
               "VALUES (%s, %s, %s, 'Avery', 'Stone', TRUE)", self.user, self.account,
           f"agent-{tag}@example.com")
        _q(db, "INSERT INTO schedules (id, account_id, name, report_type, city, lookback_days, cadence, "
               "weekly_dow, send_hour, send_minute, recipients, active, next_run_at, timezone) "
               "VALUES (%s, %s, 'Weekly Glendora', 'market_snapshot', 'Glendora', 30, 'weekly', "
               "1, 9, 0, %s, TRUE, now() - interval '1 minute', 'America/Los_Angeles')",
           self.schedule, self.account, self.recipients_json(R1, R2))

    @staticmethod
    def recipients_json(*emails):
        return [json.dumps({"type": "manual_email", "email": e}) for e in emails]

    # the ticker, for this schedule only
    def tick(self):
        others = _q(self.db, "SELECT id::text, processing_locked_at FROM schedules "
                             "WHERE id <> %s AND active AND (next_run_at IS NULL OR next_run_at <= now())",
                    self.schedule)
        try:
            # Other due schedules in a shared database are held by the ticker's
            # own lock for the length of this tick, then restored.
            for sid, _ in others:
                _q(self.db, "UPDATE schedules SET processing_locked_at = now() WHERE id = %s", sid)
            self.tick_mod.process_due_schedules()
        finally:
            for sid, locked in others:
                _q(self.db, "UPDATE schedules SET processing_locked_at = %s WHERE id = %s", locked, sid)
        return self.latest_run()

    def latest_run(self):
        rows = _q(self.db, "SELECT report_run_id::text FROM schedule_runs WHERE schedule_id = %s "
                           "ORDER BY created_at DESC LIMIT 1", self.schedule)
        return rows[0][0] if rows else None

    def sweep(self):
        self.tick_mod.sweep_stale_runs()

    def publishes(self, run_id):
        """This run's publishes only: the sweep also republishes rows other tests left."""
        return self.published.count(run_id)

    def deliver(self, run_id):
        """One Celery message for this run, executed in this thread."""
        rt, params = _q(self.db, "SELECT report_type, input_params FROM report_generations "
                                 "WHERE id = %s", run_id)[0]
        return self.tasks.generate_report(run_id, self.account, rt, params)

    def run(self, run_id):
        return dict(zip(
            ["status", "error", "recovery_tracked", "dispatch_attempts", "dispatched_at",
             "owner_token", "lease_at", "send_claimed_at", "send_recipients", "send_outcomes",
             "last_dispatch_error", "created_at"],
            _q(self.db, "SELECT status, error, recovery_tracked, dispatch_attempts, dispatched_at, "
                        "owner_token::text, lease_at, send_claimed_at, send_recipients, send_outcomes, "
                        "last_dispatch_error, created_at FROM schedule_runs WHERE report_run_id = %s",
               run_id)[0]))

    def generation(self, run_id):
        return _q(self.db, "SELECT status, pdf_url, input_params FROM report_generations WHERE id = %s",
                  run_id)[0]

    def email_log(self, run_id):
        return _q(self.db, "SELECT status FROM email_log WHERE report_id = %s ORDER BY created_at", run_id)

    def shift(self, run_id, **ago):
        """Move timestamps into the past, as if that much time had gone by."""
        for col, delta in ago.items():
            _q(self.db, f"UPDATE schedule_runs SET {col} = now() - %s WHERE report_run_id = %s",
               delta, run_id)


@pytest.fixture
def world(db, monkeypatch, tmp_path, sendgrid):
    from worker import tasks, schedules_tick, scheduled_runs
    import worker.market_builder as market_builder

    hooks, published, notices = {}, [], []
    monkeypatch.setattr(tasks, "DATABASE_URL", db)
    monkeypatch.setattr(schedules_tick, "DATABASE_URL", db)
    monkeypatch.setattr(tasks, "cache_get", lambda *a, **k: dict(RESULT))
    monkeypatch.setattr(tasks, "cache_set", lambda *a, **k: None)
    monkeypatch.setattr(tasks, "proxy_report_photos_inplace", lambda *a, **k: None)
    monkeypatch.setattr(tasks, "embed_images_as_base64", lambda html: html)
    monkeypatch.setattr(tasks, "_deliver_webhooks", lambda *a, **k: None)
    monkeypatch.setattr(tasks, "_send_failure_notification", lambda **k: notices.append(k))

    class Builder:
        def __init__(self, data):
            self.data = data

        def render_html(self):
            return "<html><body>report</body></html>"

        def render_page_header_html(self):
            return ""

        def render_page_footer_html(self):
            return ""
    monkeypatch.setattr(market_builder, "MarketReportBuilder", Builder)

    def render(run_id, **kw):
        if "render" in hooks:
            hooks["render"](run_id)
        path = tmp_path / f"{run_id}.pdf"
        path.write_bytes(b"%PDF-1.4 test")
        return str(path), None
    monkeypatch.setattr(tasks, "render_pdf", render)
    monkeypatch.setattr(tasks, "upload_to_r2", lambda path, key, *a, **k: f"https://r2.test/{key}")

    w = World(db, tasks, schedules_tick, scheduled_runs, hooks, published, notices)

    def dispatch(run_id, account_id, report_type, params, schedule_id):
        published.append(run_id)
        if not w.publish_ok:
            return None, "OperationalError: Error 111 connecting to redis:6379. Connection refused."
        return f"task-{len(published)}", None
    monkeypatch.setattr(schedules_tick, "dispatch_report", dispatch)
    return w


# ── §2 the legacy boundary ──────────────────────────────────────────────────

@pytest.mark.parametrize("age", [timedelta(minutes=45), timedelta(hours=7)])
def test_a_legacy_queued_row_is_never_republished_or_leased(world, age):
    """Rows the new ticker did not write keep today's path exactly (AMEND 1)."""
    run_id = world.tick()
    _q(world.db, "UPDATE schedule_runs SET recovery_tracked = FALSE, created_at = now() - %s "
                 "WHERE report_run_id = %s", age, run_id)
    published_before = world.publishes(run_id)
    world.sweep()
    row = world.run(run_id)
    assert world.publishes(run_id) == published_before, "a legacy row was republished"
    assert row["status"] == "failed" and row["error"].startswith("never picked up"), row
    assert row["owner_token"] is None


def test_a_legacy_row_inside_its_window_is_left_alone(world):
    """
    Five minutes old and never acknowledged: the legacy sweep leaves it (its
    window is 30 minutes), and a tracked row in that state WOULD be republished
    (case a). So only the marker keeps the tracked sweep off it.
    """
    run_id = world.tick()
    _q(world.db, "UPDATE schedule_runs SET recovery_tracked = FALSE, dispatched_at = NULL, "
                 "created_at = now() - interval '5 minutes', last_dispatch_at = now() - interval '5 minutes' "
                 "WHERE report_run_id = %s", run_id)
    published_before = world.publishes(run_id)
    world.sweep()
    row = world.run(run_id)
    assert row["status"] == "queued" and row["dispatch_attempts"] == 1, row
    assert world.publishes(run_id) == published_before, "a legacy row was republished"
    assert not world.sr.is_tracked(world.db, run_id)


# ── §3 publishing ───────────────────────────────────────────────────────────

def test_the_ticker_writes_a_tracked_occurrence_and_records_the_acknowledgement(world):
    run_id = world.tick()
    row = world.run(run_id)
    assert row["recovery_tracked"] and row["status"] == "queued"
    assert row["dispatch_attempts"] == 1 and row["dispatched_at"] is not None
    assert world.publishes(run_id) == 1


def test_a_failed_publish_is_republished_by_the_sweep_and_then_sent_once(world, sendgrid):
    world.publish_ok = False
    run_id = world.tick()
    row = world.run(run_id)
    assert row["status"] == "queued" and row["dispatched_at"] is None
    assert "Connection refused" in row["last_dispatch_error"]

    world.sweep()                                     # under 2 minutes: too soon
    assert world.run(run_id)["dispatch_attempts"] == 1
    world.publish_ok = True
    world.shift(run_id, created_at=timedelta(minutes=3), last_dispatch_at=timedelta(minutes=3))
    world.sweep()
    row = world.run(run_id)
    assert row["dispatch_attempts"] == 2 and row["dispatched_at"] is not None
    assert world.publishes(run_id) == 2

    world.deliver(run_id)
    assert world.run(run_id)["status"] == "completed"
    assert (sendgrid.count(R1), sendgrid.count(R2)) == (1, 1)
    assert world.email_log(run_id) == [("sent",)]


def test_a_publish_whose_acknowledgement_was_lost_makes_two_messages_and_one_send(world, sendgrid):
    run_id = world.tick()
    _q(world.db, "UPDATE schedule_runs SET dispatched_at = NULL WHERE report_run_id = %s", run_id)
    world.shift(run_id, created_at=timedelta(minutes=3), last_dispatch_at=timedelta(minutes=3))
    world.sweep()
    assert world.publishes(run_id) == 2
    first = world.deliver(run_id)
    second = world.deliver(run_id)
    assert first["ok"] and second == {"ok": False, "reason": "duplicate_message", "run_id": run_id}
    assert sendgrid.count() == 2, sendgrid.posts      # one per recipient, once


def _state(world, run_id, **over):
    row = world.run(run_id)
    now = _q(world.db, "SELECT now()")[0][0]
    base = dict(id="x", run_id=run_id, status=row["status"], created_at=now - timedelta(minutes=10),
                lease_at=None, owner_token=None, send_claimed_at=None, dispatched_at=None,
                dispatch_attempts=1, last_dispatch_at=now, schedule_id="s", schedule_active=True,
                account_id="a", account_active=True, can_send=True, recipients=[],
                report_type="market_snapshot", params={}, now=now)
    base.update(over)
    return world.sr.RunState(**base)


@pytest.mark.parametrize("attempts,wait", [(1, 2), (2, 4), (3, 8), (4, 16), (5, 16)])
def test_backoff_is_2_4_8_16_minutes_capped(world, attempts, wait):
    run_id = world.tick()
    now = _q(world.db, "SELECT now()")[0][0]
    just_before = _state(world, run_id, dispatch_attempts=attempts,
                         last_dispatch_at=now - timedelta(minutes=wait) + timedelta(seconds=5))
    just_after = _state(world, run_id, dispatch_attempts=attempts,
                        last_dispatch_at=now - timedelta(minutes=wait, seconds=1))
    assert world.sr.sweep_decision(just_before) is None
    assert world.sr.sweep_decision(just_after) == ("republish", "a")


def test_the_sixth_publish_is_allowed_and_the_seventh_refused(world):
    run_id = world.tick()
    old = timedelta(minutes=20)
    world.shift(run_id, created_at=old, last_dispatch_at=old)
    _q(world.db, "UPDATE schedule_runs SET dispatched_at = NULL, dispatch_attempts = 5 "
                 "WHERE report_run_id = %s", run_id)
    world.sweep()
    assert world.run(run_id)["dispatch_attempts"] == 6, "the 6th publish was refused"
    world.shift(run_id, last_dispatch_at=old)
    _q(world.db, "UPDATE schedule_runs SET dispatched_at = NULL WHERE report_run_id = %s", run_id)
    world.sweep()
    row = world.run(run_id)
    assert row["dispatch_attempts"] == 6, "a 7th publish was made"
    assert row["status"] == "failed" and "6 attempts" in row["error"], row


def test_concurrent_sweeps_never_take_the_same_row(world):
    run_id = world.tick()
    world.shift(run_id, created_at=timedelta(minutes=5), last_dispatch_at=timedelta(minutes=5))
    _q(world.db, "UPDATE schedule_runs SET dispatched_at = NULL WHERE report_run_id = %s", run_id)
    holder = psycopg.connect(world.db)
    holder.execute("SELECT 1 FROM schedule_runs WHERE report_run_id = %s FOR UPDATE", (run_id,))
    try:
        sweeping = threading.Thread(target=world.sweep, daemon=True)
        sweeping.start()
        sweeping.join(10)
        assert not sweeping.is_alive(), "the sweep waited on a row another ticker holds"
        assert world.run(run_id)["dispatch_attempts"] == 1
    finally:
        holder.rollback()
        holder.close()
    sweeping.join(30)
    world.sweep()
    assert world.run(run_id)["dispatch_attempts"] == 2


# ── §4 the lease ────────────────────────────────────────────────────────────

def test_two_simultaneous_stale_takeovers_have_exactly_one_winner(world):
    run_id = world.tick()
    _q(world.db, "UPDATE schedule_runs SET status = 'processing', owner_token = gen_random_uuid(), "
                 "lease_at = now() - interval '7 minutes', started_at = now() - interval '7 minutes' "
                 "WHERE report_run_id = %s", run_id)
    barrier, out = threading.Barrier(2, timeout=30), []

    def take():
        barrier.wait()
        out.append(world.sr.take_lease(world.db, run_id))
    threads = [threading.Thread(target=take) for _ in range(2)]
    [t.start() for t in threads]
    [t.join(30) for t in threads]
    tokens = [t for t, _ in out if t]
    assert len(tokens) == 1, out
    assert world.run(run_id)["owner_token"] == tokens[0]


def test_a_duplicate_message_writes_nothing_at_all(world, sendgrid):
    run_id = world.tick()
    token, _ = world.sr.take_lease(world.db, run_id)            # a live owner
    before = world.generation(run_id), world.run(run_id)
    result = world.deliver(run_id)
    assert result["reason"] == "duplicate_message"
    assert (world.generation(run_id), world.run(run_id)) == before
    assert sendgrid.count() == 0


def test_a_superseded_owner_writes_nothing_and_sends_nothing(world, sendgrid):
    run_id = world.tick()

    def steal(_run_id):
        _q(world.db, "UPDATE schedule_runs SET owner_token = gen_random_uuid(), lease_at = now() "
                     "WHERE report_run_id = %s", run_id)
    world.hooks["render"] = steal
    result = world.deliver(run_id)
    assert result["reason"] == "superseded", result
    status, pdf_url, _ = world.generation(run_id)
    assert status == "processing" and pdf_url is None, "a superseded owner completed the report"
    assert world.run(run_id)["status"] == "processing"
    assert sendgrid.count() == 0 and world.notices == []


def test_the_sweep_at_six_minutes_republishes_a_dead_owner_and_does_not_fail_it(world, sendgrid):
    run_id = world.tick()
    world.sr.take_lease(world.db, run_id)                       # the owner dies here
    world.shift(run_id, started_at=timedelta(minutes=7), lease_at=timedelta(minutes=7),
                last_dispatch_at=timedelta(minutes=7))
    world.sweep()
    row = world.run(run_id)
    assert row["status"] == "processing" and row["dispatch_attempts"] == 2, row
    world.deliver(run_id)                                       # the republished message
    assert world.run(run_id)["status"] == "completed"
    late = world.deliver(run_id)                                # acks_late redelivery at t+15
    assert late["reason"] == "duplicate_message"
    assert sendgrid.count() == 2


def test_the_redelivery_at_fifteen_minutes_takes_a_stale_lease_when_no_sweep_ran(world, sendgrid):
    run_id = world.tick()
    world.sr.take_lease(world.db, run_id)
    world.shift(run_id, lease_at=timedelta(minutes=15))
    assert world.deliver(run_id)["ok"]
    assert world.run(run_id)["status"] == "completed" and sendgrid.count() == 2


def test_a_live_owner_refreshing_its_lease_is_never_taken_over(world):
    run_id = world.tick()
    token, _ = world.sr.take_lease(world.db, run_id)
    world.shift(run_id, lease_at=timedelta(minutes=5))
    world.sr.refresh_lease(world.db, run_id, token)
    world.sweep()
    assert world.sr.take_lease(world.db, run_id) == (None, "duplicate_message")
    assert world.run(run_id)["owner_token"] == token


def test_every_owner_write_is_conditioned_on_its_token(world):
    """After a takeover, the old owner's writes match nothing, report_generations included."""
    run_id = world.tick()
    old, _ = world.sr.take_lease(world.db, run_id)
    world.shift(run_id, lease_at=timedelta(minutes=7))
    new, _ = world.sr.take_lease(world.db, run_id)
    assert old and new and old != new
    assert world.sr.finish(world.db, run_id, old, "completed", None) is False
    with psycopg.connect(world.db, autocommit=True) as conn:
        assert world.sr.finish_after_error(conn.cursor(), run_id, old, "failed", "x") is None
        cur = conn.execute("UPDATE report_generations SET status = 'completed' WHERE id = %s"
                           + world.sr.OWNED, (run_id, *world.sr.owned(run_id, old)))
        assert cur.rowcount == 0
    assert world.sr.claim_send(world.db, run_id, old, [R1]) == world.sr.REFUSED
    with pytest.raises(world.sr.Superseded):
        world.sr.refresh_lease(world.db, run_id, old)
    row = world.run(run_id)
    assert row["status"] == "processing" and row["owner_token"] == new and row["send_claimed_at"] is None


# ── §5 delivery at the HTTP transport boundary ──────────────────────────────

def test_accepted_then_the_answer_lost_is_needs_review_and_never_resent(world, sendgrid):
    sendgrid.behaviour["__first__"] = "drop"      # whichever recipient goes first
    run_id = world.tick()
    world.deliver(run_id)
    row = world.run(run_id)
    assert row["status"] == "needs_review", row
    assert world.email_log(run_id) == [("needs_review",)]
    assert (sendgrid.count(R1), sendgrid.count(R2)) == (1, 1)
    assert world.notices == [], "a 'didn't go out' email for a send that may have gone out"
    assert world.deliver(run_id)["reason"] == "duplicate_message"
    world.shift(run_id, lease_at=timedelta(hours=1), last_dispatch_at=timedelta(hours=1))
    world.sweep()
    assert sendgrid.count() == 2, sendgrid.posts


def test_a_read_timeout_is_needs_review_with_one_post(world, sendgrid):
    sendgrid.behaviour[R1] = "hang"
    run_id = world.tick()
    world.deliver(run_id)
    assert world.run(run_id)["status"] == "needs_review"
    assert sendgrid.count(R1) == 1
    world.deliver(run_id)
    assert sendgrid.count(R1) == 1


def test_a_503_is_one_post_on_the_tracked_path_and_four_on_the_legacy_one(world, sendgrid):
    sendgrid.behaviour[R1] = "503"
    run_id = world.tick()
    world.deliver(run_id)
    assert world.run(run_id)["status"] == "needs_review"
    assert sendgrid.count(R1) == 1
    from worker.email.providers.sendgrid import send_email
    code, _ = send_email([R1], "legacy", "<p>legacy</p>")
    assert code == 503 and sendgrid.count(R1) == 1 + 4, "the legacy path's retries changed"


def test_an_unknown_outcome_wins_over_a_rejection(world, sendgrid):
    sendgrid.behaviour.update({R1: "400", R2: "drop"})
    run_id = world.tick()
    world.deliver(run_id)
    row = world.run(run_id)
    assert row["status"] == "needs_review", row
    outcomes = {o["email"]: o["outcome"] for o in row["send_outcomes"]}
    assert outcomes == {R1: "rejected", R2: "unknown"}
    assert sorted(row["send_recipients"]) == [R1, R2]
    assert (sendgrid.count(R1), sendgrid.count(R2)) == (1, 1)


def test_a_definite_rejection_is_failed_and_not_resent(world, sendgrid):
    sendgrid.behaviour.update({R1: "400", R2: "403"})
    run_id = world.tick()
    world.deliver(run_id)
    row = world.run(run_id)
    assert row["status"] == "failed" and row["error"].startswith("failed_email: 2 of 2"), row
    assert world.email_log(run_id) == [("failed",)]
    world.deliver(run_id)
    assert sendgrid.count() == 2


def test_a_refused_connection_is_not_sent_and_failed(world, sendgrid, monkeypatch):
    from worker.email.providers import sendgrid as provider
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        closed_port = s.getsockname()[1]
    monkeypatch.setattr(provider, "SENDGRID_API_URL", f"http://127.0.0.1:{closed_port}/v3/mail/send")
    run_id = world.tick()
    world.deliver(run_id)
    row = world.run(run_id)
    assert row["status"] == "failed", row
    assert {o["outcome"] for o in row["send_outcomes"]} == {"not_sent"}
    assert sendgrid.count() == 0


def test_the_claim_is_taken_after_the_render_and_a_render_failure_leaves_none(world, sendgrid):
    run_id = world.tick()

    def boom(_):
        raise RuntimeError("renderer unavailable")
    world.hooks["render"] = boom
    world.deliver(run_id)
    row = world.run(run_id)
    assert row["status"] == "failed" and row["send_claimed_at"] is None
    assert sendgrid.count() == 0 and len(world.notices) == 1


class WorkerDied(BaseException):
    """Not an Exception: nothing in the task catches it, like a killed process."""


def test_a_worker_that_dies_mid_loop_is_needs_review_and_the_rest_are_never_sent(world, sendgrid, monkeypatch):
    run_id = world.tick()

    def die(*a, **k):
        raise WorkerDied()
    monkeypatch.setattr(world.sr, "append_outcome", die)
    monkeypatch.setattr(world.tasks.scheduled_runs, "append_outcome", die)
    from worker.email import send as send_mod
    real = send_mod._send_each_once

    def once_then_die(account_id, recipients, subject, html, claim, on_attempt):
        def hook(email, attempt):
            raise WorkerDied()
        return real(account_id, recipients, subject, html, claim, hook)
    monkeypatch.setattr(send_mod, "_send_each_once", once_then_die)
    with pytest.raises(WorkerDied):
        world.deliver(run_id)
    first = world.run(run_id)["send_recipients"][0]
    assert sendgrid.posts == [first]
    assert world.run(run_id)["send_claimed_at"] is not None
    world.shift(run_id, lease_at=timedelta(minutes=7))
    assert world.deliver(run_id)["reason"] == "needs_review"    # the redelivery settles it
    assert world.run(run_id)["status"] == "needs_review"
    world.sweep()
    assert sendgrid.posts == [first], "the second recipient was sent after a claimed death"


def test_a_dead_claimed_run_is_needs_review_through_the_sweep_too(world, sendgrid):
    run_id = world.tick()
    token, _ = world.sr.take_lease(world.db, run_id)
    assert world.sr.claim_send(world.db, run_id, token, [R1, R2]) == world.sr.CLAIMED
    world.shift(run_id, lease_at=timedelta(minutes=7), last_dispatch_at=timedelta(minutes=7))
    world.sweep()
    assert world.run(run_id)["status"] == "needs_review"
    assert sendgrid.count() == 0


def _failing_claim_db(world, monkeypatch, *, commit_then_fail):
    """claim_send's own connection fails: before anything, or after its COMMIT."""
    real_connect = psycopg.connect
    real_claim = world.sr.claim_send

    class LostAnswer:
        def __init__(self, conn):
            self._c = conn

        def __getattr__(self, n):
            return getattr(self._c, n)

        def __enter__(self):
            self._c.__enter__()
            return self

        def __exit__(self, *e):
            return self._c.__exit__(*e)

        def commit(self):
            self._c.commit()
            raise psycopg.OperationalError("server closed the connection unexpectedly")

    def connect(*a, **k):
        if not commit_then_fail:
            raise psycopg.OperationalError("connection refused")
        return LostAnswer(real_connect(*a, **k))

    def claim(*a, **k):
        monkeypatch.setattr(world.sr.psycopg, "connect", connect)
        try:
            return real_claim(*a, **k)
        finally:
            monkeypatch.setattr(world.sr.psycopg, "connect", real_connect)
    monkeypatch.setattr(world.sr, "claim_send", claim)


def test_a_claim_that_cannot_be_written_sends_nothing_and_is_recovered(world, sendgrid, monkeypatch):
    run_id = world.tick()
    _failing_claim_db(world, monkeypatch, commit_then_fail=False)
    world.deliver(run_id)
    row = world.run(run_id)
    assert sendgrid.count() == 0 and row["send_claimed_at"] is None
    assert row["status"] == "processing", "nothing is written after a failed claim"
    monkeypatch.undo()


def test_a_claim_whose_commit_answer_was_lost_is_needs_review_and_never_sent(world, sendgrid, monkeypatch):
    """Codex, design PASS: the persisted send_claimed_at is the authority, not the exception."""
    run_id = world.tick()
    _failing_claim_db(world, monkeypatch, commit_then_fail=True)
    world.deliver(run_id)
    row = world.run(run_id)
    assert sendgrid.count() == 0
    assert row["send_claimed_at"] is not None and row["status"] == "processing", row
    world.shift(run_id, lease_at=timedelta(minutes=7), last_dispatch_at=timedelta(minutes=7))
    world.sweep()
    assert world.run(run_id)["status"] == "needs_review"
    assert sendgrid.count() == 0


def test_a_failed_duplicate_lookup_and_journal_still_send_exactly_once(world, sendgrid, monkeypatch):
    def no_log_db():
        raise psycopg.OperationalError("log database unavailable")
    monkeypatch.setattr(world.tasks, "_open_log_connection", no_log_db)
    run_id = world.tick()
    world.deliver(run_id)
    assert world.run(run_id)["status"] == "completed"
    assert (sendgrid.count(R1), sendgrid.count(R2)) == (1, 1)


def test_a_failed_outcome_append_does_not_stop_the_loop(world, sendgrid, monkeypatch):
    def fail(*a, **k):
        raise psycopg.OperationalError("append failed")
    monkeypatch.setattr(world.sr, "append_outcome", fail)
    run_id = world.tick()
    world.deliver(run_id)
    assert world.run(run_id)["status"] == "completed"
    assert (sendgrid.count(R1), sendgrid.count(R2)) == (1, 1)


def test_a_failed_outcome_write_after_202s_is_needs_review_and_not_resent(world, sendgrid, monkeypatch):
    def fail(*a, **k):
        raise psycopg.OperationalError("outcome write failed")
    monkeypatch.setattr(world.sr, "finish", fail)
    run_id = world.tick()
    world.deliver(run_id)
    row = world.run(run_id)
    assert row["status"] == "needs_review", row
    assert world.notices == []
    assert world.generation(run_id)[0] == "completed", "the report itself was marked failed"
    monkeypatch.undo()
    world.deliver(run_id)
    assert sendgrid.count() == 2


def test_a_suppression_lookup_error_sends_nothing_and_a_republish_sends_to_the_filtered_list(
        world, sendgrid, monkeypatch):
    from worker.email import send as send_mod
    real = send_mod.send_schedule_email

    def broken_db(*a, **k):
        class Conn:
            def cursor(self):
                raise psycopg.OperationalError("suppressions unavailable")
        k["db_conn"] = Conn()
        return real(*a, **k)
    monkeypatch.setattr(world.tasks, "send_schedule_email", broken_db)
    run_id = world.tick()
    world.deliver(run_id)
    row = world.run(run_id)
    assert sendgrid.count() == 0 and row["send_claimed_at"] is None and row["status"] == "processing"

    monkeypatch.setattr(world.tasks, "send_schedule_email", real)
    _q(world.db, "INSERT INTO email_suppressions (account_id, email, reason) VALUES (%s, %s, 'unsubscribe')",
       world.account, R2)
    world.shift(run_id, lease_at=timedelta(minutes=7), last_dispatch_at=timedelta(minutes=7))
    world.sweep()
    world.deliver(run_id)
    assert world.run(run_id)["status"] == "completed"
    assert sendgrid.posts == [R1]


# ── §4/§5 eligibility over time, with no sweep in between ──────────────────

def test_a_message_delivered_after_the_horizon_is_expired(world, sendgrid):
    run_id = world.tick()
    world.shift(run_id, created_at=timedelta(hours=6, seconds=1))
    assert world.deliver(run_id)["reason"] == "expired"
    assert world.run(run_id)["status"] == "expired"
    assert world.generation(run_id)[0] == "failed"
    assert sendgrid.count() == 0


def test_the_lease_boundary_is_six_hours_from_the_occurrence(world):
    run_id = world.tick()
    world.shift(run_id, created_at=timedelta(hours=6) - timedelta(seconds=3))
    token, outcome = world.sr.take_lease(world.db, run_id)
    assert token and outcome == "leased"


def test_the_horizon_crossed_between_the_lease_and_the_send_claim_is_expired_with_no_post(world, sendgrid):
    """Rev 2 AMEND 1: a valid lease, then the render runs past 6 h. No sweep."""
    run_id = world.tick()
    world.shift(run_id, created_at=timedelta(hours=6) - timedelta(seconds=10))

    def cross(_):
        world.shift(run_id, created_at=timedelta(hours=6, seconds=1))
    world.hooks["render"] = cross
    world.deliver(run_id)
    row = world.run(run_id)
    assert row["status"] == "expired" and row["send_claimed_at"] is None, row
    assert sendgrid.count() == 0
    assert world.generation(run_id)[0] == "completed", "the report exists; it was not sent"


def test_the_send_claim_just_inside_the_horizon_sends(world, sendgrid):
    run_id = world.tick()
    world.hooks["render"] = lambda _: world.shift(run_id, created_at=timedelta(hours=6) - timedelta(seconds=3))
    world.deliver(run_id)
    assert world.run(run_id)["status"] == "completed" and sendgrid.count() == 2


def test_a_row_made_terminal_after_the_lease_is_never_claimed(world, sendgrid, monkeypatch):
    """Settled after the report completed, so only the send claim stands in the way."""
    run_id = world.tick()
    real = world.tasks.resolve_recipients_to_emails

    def settle_then_resolve(*a, **k):
        _q(world.db, "UPDATE schedule_runs SET status = 'failed' WHERE report_run_id = %s", run_id)
        return real(*a, **k)
    monkeypatch.setattr(world.tasks, "resolve_recipients_to_emails", settle_then_resolve)
    world.deliver(run_id)
    row = world.run(run_id)
    assert row["status"] == "failed" and row["send_claimed_at"] is None
    assert sendgrid.count() == 0


def test_a_schedule_paused_before_the_message_runs_is_cancelled(world, sendgrid):
    run_id = world.tick()
    _q(world.db, "UPDATE schedules SET active = FALSE WHERE id = %s", world.schedule)
    assert world.deliver(run_id)["reason"] == "cancelled"
    assert world.run(run_id)["error"] == world.sr.MSG_PAUSED
    assert sendgrid.count() == 0


def test_a_schedule_paused_during_the_render_is_cancelled_at_the_send_claim(world, sendgrid):
    run_id = world.tick()
    world.hooks["render"] = lambda _: _q(world.db, "UPDATE schedules SET active = FALSE WHERE id = %s",
                                         world.schedule)
    world.deliver(run_id)
    row = world.run(run_id)
    assert row["status"] == "cancelled" and row["send_claimed_at"] is None
    assert sendgrid.count() == 0


def test_a_deactivated_account_is_cancelled(world, sendgrid):
    run_id = world.tick()
    _q(world.db, "UPDATE accounts SET is_active = FALSE WHERE id = %s", world.account)
    assert world.deliver(run_id)["reason"] == "cancelled"
    assert world.run(run_id)["error"] == world.sr.MSG_DEACTIVATED
    assert sendgrid.count() == 0


def test_a_sender_who_loses_verification_is_blocked_with_the_refusal_logged(world, sendgrid):
    run_id = world.tick()
    _q(world.db, "UPDATE users SET email_verified = FALSE WHERE id = %s", world.user)
    assert world.deliver(run_id)["reason"] == "blocked_unverified"
    refusals = _q(world.db, "SELECT status FROM email_log WHERE schedule_id = %s AND status = 'blocked_unverified'",
                  world.schedule)
    assert refusals == [("blocked_unverified",)]
    assert sendgrid.count() == 0


def test_recipients_changed_before_a_republish_get_it(world, sendgrid):
    run_id = world.tick()
    _q(world.db, "UPDATE schedules SET recipients = %s WHERE id = %s",
       World.recipients_json("third@example.com"), world.schedule)
    world.deliver(run_id)
    assert sendgrid.posts == ["third@example.com"]
    assert world.run(run_id)["send_recipients"] == ["third@example.com"]


def test_a_recipient_who_unsubscribes_before_the_send_is_not_sent(world, sendgrid):
    run_id = world.tick()
    _q(world.db, "INSERT INTO email_suppressions (account_id, email, reason) VALUES (%s, %s, 'unsubscribe')",
       world.account, R1)
    world.deliver(run_id)
    assert sendgrid.posts == [R2]


# ── D-332: the manual allowance never stops a schedule ─────────────────────

def test_an_exhausted_manual_allowance_never_stops_or_counts_a_scheduled_send(world, sendgrid, monkeypatch):
    from worker import limit_checker
    before = limit_checker.check_usage_limit(world.account, product="market_reports")
    monkeypatch.setattr(limit_checker, "check_usage_limit",
                        lambda *a, **k: pytest.fail("the manual allowance was consulted"))
    run_id = world.tick()
    world.deliver(run_id)
    assert world.run(run_id)["status"] == "completed" and sendgrid.count() == 2
    monkeypatch.undo()
    after = limit_checker.check_usage_limit(world.account, product="market_reports")
    assert after.get("used") == before.get("used"), (before, after)
