from fastapi import Depends, HTTPException, Request
from ..db import db_conn


def get_admin_user(request: Request):
    """
    Dependency that verifies the current user is a platform admin.
    
    Platform admin is determined by users.is_platform_admin = TRUE.
    This is SEPARATE from tenant roles (account_users.role = OWNER/ADMIN/MEMBER).
    
    Raises 401 if not authenticated.
    Raises 403 if not a platform admin.
    Returns the user info if platform admin.
    """
    # Get user info from request.state (set by auth middleware)
    user_info = getattr(request.state, "user", None)
    
    if not user_info:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Check platform admin flag (NOT tenant role)
    is_platform_admin = user_info.get("is_platform_admin", False)
    
    if not is_platform_admin:
        raise HTTPException(status_code=403, detail="Platform admin only")
    
    return user_info

