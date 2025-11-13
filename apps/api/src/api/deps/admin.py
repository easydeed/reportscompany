from fastapi import Depends, HTTPException, Request
from ..db import db_conn


def get_admin_user(request: Request):
    """
    Dependency that verifies the current user has ADMIN role.
    Raises 403 if not admin.
    Returns the user info if admin.
    """
    # Get user info from request.state (set by auth middleware)
    user_info = getattr(request.state, "user", None)
    
    if not user_info:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    role = user_info.get("role", "USER")
    
    if role != "ADMIN":
        raise HTTPException(status_code=403, detail="admin_only")
    
    return user_info

