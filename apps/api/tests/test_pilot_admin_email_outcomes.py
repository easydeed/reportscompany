"""Exercise the admin query with worker outcomes on the migrated schema."""
from contextlib import contextmanager
from uuid import uuid4

import psycopg
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.routes import admin


def test_admin_email_outcomes_and_filters(db_session, monkeypatch):
    app = FastAPI()
    app.include_router(admin.router)
    slug = "pct-outcomes-" + uuid4().hex
    with psycopg.connect(db_session) as conn, conn.cursor() as cur:
        account = cur.execute(
            "INSERT INTO accounts (name, slug) VALUES (%s, %s) RETURNING id",
            (slug, slug),
        ).fetchone()[0]
        app.dependency_overrides[admin.get_admin_user] = lambda: {"account_id": str(account)}

        @contextmanager
        def test_connection():
            yield conn, cur

        monkeypatch.setattr(admin, "db_conn", test_connection)
        cases = [("sent", 202), ("suppressed", 200), ("needs_review", None),
                 ("blocked_unverified", None), ("failed", 400), ("unknown", 202)]
        for status, code in cases:
            cur.execute(
                "INSERT INTO email_log (account_id, to_emails, status, response_code) "
                "VALUES (%s, %s, %s, %s)",
                (account, [f"{status}-{slug}@example.test"], status, code),
            )

        with TestClient(app) as client:
            def logs(**filters):
                result = client.get("/v1/admin/emails", params=filters)
                assert result.status_code == 200, result.text
                return result.json()["emails"]

            records = logs(q=slug.upper())
            assert {r["delivery_status"]: r["status"] for r in records} == {
                value: "success" if value == "sent" else value for value, _ in cases
            }
            held = logs(q=f"needs_review-{slug}", status="needs_review", limit=1)
            assert len(held) == 1 and held[0]["delivery_status"] == "needs_review"
            assert not logs(q=f"suppressed-{slug}", status="sent")
        conn.rollback()
