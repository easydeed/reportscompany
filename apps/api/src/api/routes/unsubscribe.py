from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr
import hmac
import hashlib
import os
from ..db import db_conn

router = APIRouter(prefix="/v1")

# Secret for HMAC token generation/validation
# MUST match EMAIL_UNSUB_SECRET in Worker
EMAIL_UNSUB_SECRET = os.getenv("EMAIL_UNSUB_SECRET", "dev-unsubscribe-secret-change-in-prod")


# ====== Schemas ======
class UnsubscribeRequest(BaseModel):
    email: EmailStr
    token: str
    reason: str = "user_request"


# ====== Helpers ======
def generate_unsubscribe_token(account_id: str, email: str) -> str:
    """
    Generate HMAC token for unsubscribe links.
    Format: HMAC-SHA256(account_id:email, secret)
    MUST match the format in worker/email/send.py
    """
    message = f"{account_id}:{email}"
    return hmac.new(
        EMAIL_UNSUB_SECRET.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()


def verify_unsubscribe_token(account_id: str, email: str, token: str) -> bool:
    """
    Verify HMAC token matches account_id:email.
    """
    expected_token = generate_unsubscribe_token(account_id, email)
    return hmac.compare_digest(expected_token, token)


# ====== Routes ======
@router.post("/email/unsubscribe", status_code=status.HTTP_200_OK)
def unsubscribe_email(payload: UnsubscribeRequest):
    """
    Unsubscribe an email address from all schedules.
    
    Token format: HMAC-SHA256(email:account_id, secret)
    
    This endpoint does NOT require authentication - it uses the HMAC token
    to verify the unsubscribe request came from a legitimate email link.
    """
    # Extract account_id from database by finding schedules with this email
    with db_conn() as conn:
        cur = conn.cursor()
        
        # Find account_id from schedules that contain this email
        cur.execute("""
            SELECT DISTINCT account_id::text
            FROM schedules
            WHERE %s = ANY(recipients)
            LIMIT 1
        """, (payload.email,))
        
        row = cur.fetchone()
        if not row:
            # Email not found in any schedules - still return success (idempotent)
            return {"message": "Email unsubscribed"}
        
        account_id = row[0]
        
        # Verify token
        if not verify_unsubscribe_token(account_id, payload.email, payload.token):
            raise HTTPException(
                status_code=400,
                detail="Invalid unsubscribe token"
            )
        
        # Insert into suppressions (idempotent due to UNIQUE constraint)
        cur.execute("""
            INSERT INTO email_suppressions (account_id, email, reason)
            VALUES (%s::uuid, %s, %s)
            ON CONFLICT (account_id, email) DO NOTHING
        """, (account_id, payload.email, payload.reason))
        
        conn.commit()
        
        return {"message": "Email unsubscribed successfully"}


@router.get("/email/unsubscribe/token")
def get_unsubscribe_token(email: str, account_id: str):
    """
    Generate an unsubscribe token for testing.
    
    WARNING: This endpoint should be disabled in production or require admin auth.
    It's provided for development/testing purposes only.
    """
    if os.getenv("ENVIRONMENT", "dev") == "production":
        raise HTTPException(status_code=404, detail="Not found")
    
    token = generate_unsubscribe_token(account_id, email)
    
    return {
        "email": email,
        "account_id": account_id,
        "token": token,
        "unsubscribe_url": f"/v1/email/unsubscribe?email={email}&token={token}"
    }

