from fastapi import APIRouter, HTTPException, Request
from ..db import db_conn, set_rls, fetchone_dict
from ..services.branding import get_brand_for_account
from ..settings import settings
import hmac
import re

router = APIRouter(prefix="/v1")

# UUID v4 regex pattern for validation
UUID_PATTERN = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$', re.I)

def is_valid_uuid(value: str) -> bool:
    """Validate UUID format to prevent brute-force attacks."""
    return bool(UUID_PATTERN.match(value))


def _is_internal_render_caller(request: Request) -> bool:
    """
    S3 — Returns True if the request carries a valid X-Internal-Render-Token
    header. Used by the Next.js print page (apps/web/app/print/[runId]/page.tsx)
    and social image route (apps/web/app/api/social/[runId]/route.ts) to
    render report HTML server-side without a user session.

    The token is configured via the INTERNAL_RENDER_TOKEN env var on both
    the API and the Next.js service. If the env var is empty, the token
    path is disabled and only authenticated account sessions can read
    report data.

    Uses hmac.compare_digest to prevent timing attacks.
    """
    expected = settings.INTERNAL_RENDER_TOKEN
    if not expected:
        return False
    provided = request.headers.get("X-Internal-Render-Token", "")
    if not provided:
        return False
    return hmac.compare_digest(provided, expected)


@router.get("/reports/{run_id}/data")
def report_data(run_id: str, request: Request):
    """
    Report data endpoint — used by the print page and social image renderer
    to fetch the stored result_json + brand info for a market report.

    S3 — Was previously public (middleware bypass). Now requires either:
      1. An authenticated account session (JWT, API key, or demo header),
         in which case the report must belong to that account_id.
      2. The X-Internal-Render-Token header matching INTERNAL_RENDER_TOKEN
         (used by the Next.js print/social server-side renderers).
    Anonymous callers without either credential get 401.

    Phase 30: Includes brand info for white-label PDF rendering.

    Security: Validates UUID format to prevent enumeration attacks.
    """
    if not is_valid_uuid(run_id):
        raise HTTPException(status_code=400, detail="Invalid report ID format")

    # Resolve auth posture. AuthContextMiddleware sets request.state.account_id
    # only when a user session was authenticated. If absent, we fall back to
    # the internal render token; if neither is present we 401.
    session_account_id = getattr(request.state, "account_id", None)
    is_internal = _is_internal_render_caller(request)

    if not session_account_id and not is_internal:
        raise HTTPException(status_code=401, detail="Unauthorized")

    with db_conn() as (conn, cur):
        # Look up the report. For session callers we additionally constrain
        # by account_id so cross-tenant ID guessing returns 404, identical
        # to /v1/reports/{id}.
        if session_account_id:
            set_rls(cur, session_account_id)
            cur.execute(
                "SELECT account_id::text, result_json, pdf_url, theme_id "
                "FROM report_generations WHERE id=%s AND account_id=%s",
                (run_id, session_account_id),
            )
        else:
            # Internal render path: trust the token, look up by id only,
            # then scope RLS to the report's owning account so the brand
            # query below sees the right rows.
            cur.execute(
                "SELECT account_id::text, result_json, pdf_url, theme_id "
                "FROM report_generations WHERE id=%s",
                (run_id,),
            )

        row = fetchone_dict(cur)
        if not row:
            raise HTTPException(status_code=404, detail="Report not found")
        if not row.get("result_json"):
            raise HTTPException(status_code=404, detail="Report data not yet available")

        account_id = row["account_id"]
        if is_internal and not session_account_id:
            set_rls(cur, account_id)

        brand = get_brand_for_account(cur, account_id)

        return {
            **row["result_json"],
            "brand": brand,
            "pdf_url": row.get("pdf_url"),
            "theme_id": row.get("theme_id"),
        }
