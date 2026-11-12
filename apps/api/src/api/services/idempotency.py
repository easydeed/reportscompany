"""A retried create returns what the first one made (LR-024, D-382/D-330).

Design: docs/plans/launch-readiness-2026-11-06/LR-024_SAFE_RETRY.md, rev 3,
Codex design PASS.

The wizard's create can succeed and lose its answer. Its "Try again" sends
the same `Idempotency-Key` to POST /v1/idempotent/{reports,schedules}; those
routes exist only in this release, so an older API answers 404 there without
running anything, and a keyed request can never create an unkeyed duplicate.

Inside the endpoint's own transaction, after authentication and before the
verification and limit checks:

  1. a transaction-scoped advisory lock on (endpoint, account, key), so two
     concurrent requests with one key are serialized;
  2. look the key up:
       none                    -> a new request; `record()` it in the SAME
                                  transaction as the resource it creates
       older than the window   -> 410 idempotency_key_expired (never new)
       a different body        -> 409 idempotency_key_reused
       same body               -> replay: the resource as it is now, with no
                                  verification, limit, usage, enqueue or email;
                                  if it was deleted, 410 idempotent_resource_gone
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Any, Dict, Optional

from fastapi import HTTPException, Request
from pydantic import BaseModel

KEY_HEADER = "Idempotency-Key"
REPLAYED_HEADER = "Idempotent-Replayed"
#: The server replays a key for 7 days; the wizard promises a safe retry for 6.
REPLAY_WINDOW_DAYS = 7
REPORTS = "reports.create"
SCHEDULES = "schedules.create"

_KEY = re.compile(r"^[A-Za-z0-9_-]{8,100}$")


@dataclass(frozen=True)
class Claim:
    endpoint: str
    key: str
    request_hash: str


def require_key(request: Request) -> str:
    """The keyed routes require a well-formed key; nothing is looked up without one."""
    key = request.headers.get(KEY_HEADER)
    if key is None or not key.strip():
        raise HTTPException(status_code=422, detail={
            "error": "idempotency_key_required",
            "message": f"This endpoint requires an {KEY_HEADER} header.",
        })
    if not _KEY.match(key):
        raise HTTPException(status_code=422, detail={
            "error": "invalid_idempotency_key",
            "message": f"{KEY_HEADER} must be 8–100 letters, digits, '-' or '_'.",
        })
    return key


def fingerprint(payload: BaseModel, stored_as: Optional[Dict[str, Any]] = None) -> str:
    """SHA-256 of the VALIDATED request, canonically serialized.

    Keys are sorted at every depth and defaults are filled by the model, so
    JSON key order, an omitted default and the same default sent explicitly
    all hash alike; array order is kept (it is part of the request). Values
    the server resolves later (the account's default theme or accent) are not
    in the model, so they cannot make a replay look different.

    `stored_as` replaces fields with the value the route actually stores for
    them, so forms the route treats as one request hash alike: an omitted,
    null or empty `filters` all store `{}` (Codex code review). The route
    computes it with the same helper it stores with, so the two cannot drift.
    """
    form = {**payload.model_dump(mode="json"), **(stored_as or {})}
    canonical = json.dumps(form, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def claim_for(request: Request, endpoint: str, payload: BaseModel,
              stored_as: Optional[Dict[str, Any]] = None) -> Claim:
    return Claim(endpoint, require_key(request), fingerprint(payload, stored_as))


def lookup(cur, account_id: str, claim: Claim) -> Optional[str]:
    """Lock the key for this transaction, then: None for a new request, or the
    resource id to replay. Raises 410 for an expired key, 409 for a reused one."""
    cur.execute("SELECT pg_advisory_xact_lock(hashtextextended(%s, 0))",
                (f"{claim.endpoint}:{account_id}:{claim.key}",))
    cur.execute("""
        SELECT request_hash, resource_id::text,
               created_at < NOW() - make_interval(days => %s) AS expired
        FROM request_idempotency
        WHERE account_id = %s::uuid AND endpoint = %s AND idem_key = %s
    """, (REPLAY_WINDOW_DAYS, account_id, claim.endpoint, claim.key))
    row = cur.fetchone()
    if not row:
        return None
    request_hash, resource_id, expired = row
    if expired:
        raise HTTPException(status_code=410, detail={
            "error": "idempotency_key_expired",
            "message": "This request is too old to retry safely. Check your list before sending it again.",
        })
    if request_hash != claim.request_hash:
        raise HTTPException(status_code=409, detail={
            "error": "idempotency_key_reused",
            "message": "This Idempotency-Key was already used for a different request.",
        })
    return resource_id


def gone(resource_id: str):
    """The key's resource was created and has since been deleted: never recreate it."""
    raise HTTPException(status_code=410, detail={
        "error": "idempotent_resource_gone",
        "resource_id": resource_id,
        "message": "Your earlier request went through, and what it created has since been deleted.",
    })


def record(cur, account_id: str, claim: Claim, resource_id: str) -> None:
    """In the SAME transaction as the resource: a refusal or failure leaves no key."""
    cur.execute("""
        INSERT INTO request_idempotency (account_id, endpoint, idem_key, request_hash, resource_id)
        VALUES (%s::uuid, %s, %s, %s, %s::uuid)
    """, (account_id, claim.endpoint, claim.key, claim.request_hash, resource_id))
