# PHASE 29C - COMPLETE IMPLEMENTATION GUIDE FOR CURSOR

**Date:** November 14, 2025  
**Dependencies:** Phase 29A+B must be deployed and migration run

---

## ✅ COMPLETED

- ✅ 29C.1: Extended `set_rls()` in `apps/api/src/api/db.py`
- ✅ 29C.2: Created `apps/api/src/api/services/accounts.py` with helper functions
- ✅ Phase 29A migration applied to database

---

## 📋 REMAINING TASKS FOR CURSOR

Execute these tasks in order. Each is self-contained.

---

### **TASK 29C.3A: Account Switching API Endpoints**

**File:** `apps/api/src/api/routes/account.py`

**Add these endpoints:**

```python
from ..services.accounts import (
    get_user_accounts,
    verify_user_account_access,
    get_account_info
)

@router.get("/account/accounts")
def list_user_accounts(request: Request, account_id: str = Depends(require_account_id)):
    """
    Phase 29C: List all accounts the current user belongs to.
    
    Returns list of accounts with user's role in each.
    """
    # Get current user from request context (set by AuthContextMiddleware)
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise HTTPException(status_code=401, detail="User ID not found in session")
    
    with db_conn() as (conn, cur):
        accounts = get_user_accounts(cur, user_id)
        return {"accounts": accounts, "count": len(accounts)}


@router.post("/account/use")
def switch_account(
    body: dict,
    response: Response,
    request: Request,
    account_id: str = Depends(require_account_id)
):
    """
    Phase 29C: Switch current account context.
    
    Body: { "account_id": "uuid" }
    
    Sets mr_account_id cookie to chosen account.
    """
    new_account_id = body.get("account_id")
    if not new_account_id:
        raise HTTPException(status_code=400, detail="account_id required")
    
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise HTTPException(status_code=401, detail="User ID not found in session")
    
    with db_conn() as (conn, cur):
        # Verify user has access to this account
        if not verify_user_account_access(cur, user_id, new_account_id):
            raise HTTPException(
                status_code=403,
                detail="You do not have access to this account"
            )
        
        # Get account info
        account = get_account_info(cur, new_account_id)
        if not account:
            raise HTTPException(status_code=404, detail="Account not found")
    
    # Set cookie for account context
    response.set_cookie(
        key="mr_account_id",
        value=new_account_id,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=30 * 24 * 60 * 60  # 30 days
    )
    
    return {
        "ok": True,
        "current_account_id": new_account_id,
        "account_type": account["account_type"],
        "plan_slug": account["plan_slug"]
    }
```

**Note:** Ensure `AuthContextMiddleware` sets `request.state.user_id` from the JWT/session.

---

### **TASK 29C.4A: Affiliate Service Functions**

**Create File:** `apps/api/src/api/services/affiliates.py`

```python
"""
Affiliate Services

Phase 29C: Industry affiliate account management
"""

from typing import Dict, Any, List


def get_sponsored_accounts(cur, affiliate_account_id: str) -> List[Dict[str, Any]]:
    """
    Get all accounts sponsored by this affiliate.
    
    Args:
        cur: Database cursor
        affiliate_account_id: Affiliate account UUID
    
    Returns:
        List of sponsored accounts with usage metrics
    """
    cur.execute("""
        SELECT
            a.id::text AS account_id,
            a.name,
            a.plan_slug,
            a.account_type,
            a.created_at,
            COALESCE(u.report_count, 0) AS reports_this_month,
            u.last_report_at
        FROM accounts a
        LEFT JOIN (
            SELECT 
                account_id,
                COUNT(*) AS report_count,
                MAX(generated_at) AS last_report_at
            FROM report_generations
            WHERE generated_at >= DATE_TRUNC('month', NOW())
              AND status IN ('completed', 'processing')
            GROUP BY account_id
        ) u ON u.account_id = a.id
        WHERE a.sponsor_account_id = %s::uuid
        ORDER BY u.report_count DESC NULLS LAST, a.created_at DESC
    """, (affiliate_account_id,))
    
    accounts = []
    for row in cur.fetchall():
        accounts.append({
            "account_id": row[0],
            "name": row[1],
            "plan_slug": row[2],
            "account_type": row[3],
            "created_at": row[4].isoformat() if row[4] else None,
            "reports_this_month": row[5],
            "last_report_at": row[6].isoformat() if row[6] else None,
        })
    
    return accounts


def get_affiliate_overview(cur, affiliate_account_id: str) -> Dict[str, Any]:
    """
    Get overview metrics for an affiliate account.
    
    Args:
        cur: Database cursor
        affiliate_account_id: Affiliate account UUID
    
    Returns:
        Overview metrics dictionary
    """
    sponsored = get_sponsored_accounts(cur, affiliate_account_id)
    
    total_reports = sum(acc["reports_this_month"] for acc in sponsored)
    
    return {
        "sponsored_count": len(sponsored),
        "total_reports_this_month": total_reports,
    }


def verify_affiliate_account(cur, account_id: str) -> bool:
    """
    Verify that an account is an industry affiliate.
    
    Args:
        cur: Database cursor
        account_id: Account UUID to check
    
    Returns:
        True if account_type is INDUSTRY_AFFILIATE
    """
    cur.execute("""
        SELECT account_type
        FROM accounts
        WHERE id = %s::uuid
    """, (account_id,))
    
    row = cur.fetchone()
    if not row:
        return False
    
    return row[0] == 'INDUSTRY_AFFILIATE'
```

---

### **TASK 29C.4B: Affiliate API Routes**

**Create File:** `apps/api/src/api/routes/affiliates.py`

```python
"""
Affiliate API Routes

Phase 29C: Industry affiliate dashboard and management
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from ..db import db_conn
from ..services.affiliates import (
    get_affiliate_overview,
    get_sponsored_accounts,
    verify_affiliate_account
)
from .reports import require_account_id

router = APIRouter(prefix="/v1/affiliate", tags=["affiliate"])


@router.get("/overview")
def get_overview(request: Request, account_id: str = Depends(require_account_id)):
    """
    Get affiliate dashboard overview.
    
    Phase 29C: Shows sponsored accounts and usage metrics.
    
    Returns 403 if account is not INDUSTRY_AFFILIATE.
    """
    with db_conn() as (conn, cur):
        # Verify this is an affiliate account
        if not verify_affiliate_account(cur, account_id):
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "not_affiliate_account",
                    "message": "This account is not an industry affiliate."
                }
            )
        
        # Get overview metrics
        overview = get_affiliate_overview(cur, account_id)
        
        # Get sponsored accounts list
        sponsored = get_sponsored_accounts(cur, account_id)
        
        # Get account info
        cur.execute("""
            SELECT id::text, name, account_type, plan_slug
            FROM accounts
            WHERE id = %s::uuid
        """, (account_id,))
        
        acc_row = cur.fetchone()
        
        return {
            "account": {
                "account_id": acc_row[0],
                "name": acc_row[1],
                "account_type": acc_row[2],
                "plan_slug": acc_row[3],
            },
            "overview": overview,
            "sponsored_accounts": sponsored,
        }
```

**Update:** `apps/api/src/api/main.py`

Add this import and route:
```python
from .routes.affiliates import router as affiliates_router

# In app setup:
app.include_router(affiliates_router)
```

---

### **TASK 29C.6A: Invite Sponsored Agent Endpoint**

**Add to:** `apps/api/src/api/routes/affiliates.py`

```python
from pydantic import BaseModel, EmailStr
import secrets


class InviteAgentRequest(BaseModel):
    name: str
    email: EmailStr
    default_city: str | None = None


@router.post("/invite-agent")
def invite_agent(
    body: InviteAgentRequest,
    request: Request,
    account_id: str = Depends(require_account_id)
):
    """
    Invite a new agent to be sponsored by this affiliate.
    
    Phase 29C: Creates new REGULAR account with sponsored_free plan.
    
    Body:
        name: Agent/company name
        email: Agent email
        default_city: Optional default city for reports
    
    Returns:
        account_id: New sponsored account ID
        user_id: New user ID
        token: Invite token for welcome link
    """
    with db_conn() as (conn, cur):
        # Verify this is an affiliate account
        if not verify_affiliate_account(cur, account_id):
            raise HTTPException(
                status_code=403,
                detail="Only industry affiliates can invite agents"
            )
        
        # Check if email already exists
        cur.execute("SELECT id FROM users WHERE email = %s", (body.email,))
        if cur.fetchone():
            raise HTTPException(
                status_code=400,
                detail="A user with this email already exists"
            )
        
        # Create new account
        cur.execute("""
            INSERT INTO accounts (name, slug, account_type, plan_slug, sponsor_account_id)
            VALUES (%s, %s, 'REGULAR', 'sponsored_free', %s::uuid)
            RETURNING id::text
        """, (
            body.name,
            body.name.lower().replace(' ', '-').replace('.', '')[:50],
            account_id
        ))
        new_account_id = cur.fetchone()[0]
        
        # Create new user
        cur.execute("""
            INSERT INTO users (account_id, email, is_active, email_verified, role)
            VALUES (%s::uuid, %s, true, false, 'member')
            RETURNING id::text
        """, (new_account_id, body.email))
        new_user_id = cur.fetchone()[0]
        
        # Create account_users entry (OWNER)
        cur.execute("""
            INSERT INTO account_users (account_id, user_id, role)
            VALUES (%s::uuid, %s::uuid, 'OWNER')
        """, (new_account_id, new_user_id))
        
        # Generate invite token
        token = secrets.token_urlsafe(32)
        
        # Store invite token (create table if needed)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS signup_tokens (
                id SERIAL PRIMARY KEY,
                token TEXT UNIQUE NOT NULL,
                user_id UUID NOT NULL REFERENCES users(id),
                account_id UUID NOT NULL REFERENCES accounts(id),
                used BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT NOW(),
                expires_at TIMESTAMP DEFAULT NOW() + INTERVAL '7 days'
            )
        """)
        
        cur.execute("""
            INSERT INTO signup_tokens (token, user_id, account_id)
            VALUES (%s, %s::uuid, %s::uuid)
        """, (token, new_user_id, new_account_id))
        
        conn.commit()
        
        # TODO: Send invitation email (Phase 29C - optional enhancement)
        # For now, just return the token
        
        return {
            "ok": True,
            "account_id": new_account_id,
            "user_id": new_user_id,
            "token": token,
            "invite_url": f"https://reportscompany-web.vercel.app/welcome?token={token}"
        }
```

---

## 🎯 NEXT STEPS AFTER BACKEND IS COMPLETE

Once all backend tasks (29C.3A, 29C.4A, 29C.4B, 29C.6A) are done:

1. **Test Backend Endpoints:**
   - GET /v1/account/accounts
   - POST /v1/account/use
   - GET /v1/affiliate/overview
   - POST /v1/affiliate/invite-agent

2. **Frontend Implementation (29C.3B, 29C.5, 29C.6B, 29C.6C):**
   - Account switcher component
   - Affiliate dashboard page
   - Invite modal
   - Welcome page

3. **Deploy & Test:**
   - Redeploy API with new routes
   - Test with Demo Account (set to INDUSTRY_AFFILIATE)
   - Create test invite and verify flow

---

**Status:** Ready for systematic backend implementation! 🚀

Execute each task in order, test endpoints, then proceed to frontend.

