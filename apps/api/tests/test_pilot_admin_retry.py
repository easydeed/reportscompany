from concurrent.futures import ThreadPoolExecutor
from threading import Event
from unittest.mock import Mock
from uuid import uuid4

from fastapi import HTTPException
import psycopg
from psycopg.types.json import Jsonb
import pytest

from api.routes import admin
from api.worker_client import celery_app
from worker import market_builder, scheduled_runs, tasks


@pytest.fixture
def generation(db_session, monkeypatch, tmp_path):
    monkeypatch.setenv("ADMIN_GENERATION_RETRY_ENABLED", "1")
    account, report = str(uuid4()), str(uuid4())
    params = {"city": "Irvine", "send_email": False, "recipients": []}

    def query(sql, *args):
        with psycopg.connect(db_session) as conn:
            cur = conn.execute(sql, args)
            return cur.fetchone() if cur.description else None

    query("INSERT INTO accounts (id,name,slug) VALUES (%s,'D-396',%s)", account, account)
    query("""INSERT INTO report_generations (id,account_id,report_type,status,input_params)
             VALUES (%s,%s,'market_snapshot','failed',%s)""", report, account, Jsonb(params))
    publish = Mock()
    render = Mock(return_value=(str(tmp_path / "generated.pdf"), None))
    monkeypatch.setattr(celery_app, "send_task", publish)
    monkeypatch.setattr(tasks, "DATABASE_URL", db_session)
    monkeypatch.setattr(tasks, "cache_get", lambda *args: {"matched": 1})
    monkeypatch.setattr(tasks, "proxy_report_photos_inplace", lambda *a, **kw: None)
    monkeypatch.setattr(market_builder, "MarketReportBuilder", Mock(return_value=Mock(
        render_html=lambda: "body", render_page_header_html=lambda: "", render_page_footer_html=lambda: "")))
    monkeypatch.setattr(tasks, "embed_images_as_base64", lambda html: html)
    monkeypatch.setattr(tasks, "render_pdf", render)
    monkeypatch.setattr(tasks, "upload_to_r2", lambda *a: "https://example.test/report.pdf")
    monkeypatch.setattr(tasks, "send_schedule_email", lambda *a, **k: pytest.fail("email delivery"))
    monkeypatch.setattr(tasks, "_deliver_webhooks", lambda *a: pytest.fail("duplicate webhook"))

    def retry():
        return admin.retry_market_report(report, {"account_id": account})

    def deliver(attempt=None):
        if attempt is None:
            return tasks.generate_report(report, account, "market_snapshot", params)
        call = publish.call_args_list[attempt - 1]
        assert call.args == ("generate_report",)
        return tasks.generate_report(*call.kwargs["args"], **call.kwargs["kwargs"])

    def age_request():
        query("""UPDATE report_generations SET additional_params=jsonb_set(additional_params,
                 '{admin_generation_retry,requested_at}', to_jsonb(now()-interval '2 minutes'))
                 WHERE id=%s""", report)

    try:
        yield retry, deliver, publish, render, query, report, age_request
    finally:
        query("DELETE FROM email_log WHERE report_id=%s", report)
        query("DELETE FROM report_generations WHERE id=%s", report)
        query("DELETE FROM accounts WHERE id=%s", account)


@pytest.mark.parametrize("original_first", [True, False])
def test_lost_ack_delayed_original_and_duplicate_retry(generation, original_first):
    retry, deliver, publish, render, query, report, _ = generation
    publish.side_effect = ConnectionError("acknowledgement lost")
    with pytest.raises(HTTPException) as unknown:
        retry()
    assert unknown.value.status_code == 503
    assert query("SELECT status FROM report_generations WHERE id=%s", report) == ("retry_pending",)
    if original_first:
        assert deliver()["reason"] == "superseded_retry"
    with ThreadPoolExecutor(2) as pool:
        outcomes = list(pool.map(deliver, [1, 1]))
    assert sorted(outcome["ok"] for outcome in outcomes) == [False, True]
    assert deliver()["reason"] == "superseded_retry"
    assert query("SELECT status FROM report_generations WHERE id=%s", report) == ("completed",)
    render.assert_called_once()


def test_interrupted_retry_recovers_after_worker_releases_ownership(generation, monkeypatch):
    retry, deliver, _, render, query, report, age = generation
    entered, release = Event(), Event()

    class WorkerLost(BaseException):
        pass

    def interrupt(*args):
        entered.set()
        assert release.wait(10)
        raise WorkerLost()

    assert retry()["status"] == "queued"
    with monkeypatch.context() as m, ThreadPoolExecutor(1) as pool:
        m.setattr(tasks, "cache_get", interrupt)
        future = pool.submit(deliver, 1)
        try:
            assert entered.wait(10)
            age()
            with pytest.raises(HTTPException, match="already generating"):
                retry()
        finally:
            release.set()
        with pytest.raises(WorkerLost):
            future.result()
    assert query("SELECT status FROM report_generations WHERE id=%s", report) == ("processing",)
    assert retry()["status"] == "queued"
    assert deliver(1)["reason"] == deliver()["reason"] == "superseded_retry"
    assert deliver(2)["ok"]
    render.assert_called_once()


def test_original_already_working_blocks_operator_retry(generation, monkeypatch):
    retry, deliver, publish, render, _, _, _ = generation
    entered, release = Event(), Event()

    def working(*args):
        entered.set()
        assert release.wait(10)
        return {"matched": 1}

    monkeypatch.setattr(tasks, "cache_get", working)
    monkeypatch.setattr(tasks, "_deliver_webhooks", Mock())
    with ThreadPoolExecutor(1) as pool:
        future = pool.submit(deliver)
        try:
            assert entered.wait(10)
            with pytest.raises(HTTPException, match="processing"):
                retry()
        finally:
            release.set()
        assert future.result()["ok"]
    publish.assert_not_called()
    render.assert_called_once()


def test_publication_ack_does_not_overwrite_fast_completion(generation):
    retry, _, publish, render, query, report, _ = generation
    # Normal API creation persists both optional fields as JSON null for a PDF-only request.
    query("UPDATE report_generations SET input_params=%s WHERE id=%s",
          Jsonb({"send_email": None, "recipients": None, "city": "Irvine"}), report)

    def complete_before_ack(name, args, kwargs, **options):
        assert tasks.generate_report(*args, **kwargs)["ok"]

    publish.side_effect = complete_before_ack
    assert retry()["status"] == "completed"
    render.assert_called_once()


def test_two_operators_and_bounded_republication(generation):
    retry, _, publish, _, _, _, age = generation
    def request(_):
        try:
            return retry()["status"]
        except HTTPException as exc:
            return exc.status_code

    with ThreadPoolExecutor(2) as pool:
        outcomes = list(pool.map(request, range(2)))
    assert "queued" in outcomes and 409 in outcomes
    for _ in range(2):
        age()
        retry()
    age()
    with pytest.raises(HTTPException, match="three recovery attempts"):
        retry()
    assert publish.call_count == 3


def test_manual_recovery_stays_closed_during_worker_rollout(generation, monkeypatch):
    retry, _, publish, _, query, report, _ = generation
    monkeypatch.delenv("ADMIN_GENERATION_RETRY_ENABLED")
    with pytest.raises(HTTPException, match="disabled for this worker deployment"):
        retry()
    publish.assert_not_called()
    assert query("SELECT status FROM report_generations WHERE id=%s", report) == ("failed",)


@pytest.mark.parametrize("params,logged", [
    (None, False), ({}, False), ({"send_email": False}, False),
    ({"send_email": True, "recipients": []}, False),
    ({"send_email": False, "recipients": ["a@example.test"]}, False),
    ({"send_email": False, "recipients": []}, True),
])
def test_manual_delivery_uncertainty_never_publishes(generation, params, logged):
    retry, _, publish, _, query, report, _ = generation
    query("UPDATE report_generations SET input_params=%s WHERE id=%s", Jsonb(params), report)
    if logged:
        query("""INSERT INTO email_log (account_id,report_id,provider,to_emails,subject,status)
                 SELECT account_id,id,'sendgrid','{}','prior attempt','sending'
                 FROM report_generations WHERE id=%s""", report)
    with pytest.raises(HTTPException, match="No report or email was queued"):
        retry()
    publish.assert_not_called()
    assert query("SELECT status FROM report_generations WHERE id=%s", report) == ("failed",)


@pytest.mark.parametrize("claimed,attempts,hours_old,allowed", [
    (True, 1, 1, False), (False, 2, 1, True), (False, 6, 1, False), (False, 1, 7, False),
])
def test_scheduled_retry_preserves_outbox_bounds(db_session, claimed, attempts, hours_old, allowed, monkeypatch):
    account, schedule, report = (str(uuid4()) for _ in range(3))
    with psycopg.connect(db_session) as conn:
        conn.execute("INSERT INTO accounts (id, name, slug) VALUES (%s, 'retry test', %s)", (account, account))
        conn.execute("""INSERT INTO users (account_id,email,first_name,last_name,email_verified)
                        VALUES (%s,%s,'Test','Agent',true)""", (account, f"{account}@example.test"))
        conn.execute("""INSERT INTO schedules (id, account_id, name, report_type, cadence, recipients)
                        VALUES (%s,%s,'monthly','market_snapshot','monthly','{}')""", (schedule, account))
        conn.execute("""INSERT INTO report_generations (id, account_id, report_type, status, input_params)
                        VALUES (%s,%s,'market_snapshot','failed',%s)""",
                     (report, account, Jsonb({"schedule_id": schedule})))
        conn.execute("""INSERT INTO schedule_runs (schedule_id, report_run_id, status, recovery_tracked,
                            send_claimed_at, dispatch_attempts, created_at)
                        VALUES (%s,%s,'failed',true,CASE WHEN %s THEN now() END,%s,
                                now()-make_interval(hours => %s))""", (schedule, report, claimed, attempts, hours_old))
    monkeypatch.setattr(celery_app, "send_task", lambda *a, **kw: pytest.fail("manual publication"))
    try:
        if not allowed:
            with pytest.raises(HTTPException) as refused:
                admin.retry_market_report(report, {"account_id": account})
            assert refused.value.status_code == 409
        else:
            assert admin.retry_market_report(report, {"account_id": account})["status"] == "queued"
        with psycopg.connect(db_session) as conn:
            row = conn.execute("SELECT status, send_claimed_at IS NOT NULL FROM schedule_runs WHERE report_run_id=%s",
                               (report,)).fetchone()
        assert row == ("queued" if allowed else "failed", claimed)
        if allowed:
            publish = Mock(return_value=("task-id", None))
            scheduled_runs.sweep_tracked(db_session, publish)
            assert [call.args[0] for call in publish.call_args_list].count(report) == 1
            with psycopg.connect(db_session) as conn:
                assert conn.execute("SELECT dispatch_attempts FROM schedule_runs WHERE report_run_id=%s",
                                    (report,)).fetchone() == (attempts + 1,)
    finally:
        with psycopg.connect(db_session) as conn:
            conn.execute("DELETE FROM report_generations WHERE id=%s", (report,))
            conn.execute("DELETE FROM schedules WHERE id=%s", (schedule,))
            conn.execute("DELETE FROM users WHERE account_id=%s", (account,))
            conn.execute("DELETE FROM accounts WHERE id=%s", (account,))
