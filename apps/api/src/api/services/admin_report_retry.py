"""D-396. An operator can regenerate an artifact, never replay a manual send."""

import logging
import os

from fastapi import HTTPException

from ..db import db_conn, set_rls
from ..worker_client import celery_app

logger = logging.getLogger(__name__)
MAX_PUBLICATIONS = 3


def retry_generation(report_id: str, admin_account_id: str):
    with db_conn() as (conn, cur):
        set_rls(cur, admin_account_id, user_role="ADMIN")
        cur.execute("""
            SELECT status, account_id::text, report_type, input_params,
                   additional_params->'admin_generation_retry',
                   (additional_params->'admin_generation_retry'->>'requested_at')::timestamptz
                         > now() - interval '1 minute' AS recent,
                   jsonb_typeof(additional_params)
            FROM report_generations WHERE id=%s::uuid FOR UPDATE
        """, (report_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(404, "Report not found")
        status, account, kind, params, retry, recent, metadata_type = row
        if status != "failed" and not (retry and status in ("retry_pending", "queued", "processing")):
            raise HTTPException(409, f"Report is already {status}.")

        # Legacy rows can lack the schedule ID in their input snapshot.
        cur.execute("SELECT schedule_id::text FROM schedule_runs WHERE report_run_id=%s::uuid",
                    (report_id,))
        schedule = cur.fetchone()
        if schedule or (isinstance(params, dict) and params.get("schedule_id")):
            if not schedule or not isinstance(params, dict) or params.get("schedule_id") != schedule[0]:
                raise HTTPException(409, "Scheduled report history is incomplete. Review the occurrence.")
            # Only the existing outbox may publish it. Keep its horizon, attempt
            # count, backoff and irrevocable pre-send claim.
            cur.execute("""
                UPDATE schedule_runs SET status='queued', error=NULL, finished_at=NULL,
                    owner_token=NULL, lease_at=NULL, dispatched_at=NULL, started_at=NULL
                WHERE report_run_id=%s::uuid AND recovery_tracked AND status='failed'
                  AND send_claimed_at IS NULL AND dispatch_attempts < 6
                  AND created_at > now() - interval '6 hours'
                RETURNING id
            """, (report_id,))
            if not cur.fetchone():
                raise HTTPException(409, "Scheduled delivery requires operator review. No retry was queued.")
            cur.execute("UPDATE report_generations SET status='queued', error=NULL WHERE id=%s::uuid",
                        (report_id,))
            return {"ok": True, "report_id": report_id, "status": "queued", "has_retry": False,
                    "message": "The scheduled occurrence is waiting for its dispatch sweep."}

        cur.execute("SELECT EXISTS (SELECT FROM email_log WHERE report_id=%s::uuid)", (report_id,))
        if (cur.fetchone()[0] or not isinstance(params, dict) or "send_email" not in params
                or params["send_email"] not in (None, False)
                or "recipients" not in params or params["recipients"] not in (None, [])):
            raise HTTPException(409, "Delivery history or recipients prevent a safe manual retry. "
                                    "Review the original delivery. No report or email was queued.")
        if metadata_type not in (None, "object"):
            raise HTTPException(409, "Legacy report metadata requires operator review.")
        # Older workers cannot fence delayed original messages. Leave the
        # manual route closed until all of those workers have drained.
        if os.getenv("ADMIN_GENERATION_RETRY_ENABLED") != "1":
            raise HTTPException(503, "Manual generation recovery is disabled for this worker deployment.")
        # The worker holds the matching session lock throughout generation.
        cur.execute("SELECT pg_try_advisory_xact_lock(hashtextextended(%s::uuid::text, 396))", (report_id,))
        if not cur.fetchone()[0]:
            raise HTTPException(409, "A worker is already generating this report.")
        previous = retry["attempt"] if retry else 0
        if previous >= MAX_PUBLICATIONS:
            raise HTTPException(409, "All three recovery attempts have been used. Review the report manually.")
        if recent:
            raise HTTPException(409, "Recovery was requested within the last minute. Refresh before retrying.")
        attempt = previous + 1
        cur.execute("""
            UPDATE report_generations SET status='retry_pending', error=NULL, error_message=NULL,
                additional_params=jsonb_set(COALESCE(additional_params, '{}'::jsonb),
                    '{admin_generation_retry}',
                    jsonb_build_object('attempt', %s::int, 'requested_at', now()))
            WHERE id=%s::uuid
        """, (attempt, report_id))

    # Only the new worker understands this keyword. The worker reads the
    # generation inputs from PostgreSQL, not from the publication.
    try:
        celery_app.send_task("generate_report", args=[report_id, account, kind, {}],
                             kwargs={"admin_retry_attempt": attempt}, queue="celery", retry=False)
    except Exception as exc:
        logger.exception("Cannot confirm admin recovery publication for %s attempt %s", report_id, attempt)
        next_step = ("Refresh its status before retrying after one minute." if attempt < MAX_PUBLICATIONS
                     else "All three attempts have been used. Refresh its status and review manually.")
        raise HTTPException(503, f"Queue acknowledgement unavailable. The worker may have received the job. "
                                f"{next_step}") from exc
    with db_conn() as (conn, cur):
        set_rls(cur, admin_account_id, user_role="ADMIN")
        cur.execute("""
            UPDATE report_generations SET status='queued' WHERE id=%s::uuid AND status='retry_pending'
                AND additional_params->'admin_generation_retry'->>'attempt'=%s
        """, (report_id, str(attempt)))
        cur.execute("SELECT status, error FROM report_generations WHERE id=%s::uuid", (report_id,))
        status, error = cur.fetchone()
    return {"ok": True, "report_id": report_id, "status": status, "error": error, "has_retry": True,
            "message": f"Generation-only recovery attempt {attempt} of {MAX_PUBLICATIONS}. Status: {status}."}
