"""A delivered report's missing PDF is generated once, from what was stored (LR-022, D-380).

Real `generate_consumer_report_pdf` against the migrated database; the PDF
renderer and R2 are faked at their edges. Jerry, 2026-11-11: render a missing
PDF only, from the stored data, into a new object; never replace one.

On main there was no such task: the API queued nothing and the PDF a failed
render left missing stayed missing.
"""
import json
import threading
import uuid
from pathlib import Path

import pytest

from test_consumer_failures_are_recorded import db, report, tasks  # noqa: F401  (fixtures)

psycopg = pytest.importorskip("psycopg")

COMPS = [
    {"address": "1185 Sample Court", "city": "La Verne", "status": "Closed", "close_price": 655000,
     "price": 655000, "bedrooms": 3, "bathrooms": 2.5, "sqft": 1500, "close_date": "2026-09-01"},
    {"address": "1340 Example Avenue", "city": "La Verne", "status": "Closed", "close_price": 610000,
     "price": 610000, "bedrooms": 3, "bathrooms": 2, "sqft": 1400, "close_date": "2026-08-01"},
]


def _q(db, sql, *params):
    with psycopg.connect(db) as conn:
        return conn.execute(sql, params).fetchall()


@pytest.fixture
def renderer(tasks, monkeypatch, tmp_path):
    """Production file naming (PDF_DIR/<run_id>.pdf) and an in-memory R2."""
    seen = {"html": [], "store": {}}

    def render(run_id, account_id, html_content, print_base=None, **k):
        seen["html"].append(html_content)
        path = tmp_path / f"{run_id}.pdf"
        path.write_bytes(f"PDF {run_id}".encode())
        return str(path), None

    def upload(local_path, key, *a, **k):
        seen["store"][key] = Path(local_path).read_bytes()
        return f"https://r2.test/{key}"
    monkeypatch.setattr(tasks, "render_pdf", render)
    monkeypatch.setattr(tasks, "upload_to_r2", upload)
    monkeypatch.setattr(tasks, "embed_images_as_base64", lambda html: html)
    seen["dir"] = tmp_path
    return seen


@pytest.fixture
def delivered(report, db):
    """A report delivered by text whose PDF render had failed."""
    def make(**cols):
        rid = report("sms")
        with psycopg.connect(db, autocommit=True) as conn:
            conn.execute("UPDATE consumer_reports SET status = 'sent', consumer_sms_sent_at = NOW(), "
                         "comparables = %s, property_data = property_data || %s::jsonb, "
                         "pdf_status = 'queued', pdf_claimed_at = NOW() WHERE id = %s",
                         (json.dumps(COMPS), json.dumps({"owner_name": "Gerardo Owner"}), rid))
            conn.execute("UPDATE accounts SET primary_color = '#0D9488' WHERE id = "
                         "(SELECT u.account_id FROM users u JOIN consumer_reports cr ON cr.agent_id = u.id "
                         "WHERE cr.id = %s)", (rid,))
            for col, val in cols.items():
                conn.execute(f"UPDATE consumer_reports SET {col} = %s WHERE id = %s", (val, rid))
        return rid
    return make


def _state(db, rid):
    return _q(db, "SELECT pdf_status, pdf_url, pdf_object_key, pdf_error, status, consumer_sms_sent_at, "
                  "comparables, property_data FROM consumer_reports WHERE id = %s", rid)[0]


def test_a_missing_pdf_is_generated_from_the_stored_report(tasks, delivered, db, renderer):
    rid = delivered()
    before = _state(db, rid)
    result = tasks.generate_consumer_report_pdf.apply(args=[rid]).get()
    status, url, key, err, delivery_status, sent_at, comps, prop = _state(db, rid)
    assert result["ok"] is True and status == "ready" and err is None
    account = _q(db, "SELECT u.account_id FROM users u JOIN consumer_reports cr ON cr.agent_id = u.id "
                     "WHERE cr.id = %s", rid)[0][0]
    assert key.startswith(f"consumer-reports/{account}/{rid}/") and key.endswith(".pdf")
    assert url == f"https://r2.test/{key}" and renderer["store"][key]
    assert (delivery_status, sent_at, comps, prop) == before[4:], "recovery changed the delivered report"
    assert not list(renderer["dir"].glob("*.pdf")), "the local file was left behind"


def test_the_recovered_pdf_keeps_the_theme_and_invents_nothing(tasks, delivered, db, renderer):
    rid = delivered()
    tasks.generate_consumer_report_pdf.apply(args=[rid]).get()
    [html] = renderer["html"]
    assert "#0D9488".lower() in html.lower(), "the account's theme colour is missing"
    assert "Gerardo" not in html, "the assessor's owner name reached the PDF"
    # The range panel's "confidence A, strict match" is the comps' match grade,
    # in every delivered PDF; what must not appear is a point estimate.
    for invented in ("Most likely", "Estimated value", "Estimated Value"):
        assert invented not in html


def test_an_existing_pdf_is_never_replaced(tasks, delivered, db, renderer):
    rid = delivered(pdf_url="https://r2.test/original.pdf", pdf_object_key="original.pdf", pdf_status="ready")
    result = tasks.generate_consumer_report_pdf.apply(args=[rid]).get()
    assert result["ok"] is False and renderer["html"] == []
    assert _state(db, rid)[1:3] == ("https://r2.test/original.pdf", "original.pdf")


def test_an_undelivered_report_is_not_rendered(tasks, delivered, db, renderer):
    rid = delivered(status="processing", consumer_sms_sent_at=None)
    assert tasks.generate_consumer_report_pdf.apply(args=[rid]).get()["ok"] is False
    assert renderer["html"] == []


@pytest.mark.parametrize("where", ["render", "upload"])
def test_a_failed_render_or_upload_is_recorded_and_can_be_retried(tasks, delivered, db, renderer, monkeypatch, where):
    rid = delivered()

    def boom(*a, **k):
        raise RuntimeError(f"{where} broke")
    monkeypatch.setattr(tasks, "render_pdf" if where == "render" else "upload_to_r2", boom)
    result = tasks.generate_consumer_report_pdf.apply(args=[rid]).get()
    status, url, key, err, *_ = _state(db, rid)
    assert result["ok"] is False and status == "failed" and url is None and key is None
    assert f"{where} broke" in err
    assert not list(renderer["dir"].glob("*.pdf"))


def test_a_live_render_is_left_alone_and_a_stale_one_is_taken_over(tasks, delivered, db, renderer):
    rid = delivered(pdf_status="generating")
    assert tasks.generate_consumer_report_pdf.apply(args=[rid]).get()["ok"] is False
    with psycopg.connect(db, autocommit=True) as conn:
        conn.execute("UPDATE consumer_reports SET pdf_claimed_at = NOW() - interval '1 hour' WHERE id = %s", (rid,))
    assert tasks.generate_consumer_report_pdf.apply(args=[rid]).get()["ok"] is True


def test_two_jobs_for_one_report_render_once(tasks, delivered, db, renderer, monkeypatch):
    rid = delivered()
    real_claim = tasks.consumer_delivery.claim_pdf_generation
    barrier = threading.Barrier(2, timeout=30)

    def together(*a, **k):
        barrier.wait()
        return real_claim(*a, **k)
    monkeypatch.setattr(tasks.consumer_delivery, "claim_pdf_generation", together)
    out = []
    threads = [threading.Thread(target=lambda: out.append(tasks.generate_consumer_report_pdf.apply(args=[rid]).get()))
               for _ in range(2)]
    [t.start() for t in threads]
    [t.join(60) for t in threads]
    assert sorted(r["ok"] for r in out) == [False, True]
    assert len(renderer["html"]) == 1


def test_a_late_finish_for_an_old_claim_is_refused(tasks, delivered, db, renderer):
    """A render taken over as stale cannot record its result over the new claim."""
    from worker import consumer_delivery as cd
    rid = delivered()
    with psycopg.connect(db, autocommit=True) as conn:
        first = cd.claim_pdf_generation(conn.cursor(), rid)
        conn.execute("UPDATE consumer_reports SET pdf_claimed_at = NOW() - interval '1 hour' WHERE id = %s", (rid,))
        second = cd.claim_pdf_generation(conn.cursor(), rid)
        assert first and second and first[-1] != second[-1]
        assert cd.finish_pdf_generation(conn.cursor(), rid, first[-1], pdf_url="u1", pdf_key="k1") is False
        assert cd.fail_pdf_generation(conn.cursor(), rid, first[-1], "late") is False
        assert cd.finish_pdf_generation(conn.cursor(), rid, second[-1], pdf_url="u2", pdf_key="k2") is True
    assert _state(db, rid)[1:3] == ("u2", "k2")


def test_delivery_records_the_object_key_so_downloads_can_be_re_signed(tasks, report, db, renderer, monkeypatch):
    from test_consumer_failures_are_recorded import _sent, _twilio
    _twilio(monkeypatch, _sent)
    rid = report("sms")
    tasks.process_consumer_report.apply(args=[rid]).get()
    status, url, key, *_ = _state(db, rid)
    assert status == "ready" and key and url == f"https://r2.test/{key}"


def test_a_report_from_before_0065_with_a_pdf_is_never_re_rendered(tasks, delivered, db, renderer):
    """Rows delivered before this change have a pdf_url and no pdf_status."""
    rid = delivered(pdf_url="https://r2.test/legacy.pdf", pdf_status=None)
    assert tasks.generate_consumer_report_pdf.apply(args=[rid]).get()["ok"] is False
    assert renderer["html"] == []
    assert _state(db, rid)[:2] == (None, "https://r2.test/legacy.pdf")
