from fastapi import APIRouter, Request, HTTPException
from ..db import db_conn

router = APIRouter(prefix="/v1")

@router.get("/me")
def me(request: Request):
    """
    Get current user information including role.
    Returns: { account_id, user_id, email, role }
    """
    # Auth middleware already set account_id and user info
    account_id = getattr(request.state, "account_id", None)
    user_info = getattr(request.state, "user", None)
    
    if not account_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    # If auth middleware set user info (JWT authentication), use it
    if user_info and user_info.get("id"):
        return {
            "account_id": account_id,
            "user_id": user_info.get("id"),
            "email": user_info.get("email"),
            "role": user_info.get("role", "USER")
        }
    
    # Fallback: look up first user in account (API key authentication)
    with db_conn() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT id::text AS user_id, email, role 
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
            "role": (row[2] or "USER").upper()
        }

