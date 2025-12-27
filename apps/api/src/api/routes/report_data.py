from fastapi import APIRouter, Depends, HTTPException, Request
from ..db import db_conn, set_rls, fetchone_dict
from .reports import require_account_id
from ..services.branding import get_brand_for_account
import re

router = APIRouter(prefix="/v1")

# UUID v4 regex pattern for validation
UUID_PATTERN = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$', re.I)

def is_valid_uuid(value: str) -> bool:
    """Validate UUID format to prevent brute-force attacks."""
    return bool(UUID_PATTERN.match(value))

@router.get("/reports/{run_id}/data")
def report_data(run_id: str, request: Request):
    """
    Public endpoint for report data - used by print pages for PDF generation.
    Looks up account_id from the report itself, no auth required.
    
    Phase 30: Now includes brand info for white-label PDF rendering.
    
    Security: Validates UUID format to prevent enumeration attacks.
    """
    # Validate UUID format to prevent brute-force enumeration
    if not is_valid_uuid(run_id):
        raise HTTPException(status_code=400, detail="Invalid report ID format")
    
    with db_conn() as (conn, cur):
        # First, get the account_id and result_json for this report (no RLS)
        cur.execute("SELECT account_id::text, result_json FROM report_generations WHERE id=%s", (run_id,))
        row = fetchone_dict(cur)
        if not row:
            raise HTTPException(status_code=404, detail="Report not found")
        if not row.get("result_json"):
            raise HTTPException(status_code=404, detail="Report data not yet available")
        
        # Phase 30: Add brand info for white-label PDFs
        account_id = row["account_id"]
        brand = get_brand_for_account(cur, account_id)
        
        # Return result_json + brand
        return {
            **row["result_json"],
            "brand": brand
        }









