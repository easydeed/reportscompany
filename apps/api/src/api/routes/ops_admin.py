"""LR-027 slice 4: the operator's view of alerts (design #317 rev 3, sections 5 and 7).

Platform admins only (`get_admin_user`).

  POST /v1/admin/ops/test-alert
      Requests a labelled test incident. The API only records the request (a
      short-lived Redis key); the ticker's monitor consumes it on its next run
      (within 5 minutes), opens `ops_test_alert` through the real incident and
      delivery path, and resolves it on the run after. So a test proves the
      actual code path, and it sends only what that path would send: nothing
      unless OPS_ALERTS_ENABLED=1 and a destination is set. This is the
      closure evidence route of design section 7.

  GET /v1/admin/ops/alerts
      Open incidents, the notifications that need reconciliation (`unknown`
      with no recorded resolution), and the most recent notifications.

  POST /v1/admin/ops/notifications/{id}/resolution
      The operator records whether an alert was actually received, with
      evidence. Allowed for `unknown` rows (did it arrive?) and `accepted`
      rows (closure evidence of actual receipt). First resolution wins.

The ops tables hold no account data and no destinations, so nothing here can
reveal an operator's address or number.
"""
import uuid
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ..db import db_conn
from ..deps.admin import get_admin_user

router = APIRouter(prefix="/v1/admin/ops", tags=["admin"])

# The worker's monitor consumes this key (apps/worker/src/worker/ops_monitor.py
# carries the same name; tests/test_ops_heartbeat_contract.py holds them equal).
TEST_ALERT_KEY = "ops:test_alert:requested"
TEST_ALERT_TTL_S = 3600
RECENT_LIMIT = 50


def _redis():
    from ..cache import get_redis
    return get_redis()


@router.post("/test-alert", status_code=202)
def request_test_alert(admin: dict = Depends(get_admin_user)):
    request_id = str(uuid.uuid4())
    try:
        created = _redis().set(TEST_ALERT_KEY, request_id, nx=True, ex=TEST_ALERT_TTL_S)
    except Exception:  # noqa: BLE001 - the monitor could not see it either
        raise HTTPException(status_code=503, detail="Redis is unavailable, so the monitor cannot be reached.")
    if not created:
        raise HTTPException(status_code=409, detail="A test alert is already waiting for the monitor's next run.")
    return {
        "requested": True,
        "request_id": request_id,
        "detail": ("The monitor opens the test incident on its next run (within 5 minutes) and "
                   "resolves it on the run after. It is delivered only if OPS_ALERTS_ENABLED=1 "
                   "and a destination is set for the channel."),
    }


def _iso(value):
    return value.isoformat() if value is not None else None


@router.get("/alerts")
def list_alerts(admin: dict = Depends(get_admin_user)):
    with db_conn() as (conn, cur):
        cur.execute("SELECT to_regclass('ops_alert_notifications') IS NOT NULL")
        if not cur.fetchone()[0]:
            raise HTTPException(status_code=503, detail="Migration 0069 (ops_alerts) is not applied.")
        cur.execute("""SELECT id, key, opened_at, member_count, members_truncated, last_evaluated_at
                       FROM ops_alerts WHERE resolved_at IS NULL ORDER BY opened_at""")
        open_alerts = [{"id": str(r[0]), "key": r[1], "opened_at": _iso(r[2]), "member_count": r[3],
                        "members_truncated": r[4], "last_evaluated_at": _iso(r[5])} for r in cur.fetchall()]
        columns = """n.id, a.key, n.event, n.channel, n.state, n.attempts, n.created_at, n.outcome_at,
                     n.provider_message_id, n.last_error_class, n.resolution, n.resolution_evidence"""
        cur.execute(f"""SELECT {columns} FROM ops_alert_notifications n JOIN ops_alerts a ON a.id = n.alert_id
                        WHERE n.state = 'unknown' AND n.resolution IS NULL ORDER BY n.id""")
        needs_reconciliation = [_notification(r) for r in cur.fetchall()]
        cur.execute(f"""SELECT {columns} FROM ops_alert_notifications n JOIN ops_alerts a ON a.id = n.alert_id
                        ORDER BY n.id DESC LIMIT %s""", (RECENT_LIMIT,))
        recent = [_notification(r) for r in cur.fetchall()]
    return {"open_alerts": open_alerts, "needs_reconciliation": needs_reconciliation, "recent": recent}


def _notification(r) -> dict:
    return {"id": r[0], "key": r[1], "event": r[2], "channel": r[3], "state": r[4], "attempts": r[5],
            "created_at": _iso(r[6]), "outcome_at": _iso(r[7]), "provider_message_id": r[8],
            "last_error_class": r[9], "resolution": r[10], "resolution_evidence": r[11]}


class Resolution(BaseModel):
    resolution: Literal["received", "not_received"]
    evidence: str = Field(..., min_length=3, max_length=500)


@router.post("/notifications/{notification_id}/resolution")
def resolve_notification(notification_id: int, body: Resolution, admin: dict = Depends(get_admin_user)):
    evidence = " ".join(body.evidence.split())
    if len(evidence) < 3:
        raise HTTPException(status_code=422, detail="Evidence is required.")
    recorded = f"{evidence} (recorded by user:{admin.get('id') or admin.get('user_id') or 'unknown'})"
    with db_conn() as (conn, cur):
        cur.execute("""UPDATE ops_alert_notifications
                       SET resolution = %s, resolution_evidence = %s
                       WHERE id = %s AND state IN ('unknown', 'accepted') AND resolution IS NULL
                       RETURNING id, state""", (body.resolution, recorded[:600], notification_id))
        row = cur.fetchone()
        if row is None:
            cur.execute("SELECT state, resolution FROM ops_alert_notifications WHERE id = %s", (notification_id,))
            found = cur.fetchone()
    if row is not None:
        return {"id": row[0], "state": row[1], "resolution": body.resolution}
    if found is None:
        raise HTTPException(status_code=404, detail="No such notification.")
    if found[1] is not None:
        raise HTTPException(status_code=409, detail="This notification already has a recorded resolution.")
    raise HTTPException(status_code=409,
                        detail=f"Only unknown or accepted notifications can be reconciled (this one is {found[0]}).")
