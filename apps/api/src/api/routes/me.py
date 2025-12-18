from fastapi import APIRouter, Request, HTTPException
from ..db import db_conn

router = APIRouter(prefix="/v1")

@router.get("/me")
def me(request: Request):
    """
    Get current user information including role, account type, and platform admin status.
    Returns: { account_id, user_id, email, role, account_type, is_platform_admin }
    """
    # Auth middleware already set account_id and user info
    account_id = getattr(request.state, "account_id", None)
    user_info = getattr(request.state, "user", None)
    
    if not account_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    # Fetch account_type from accounts table
    with db_conn() as (conn, cur):
        cur.execute("""
            SELECT account_type
            FROM accounts
            WHERE id = %s::uuid
        """, (account_id,))
        account_row = cur.fetchone()
        account_type = account_row[0] if account_row else "REGULAR"
    
    # If auth middleware set user info (JWT authentication), use it
    if user_info and user_info.get("id"):
        return {
            "account_id": account_id,
            "user_id": user_info.get("id"),
            "email": user_info.get("email"),
            "role": user_info.get("role", "USER"),
            "account_type": account_type,
            "is_platform_admin": user_info.get("is_platform_admin", False)
        }
    
    # Fallback: look up first user in account (API key authentication)
    with db_conn() as (conn, cur):
        cur.execute("""
            SELECT id::text AS user_id, email, role, is_platform_admin 
            FROM users 
            WHERE account_id=%s::uuid 
            ORDER BY created_at ASC 
            LIMIT 1
        """, (account_id,))
        row = cur.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="User not found for account")
        
        return {
            "account_id": account_id,
            "user_id": row[0],
            "email": row[1],
            "role": (row[2] or "USER").upper(),
            "account_type": account_type,
            "is_platform_admin": bool(row[3]) if row[3] is not None else False
        }

