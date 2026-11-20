"""Serialize manual generation with operator recovery on the same report ID."""

from functools import wraps

import psycopg


def serialize_manual_generation(database_url):
    def decorate(generate):
        @wraps(generate)
        def guarded(task, run_id, account_id, report_type, params, *, admin_retry_attempt=None):
            if admin_retry_attempt is None and (params or {}).get("schedule_id"):
                return generate(task, run_id, account_id, report_type, params)

            # One connection owns the lock across the task's internal commits.
            # PostgreSQL releases it when the worker process/connection dies.
            with psycopg.connect(database_url(), autocommit=True) as conn:
                conn.execute("SELECT pg_advisory_lock(hashtextextended(%s::uuid::text, 396))", (run_id,))
                conn.execute("SELECT set_config('app.current_account_id', %s, false)", (account_id,))
                row = conn.execute("""
                    SELECT status, additional_params->'admin_generation_retry'->>'attempt', input_params,
                           report_type FROM report_generations WHERE id=%s::uuid AND account_id=%s::uuid
                """, (run_id, account_id)).fetchone()
                if not row:
                    return {"ok": False, "reason": "missing_generation", "run_id": run_id}
                status, current, stored, kind = row
                if current is None and admin_retry_attempt is None:
                    return generate(task, run_id, account_id, report_type, params)
                if (admin_retry_attempt is None or current != str(admin_retry_attempt)
                        or status not in ("queued", "retry_pending")):
                    return {"ok": False, "reason": "superseded_retry", "run_id": run_id}
                if (not isinstance(stored, dict) or stored.get("schedule_id")
                        or "send_email" not in stored or stored["send_email"] not in (None, False)
                        or "recipients" not in stored
                        or stored["recipients"] not in (None, [])):
                    return {"ok": False, "reason": "delivery_requires_review", "run_id": run_id}
                return generate(task, run_id, account_id, kind, stored, admin_retry_attempt=admin_retry_attempt)

        return guarded
    return decorate
