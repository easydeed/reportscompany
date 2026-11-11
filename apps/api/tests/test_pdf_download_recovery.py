"""The homeowner's PDF button: a working link, one job, an honest status (LR-022, D-380).

Real `/v1/r/{id}/pdf` routes against the migrated database; only the R2
signer and the Celery queue are replaced.

On main: POST returned a stored 7-day presigned URL forever (dead after a
week), and for a missing PDF it logged an analytics event and queued nothing,
so the page polled a status that could never change.

Jerry, 2026-11-11: re-sign on click; render a missing PDF only; 20 generation
requests per hour per visitor.
"""
import json
import os
import threading
import uuid

import pytest

psycopg = pytest.importorskip("psycopg")
DB = os.getenv("DATABASE_URL")
LEGACY = ("https://acct123.r2.cloudflarestorage.com/market-reports/consumer-reports/a/b.pdf"
          "?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Expires=604800&X-Amz-Signature=abc")


@pytest.fixture
def api(monkeypatch):
    if not DB or "fake" in DB:
        if os.getenv("GITHUB_ACTIONS"):
            pytest.fail("DATABASE_URL is not set in CI; this test must not skip there")
        pytest.skip("Set DATABASE_URL to run this test")
    from fastapi.testclient import TestClient
    from api.main import app
    from api.routes import mobile_reports
    from api.services import consumer_pdf
    queued = []
    monkeypatch.setattr(mobile_reports, "_queue_pdf_generation", lambda rid: queued.append(rid), raising=False)

    class Signer:
        def generate_presigned_url(self, op, Params, ExpiresIn):
            return f"https://signed.test/{Params['Key']}?expires={ExpiresIn}"
    monkeypatch.setattr(consumer_pdf, "_client", lambda: Signer())
    for name in ("R2_ACCOUNT_ID", "R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY"):
        monkeypatch.setattr(consumer_pdf, name, "configured")
    return TestClient(app, raise_server_exceptions=False), queued, consumer_pdf


@pytest.fixture
def report():
    made = []

    def make(**cols):
        tag = uuid.uuid4().hex[:8]
        acc, agent, rid = str(uuid.uuid4()), str(uuid.uuid4()), str(uuid.uuid4())
        base = {"status": "sent", "consumer_sms_sent_at": "now()"}
        base.update(cols)
        with psycopg.connect(DB, autocommit=True) as conn:
            conn.execute("INSERT INTO accounts (id, name, slug, account_type, plan_slug) "
                         "VALUES (%s, 'LR-022', %s, 'REGULAR', 'free')", (acc, f"lr022-{tag}"))
            conn.execute("INSERT INTO users (id, account_id, email, first_name, last_name) "
                         "VALUES (%s, %s, %s, 'Dana', 'Ortiz')", (agent, acc, f"lr022-{tag}@example.com"))
            conn.execute("INSERT INTO consumer_reports (id, agent_id, agent_code, consumer_phone, "
                         "property_address, property_city, property_state, property_zip, property_data) "
                         "VALUES (%s, %s, 'L22', '6265550123', '1 Main St', 'La Verne', 'CA', '91750', %s)",
                         (rid, agent, json.dumps({})))
            for col, val in base.items():
                if val == "now()":
                    conn.execute(f"UPDATE consumer_reports SET {col} = NOW() WHERE id = %s", (rid,))
                else:
                    conn.execute(f"UPDATE consumer_reports SET {col} = %s WHERE id = %s", (val, rid))
        made.append((rid, agent, acc))
        return rid
    yield make
    with psycopg.connect(DB, autocommit=True) as conn:
        for rid, agent, acc in made:
            conn.execute("DELETE FROM consumer_reports WHERE id = %s", (rid,))
            conn.execute("DELETE FROM users WHERE id = %s", (agent,))
            conn.execute("DELETE FROM accounts WHERE id = %s", (acc,))


def _row(rid):
    with psycopg.connect(DB) as conn:
        return conn.execute("SELECT pdf_status, pdf_requested_count, pdf_error FROM consumer_reports "
                            "WHERE id = %s", (rid,)).fetchone()


def _post(client, rid, ip="203.0.113.7"):
    return client.post(f"/v1/r/{rid}/pdf", headers={"X-Forwarded-For": ip})


# ── an existing PDF: a fresh link, every time ───────────────────────────────

def test_an_existing_pdf_gets_a_freshly_signed_link_and_no_job(api, report):
    client, queued, _ = api
    rid = report(pdf_url=LEGACY, pdf_object_key="consumer-reports/acc/r/gen.pdf")
    r = _post(client, rid)
    assert r.status_code == 200 and r.json() == {
        "status": "ready", "pdf_url": "https://signed.test/consumer-reports/acc/r/gen.pdf?expires=3600"}
    assert queued == [] and _row(rid)[1] == 1


def test_a_report_made_before_the_key_column_is_re_signed_from_its_stored_url(api, report):
    """The 7-day link a week-old report stored is dead; its object is not."""
    client, queued, _ = api
    rid = report(pdf_url=LEGACY)
    r = client.get(f"/v1/r/{rid}/pdf/status")
    assert r.json()["pdf_url"] == "https://signed.test/consumer-reports/a/b.pdf?expires=3600"
    assert queued == []


def test_the_object_key_is_read_from_both_url_styles_and_nothing_else():
    from api.services.consumer_pdf import object_key_from_url
    assert object_key_from_url(LEGACY, "market-reports") == "consumer-reports/a/b.pdf"
    assert object_key_from_url("https://market-reports.acct.r2.cloudflarestorage.com/x/y.pdf"
                               "?X-Amz-Signature=s", "market-reports") == "x/y.pdf"
    assert object_key_from_url("https://cdn.example.com/x/y.pdf", "market-reports") is None
    assert object_key_from_url("http://localhost:10000/dev-files/x.pdf", "market-reports") is None
    assert object_key_from_url(None) is None


def test_without_r2_credentials_the_stored_link_is_returned(api, report, monkeypatch):
    client, _, consumer_pdf = api
    monkeypatch.setattr(consumer_pdf, "R2_ACCOUNT_ID", "")
    rid = report(pdf_url="https://cdn.example.com/x.pdf")
    assert _post(client, rid).json()["pdf_url"] == "https://cdn.example.com/x.pdf"


# ── a missing PDF: one job ──────────────────────────────────────────────────

def test_a_delivered_report_with_no_pdf_queues_one_job_however_many_clicks(api, report):
    client, queued, _ = api
    rid = report()
    first, second = _post(client, rid), _post(client, rid)
    assert first.json()["status"] == "generating" and second.json()["status"] == "generating"
    assert queued == [rid], "a second click queued a second render"
    assert _row(rid)[0] == "queued"


def test_concurrent_clicks_queue_one_job(api, report):
    client, queued, _ = api
    rid = report()
    barrier = threading.Barrier(4, timeout=30)

    def click():
        barrier.wait()
        _post(client, rid)
    threads = [threading.Thread(target=click) for _ in range(4)]
    [t.start() for t in threads]
    [t.join(60) for t in threads]
    assert queued == [rid]


def test_an_undelivered_report_queues_nothing(api, report):
    client, queued, _ = api
    rid = report(status="processing", consumer_sms_sent_at=None)
    r = _post(client, rid)
    assert r.status_code == 409 and r.json()["status"] == "unavailable"
    assert queued == []


def test_a_stale_or_failed_job_can_be_requested_again(api, report):
    client, queued, _ = api
    stale = report(pdf_status="queued")
    with psycopg.connect(DB, autocommit=True) as conn:
        conn.execute("UPDATE consumer_reports SET pdf_claimed_at = NOW() - interval '1 hour' WHERE id = %s",
                     (stale,))
    failed = report(pdf_status="failed", pdf_error="R2 refused: AccessDenied for key x")
    assert _post(client, stale).json()["status"] == "generating"
    assert _post(client, failed).json()["status"] == "generating"
    assert queued == [stale, failed]


def test_a_queue_that_cannot_be_reached_is_an_honest_failure(api, report, monkeypatch):
    client, _, _ = api
    from api.routes import mobile_reports

    def down(rid):
        raise ConnectionError("redis down")
    monkeypatch.setattr(mobile_reports, "_queue_pdf_generation", down)
    rid = report()
    r = _post(client, rid)
    assert r.json()["status"] == "failed" and _row(rid)[0] == "failed"


# ── the visitor limit: 20 an hour ───────────────────────────────────────────

def test_the_twenty_first_request_in_an_hour_is_refused(api, report):
    client, queued, consumer_pdf = api
    rid = report()
    with psycopg.connect(DB, autocommit=True) as conn:
        for _ in range(consumer_pdf.GENERATE_REQUESTS_PER_HOUR):
            conn.execute("INSERT INTO report_analytics (report_id, event_type, ip_address) "
                         "VALUES (%s, %s, '198.51.100.9')", (rid, consumer_pdf.GENERATE_EVENT))
    r = _post(client, rid, ip="198.51.100.9")
    assert r.status_code == 429 and r.json()["status"] == "rate_limited"
    assert queued == []
    assert _post(client, rid, ip="198.51.100.10").json()["status"] == "generating", "another visitor is not limited"


# ── the status a page polls ─────────────────────────────────────────────────

def test_the_status_route_never_queues_and_never_leaks_the_error(api, report):
    client, queued, _ = api
    missing, failed, generating = report(), report(pdf_status="failed", pdf_error="R2 AccessDenied key x"), \
        report(pdf_status="generating")
    with psycopg.connect(DB, autocommit=True) as conn:
        conn.execute("UPDATE consumer_reports SET pdf_claimed_at = NOW() WHERE id = %s", (generating,))
    assert client.get(f"/v1/r/{missing}/pdf/status").json()["status"] == "missing"
    body = client.get(f"/v1/r/{failed}/pdf/status").json()
    assert body["status"] == "failed" and "AccessDenied" not in json.dumps(body)
    assert client.get(f"/v1/r/{generating}/pdf/status").json()["status"] == "generating"
    assert queued == []


def test_a_render_that_went_stale_reads_as_failed(api, report):
    client, _, _ = api
    rid = report(pdf_status="generating")
    with psycopg.connect(DB, autocommit=True) as conn:
        conn.execute("UPDATE consumer_reports SET pdf_claimed_at = NOW() - interval '1 hour' WHERE id = %s", (rid,))
    assert client.get(f"/v1/r/{rid}/pdf/status").json()["status"] == "failed"


def test_an_unknown_report_is_404(api):
    client, _, _ = api
    assert _post(client, str(uuid.uuid4())).status_code == 404


def test_the_queue_statement_itself_refuses_an_undelivered_report_or_an_existing_pdf(api, report):
    """The route answers first, but the one statement that queues must not rely on it."""
    _, _, consumer_pdf = api
    undelivered = report(status="processing", consumer_sms_sent_at=None)
    has_pdf = report(pdf_url="https://cdn.example.com/x.pdf")
    with psycopg.connect(DB, autocommit=True) as conn:
        cur = conn.cursor()
        assert consumer_pdf.queue_missing_pdf(cur, undelivered) is False
        assert consumer_pdf.queue_missing_pdf(cur, has_pdf) is False
