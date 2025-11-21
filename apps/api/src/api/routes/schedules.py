from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field, EmailStr, constr
from typing import List, Optional, Dict, Any, Literal, Union
from datetime import datetime
import json
from ..db import db_conn, set_rls, fetchone_dict, fetchall_dicts

router = APIRouter(prefix="/v1")

# ====== Recipient Schemas ======
class RecipientInput(BaseModel):
    """
    Typed recipient for schedules.
    
    Each recipient is stored in the DB as a JSON-encoded string:
    - {"type":"contact","id":"<contact_id>"}
    - {"type":"sponsored_agent","id":"<account_id>"}
    - {"type":"manual_email","email":"<email>"}
    """
    type: Literal["contact", "sponsored_agent", "manual_email"]
    id: Optional[str] = None
    email: Optional[EmailStr] = None


# ====== Schemas ======
class ScheduleCreate(BaseModel):
    name: constr(strip_whitespace=True, min_length=1, max_length=255)
    report_type: Literal[
        "market_snapshot",
        "new_listings",
        "inventory",
        "closed",
        "price_bands",
        "new_listings_gallery",
        "featured_listings",
    ]
    city: Optional[str] = None
    zip_codes: Optional[List[str]] = None
    lookback_days: int = 30
    cadence: str = Field(..., pattern="^(weekly|monthly)$")
    weekly_dow: Optional[int] = Field(None, ge=0, le=6)  # 0=Sun, 6=Sat
    monthly_dom: Optional[int] = Field(None, ge=1, le=28)  # 1-28
    send_hour: int = Field(9, ge=0, le=23)
    send_minute: int = Field(0, ge=0, le=59)
    recipients: List[Union[RecipientInput, EmailStr]] = Field(..., min_items=1)  # Support both typed and legacy plain emails
    include_attachment: bool = False
    active: bool = True


class ScheduleUpdate(BaseModel):
    name: Optional[str] = None
    city: Optional[str] = None
    zip_codes: Optional[List[str]] = None
    lookback_days: Optional[int] = None
    cadence: Optional[str] = Field(None, pattern="^(weekly|monthly)$")
    weekly_dow: Optional[int] = Field(None, ge=0, le=6)
    monthly_dom: Optional[int] = Field(None, ge=1, le=28)
    send_hour: Optional[int] = Field(None, ge=0, le=23)
    send_minute: Optional[int] = Field(None, ge=0, le=59)
    recipients: Optional[List[Union[RecipientInput, EmailStr]]] = None  # Support both typed and legacy plain emails
    include_attachment: Optional[bool] = None
    active: Optional[bool] = None


class ScheduleRow(BaseModel):
    id: str
    name: str
    report_type: str
    city: Optional[str] = None
    zip_codes: Optional[List[str]] = None
    lookback_days: int
    cadence: str
    weekly_dow: Optional[int] = None
    monthly_dom: Optional[int] = None
    send_hour: int
    send_minute: int
    recipients: List[str]  # Raw JSON strings from DB
    resolved_recipients: Optional[List[Dict[str, Any]]] = None  # Decoded recipient objects for frontend
    include_attachment: bool
    active: bool
    last_run_at: Optional[str] = None
    next_run_at: Optional[str] = None
    created_at: str


class ScheduleRunRow(BaseModel):
    id: str
    schedule_id: str
    report_run_id: Optional[str] = None
    status: str
    error: Optional[str] = None
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    created_at: str


# ====== Helpers ======
def require_account_id(request: Request) -> str:
    """
    Returns the account_id set by AuthContextMiddleware.
    """
    account_id = getattr(request.state, "account_id", None)
    if not account_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return account_id


def validate_recipient_ownership(cur, account_id: str, recipient: RecipientInput) -> bool:
    """
    Validate that the account has permission to send to this recipient.
    
    Returns True if valid, False otherwise.
    """
    if recipient.type == "manual_email":
        # Manual emails don't require ownership check
        return True
    
    elif recipient.type == "contact":
        # Verify contact belongs to this account
        if not recipient.id:
            return False
        cur.execute("""
            SELECT 1 FROM contacts 
            WHERE id = %s::uuid AND account_id = %s::uuid
        """, (recipient.id, account_id))
        return cur.fetchone() is not None
    
    elif recipient.type == "sponsored_agent":
        # Verify sponsorship relationship
        if not recipient.id:
            return False
        cur.execute("""
            SELECT 1 FROM accounts 
            WHERE id = %s::uuid AND sponsor_account_id = %s::uuid
        """, (recipient.id, account_id))
        return cur.fetchone() is not None
    
    return False


def encode_recipients(recipients: List[Union[RecipientInput, EmailStr, str]], cur=None, account_id: str = None) -> List[str]:
    """
    Convert RecipientInput objects or plain emails into JSON-encoded strings for DB storage.
    
    Supports both:
    - RecipientInput objects (new typed format)
    - Plain email strings (legacy format, converted to manual_email type)
    
    If cur and account_id are provided, validates ownership of typed recipients.
    """
    encoded = []
    for r in recipients:
        if isinstance(r, RecipientInput):
            # Validate ownership if DB cursor provided
            if cur and account_id and not validate_recipient_ownership(cur, account_id, r):
                print(f"⚠️  Skipping recipient {r.type}:{r.id} - no permission for account {account_id}")
                continue
            encoded.append(json.dumps(r.model_dump(exclude_none=True)))
        elif isinstance(r, str):
            # Legacy plain email or already JSON string
            if r.startswith("{"):
                # Already JSON encoded
                encoded.append(r)
            else:
                # Plain email - convert to typed format
                encoded.append(json.dumps({"type": "manual_email", "email": r}))
        else:
            # EmailStr type
            encoded.append(json.dumps({"type": "manual_email", "email": str(r)}))
    return encoded


def decode_recipients(recipients: List[str]) -> List[Dict[str, Any]]:
    """
    Decode JSON-encoded recipient strings into dictionaries for frontend.
    
    Handles both:
    - JSON objects: {"type":"contact","id":"..."}
    - Plain emails: converts to {"type":"manual_email","email":"..."}
    """
    decoded = []
    for r in recipients:
        try:
            if r.startswith("{"):
                decoded.append(json.loads(r))
            else:
                # Legacy plain email
                decoded.append({"type": "manual_email", "email": r})
        except (json.JSONDecodeError, AttributeError):
            # If parsing fails, treat as plain email
            decoded.append({"type": "manual_email", "email": r})
    return decoded


def validate_schedule_params(cadence: str, weekly_dow: Optional[int], monthly_dom: Optional[int]):
    """
    Validate that cadence-specific parameters are provided.
    """
    if cadence == "weekly" and weekly_dow is None:
        raise HTTPException(
            status_code=400, 
            detail="weekly_dow (0-6) required for weekly cadence"
        )
    if cadence == "monthly" and monthly_dom is None:
        raise HTTPException(
            status_code=400,
            detail="monthly_dom (1-28) required for monthly cadence"
        )


# ====== Routes ======
@router.post("/schedules", status_code=status.HTTP_201_CREATED)
def create_schedule(
    payload: ScheduleCreate, 
    request: Request, 
    account_id: str = Depends(require_account_id)
):
    """
    Create a new schedule.
    Validates cadence-specific parameters and stores with RLS.
    Supports typed recipients (contact, sponsored_agent, manual_email).
    """
    # Validate cadence params
    validate_schedule_params(payload.cadence, payload.weekly_dow, payload.monthly_dom)
    
    with db_conn() as conn:
        set_rls(conn, account_id)
        cur = conn.cursor()
        
        # Encode recipients to JSON strings (with ownership validation)
        encoded_recipients = encode_recipients(payload.recipients, cur=cur, account_id=account_id)
        
        if not encoded_recipients:
            raise HTTPException(
                status_code=400,
                detail="No valid recipients provided"
            )
        
        # Convert recipients list to PostgreSQL array
        # Escape quotes and format for Postgres TEXT[] literal
        recipients_escaped = [r.replace('"', '\\"') for r in encoded_recipients]
        recipients_array = "{\"" + "\",\"".join(recipients_escaped) + "\"}"
        
        zip_codes_array = None
        if payload.zip_codes:
            zip_codes_array = "{" + ",".join(payload.zip_codes) + "}"
        
        cur.execute("""
            INSERT INTO schedules (
                account_id, name, report_type, city, zip_codes, lookback_days,
                cadence, weekly_dow, monthly_dom, send_hour, send_minute,
                recipients, include_attachment, active
            ) VALUES (
                %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s,
                %s, %s, %s
            )
            RETURNING id::text, name, report_type, city, zip_codes, lookback_days,
                      cadence, weekly_dow, monthly_dom, send_hour, send_minute,
                      recipients, include_attachment, active,
                      last_run_at, next_run_at, created_at
        """, (
            account_id, payload.name, payload.report_type, payload.city, zip_codes_array,
            payload.lookback_days, payload.cadence, payload.weekly_dow, payload.monthly_dom,
            payload.send_hour, payload.send_minute, recipients_array,
            payload.include_attachment, payload.active
        ))
        
        row = cur.fetchone()
        conn.commit()
        
        recipients_raw = row[11]
        return {
            "id": row[0],
            "name": row[1],
            "report_type": row[2],
            "city": row[3],
            "zip_codes": row[4],
            "lookback_days": row[5],
            "cadence": row[6],
            "weekly_dow": row[7],
            "monthly_dom": row[8],
            "send_hour": row[9],
            "send_minute": row[10],
            "recipients": recipients_raw,  # Raw for backwards compat
            "resolved_recipients": decode_recipients(recipients_raw),  # Decoded for frontend
            "include_attachment": row[12],
            "active": row[13],
            "last_run_at": row[14].isoformat() if row[14] else None,
            "next_run_at": row[15].isoformat() if row[15] else None,
            "created_at": row[16].isoformat()
        }


@router.get("/schedules")
def list_schedules(
    request: Request, 
    account_id: str = Depends(require_account_id),
    active_only: bool = True
):
    """
    List all schedules for the account.
    """
    with db_conn() as conn:
        set_rls(conn, account_id)
        cur = conn.cursor()
        
        query = """
            SELECT id::text, name, report_type, city, zip_codes, lookback_days,
                   cadence, weekly_dow, monthly_dom, send_hour, send_minute,
                   recipients, include_attachment, active,
                   last_run_at, next_run_at, created_at
            FROM schedules
        """
        
        if active_only:
            query += " WHERE active = true"
        
        query += " ORDER BY created_at DESC"
        
        cur.execute(query)
        rows = cur.fetchall()
        
        schedules = []
        for row in rows:
            recipients_raw = row[11]
            schedules.append({
                "id": row[0],
                "name": row[1],
                "report_type": row[2],
                "city": row[3],
                "zip_codes": row[4],
                "lookback_days": row[5],
                "cadence": row[6],
                "weekly_dow": row[7],
                "monthly_dom": row[8],
                "send_hour": row[9],
                "send_minute": row[10],
                "recipients": recipients_raw,  # Raw for backwards compat
                "resolved_recipients": decode_recipients(recipients_raw),  # Decoded for frontend
                "include_attachment": row[12],
                "active": row[13],
                "last_run_at": row[14].isoformat() if row[14] else None,
                "next_run_at": row[15].isoformat() if row[15] else None,
                "created_at": row[16].isoformat()
            })
        
        return {"schedules": schedules, "count": len(schedules)}


@router.get("/schedules/{schedule_id}")
def get_schedule(
    schedule_id: str,
    request: Request, 
    account_id: str = Depends(require_account_id)
):
    """
    Get a single schedule by ID.
    """
    with db_conn() as conn:
        set_rls(conn, account_id)
        cur = conn.cursor()
        
        cur.execute("""
            SELECT id::text, name, report_type, city, zip_codes, lookback_days,
                   cadence, weekly_dow, monthly_dom, send_hour, send_minute,
                   recipients, include_attachment, active,
                   last_run_at, next_run_at, created_at
            FROM schedules
            WHERE id = %s::uuid
        """, (schedule_id,))
        
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Schedule not found")
        
        recipients_raw = row[11]
        return {
            "id": row[0],
            "name": row[1],
            "report_type": row[2],
            "city": row[3],
            "zip_codes": row[4],
            "lookback_days": row[5],
            "cadence": row[6],
            "weekly_dow": row[7],
            "monthly_dom": row[8],
            "send_hour": row[9],
            "send_minute": row[10],
            "recipients": recipients_raw,  # Raw for backwards compat
            "resolved_recipients": decode_recipients(recipients_raw),  # Decoded for frontend
            "include_attachment": row[12],
            "active": row[13],
            "last_run_at": row[14].isoformat() if row[14] else None,
            "next_run_at": row[15].isoformat() if row[15] else None,
            "created_at": row[16].isoformat()
        }


@router.patch("/schedules/{schedule_id}")
def update_schedule(
    schedule_id: str,
    payload: ScheduleUpdate,
    request: Request, 
    account_id: str = Depends(require_account_id)
):
    """
    Update a schedule.
    Nulls out next_run_at so ticker recomputes on next tick.
    """
    # Build dynamic update query
    updates = []
    params = []
    
    if payload.name is not None:
        updates.append("name = %s")
        params.append(payload.name)
    
    if payload.city is not None:
        updates.append("city = %s")
        params.append(payload.city)
    
    if payload.zip_codes is not None:
        zip_codes_array = "{" + ",".join(payload.zip_codes) + "}" if payload.zip_codes else None
        updates.append("zip_codes = %s")
        params.append(zip_codes_array)
    
    if payload.lookback_days is not None:
        updates.append("lookback_days = %s")
        params.append(payload.lookback_days)
    
    if payload.cadence is not None:
        updates.append("cadence = %s")
        params.append(payload.cadence)
    
    if payload.weekly_dow is not None:
        updates.append("weekly_dow = %s")
        params.append(payload.weekly_dow)
    
    if payload.monthly_dom is not None:
        updates.append("monthly_dom = %s")
        params.append(payload.monthly_dom)
    
    if payload.send_hour is not None:
        updates.append("send_hour = %s")
        params.append(payload.send_hour)
    
    if payload.send_minute is not None:
        updates.append("send_minute = %s")
        params.append(payload.send_minute)
    
    # Note: recipients validation happens below after DB connection is established
    recipients_to_update = payload.recipients
    
    if payload.include_attachment is not None:
        updates.append("include_attachment = %s")
        params.append(payload.include_attachment)
    
    if payload.active is not None:
        updates.append("active = %s")
        params.append(payload.active)
    
    if not updates and recipients_to_update is None:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    with db_conn() as conn:
        set_rls(conn, account_id)
        cur = conn.cursor()
        
        # Handle recipients separately to validate ownership
        if recipients_to_update is not None:
            encoded_recipients = encode_recipients(recipients_to_update, cur=cur, account_id=account_id)
            if not encoded_recipients:
                raise HTTPException(
                    status_code=400,
                    detail="No valid recipients provided"
                )
            recipients_escaped = [r.replace('"', '\\"') for r in encoded_recipients]
            recipients_array = "{\"" + "\",\"".join(recipients_escaped) + "\"}"
            updates.append("recipients = %s")
            params.append(recipients_array)
        
        if not updates:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        # Always null out next_run_at on updates so ticker recomputes
        updates.append("next_run_at = NULL")
        
        # Add schedule_id to params
        params.append(schedule_id)
        
        query = f"""
            UPDATE schedules
            SET {", ".join(updates)}
            WHERE id = %s::uuid
            RETURNING id::text
        """
        
        cur.execute(query, params)
        row = cur.fetchone()
        conn.commit()
        
        if not row:
            raise HTTPException(status_code=404, detail="Schedule not found")
        
        return {"id": row[0], "message": "Schedule updated"}


@router.delete("/schedules/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_schedule(
    schedule_id: str,
    request: Request, 
    account_id: str = Depends(require_account_id)
):
    """
    Delete a schedule.
    Cascade deletes schedule_runs via foreign key.
    """
    with db_conn() as conn:
        set_rls(conn, account_id)
        cur = conn.cursor()
        
        cur.execute("""
            DELETE FROM schedules
            WHERE id = %s::uuid
            RETURNING id
        """, (schedule_id,))
        
        row = cur.fetchone()
        conn.commit()
        
        if not row:
            raise HTTPException(status_code=404, detail="Schedule not found")
        
        return None


@router.get("/schedules/{schedule_id}/runs")
def list_schedule_runs(
    schedule_id: str,
    request: Request, 
    account_id: str = Depends(require_account_id),
    limit: int = 50
):
    """
    List execution history for a schedule.
    """
    with db_conn() as conn:
        set_rls(conn, account_id)
        cur = conn.cursor()
        
        # Verify schedule exists and belongs to account (via RLS)
        cur.execute("""
            SELECT id FROM schedules WHERE id = %s::uuid
        """, (schedule_id,))
        
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="Schedule not found")
        
        # Fetch runs
        cur.execute("""
            SELECT id::text, schedule_id::text, report_run_id::text,
                   status, error, started_at, finished_at, created_at
            FROM schedule_runs
            WHERE schedule_id = %s::uuid
            ORDER BY created_at DESC
            LIMIT %s
        """, (schedule_id, limit))
        
        rows = cur.fetchall()
        
        runs = []
        for row in rows:
            runs.append({
                "id": row[0],
                "schedule_id": row[1],
                "report_run_id": row[2],
                "status": row[3],
                "error": row[4],
                "started_at": row[5].isoformat() if row[5] else None,
                "finished_at": row[6].isoformat() if row[6] else None,
                "created_at": row[7].isoformat()
            })
        
        return {"runs": runs, "count": len(runs)}

