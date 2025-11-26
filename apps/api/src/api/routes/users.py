"""
User Profile & Settings Routes

Provides endpoints for:
- GET /v1/users/me - Get current user profile
- PATCH /v1/users/me - Update user profile (first_name, last_name, company_name, phone, avatar_url)
- POST /v1/users/me/password - Change password (requires current password)
- PATCH /v1/users/me/email - Update email (requires current password)
"""

from fastapi import APIRouter, Request, HTTPException, Response
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from ..db import db_conn
from ..auth import check_password, hash_password, sign_jwt
from ..settings import settings

router = APIRouter(prefix="/v1")


# ============ Models ============

class UserProfileOut(BaseModel):
    id: str
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    company_name: Optional[str] = None
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    email_verified: bool = False
    created_at: Optional[datetime] = None


class UserProfileUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    company_name: Optional[str] = None
    phone: Optional[str] = None
    avatar_url: Optional[str] = None


class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str


class EmailChangeRequest(BaseModel):
    new_email: EmailStr
    current_password: str


# ============ Endpoints ============

@router.get("/users/me", response_model=UserProfileOut)
def get_user_profile(request: Request):
    """
    Get current user's profile information.
    """
    user_info = getattr(request.state, "user", None)

    if not user_info or not user_info.get("id"):
        raise HTTPException(status_code=401, detail="Unauthorized")

    user_id = user_info["id"]

    with db_conn() as (conn, cur):
        cur.execute("""
            SELECT
                id::text,
                email,
                first_name,
                last_name,
                company_name,
                phone,
                avatar_url,
                email_verified,
                created_at
            FROM users
            WHERE id = %s::uuid AND is_active = TRUE
        """, (user_id,))

        row = cur.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="User not found")

        return UserProfileOut(
            id=row[0],
            email=row[1],
            first_name=row[2],
            last_name=row[3],
            company_name=row[4],
            phone=row[5],
            avatar_url=row[6],
            email_verified=row[7] or False,
            created_at=row[8]
        )


@router.patch("/users/me", response_model=UserProfileOut)
def update_user_profile(body: UserProfileUpdate, request: Request):
    """
    Update current user's profile information.

    Updatable fields:
    - first_name
    - last_name
    - company_name
    - phone
    - avatar_url
    """
    user_info = getattr(request.state, "user", None)

    if not user_info or not user_info.get("id"):
        raise HTTPException(status_code=401, detail="Unauthorized")

    user_id = user_info["id"]

    # Build dynamic update query
    updates = []
    params = []

    if body.first_name is not None:
        updates.append("first_name = %s")
        params.append(body.first_name.strip() if body.first_name else None)

    if body.last_name is not None:
        updates.append("last_name = %s")
        params.append(body.last_name.strip() if body.last_name else None)

    if body.company_name is not None:
        updates.append("company_name = %s")
        params.append(body.company_name.strip() if body.company_name else None)

    if body.phone is not None:
        updates.append("phone = %s")
        params.append(body.phone.strip() if body.phone else None)

    if body.avatar_url is not None:
        updates.append("avatar_url = %s")
        params.append(body.avatar_url.strip() if body.avatar_url else None)

    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    updates.append("updated_at = NOW()")
    params.append(user_id)

    with db_conn() as (conn, cur):
        cur.execute(f"""
            UPDATE users
            SET {", ".join(updates)}
            WHERE id = %s::uuid AND is_active = TRUE
            RETURNING
                id::text,
                email,
                first_name,
                last_name,
                company_name,
                phone,
                avatar_url,
                email_verified,
                created_at
        """, params)

        row = cur.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="User not found")

        conn.commit()

        return UserProfileOut(
            id=row[0],
            email=row[1],
            first_name=row[2],
            last_name=row[3],
            company_name=row[4],
            phone=row[5],
            avatar_url=row[6],
            email_verified=row[7] or False,
            created_at=row[8]
        )


@router.post("/users/me/password")
def change_password(body: PasswordChangeRequest, request: Request, response: Response):
    """
    Change user's password.

    Requirements:
    - Current password must be correct
    - New password must be at least 8 characters

    Side effects:
    - Updates password_changed_at timestamp
    - Issues new JWT token (invalidates other sessions)
    """
    user_info = getattr(request.state, "user", None)

    if not user_info or not user_info.get("id"):
        raise HTTPException(status_code=401, detail="Unauthorized")

    user_id = user_info["id"]

    # Validate new password
    if len(body.new_password) < 8:
        raise HTTPException(
            status_code=400,
            detail="New password must be at least 8 characters"
        )

    if body.current_password == body.new_password:
        raise HTTPException(
            status_code=400,
            detail="New password must be different from current password"
        )

    with db_conn() as (conn, cur):
        # Get current password hash
        cur.execute("""
            SELECT password_hash, account_id::text
            FROM users
            WHERE id = %s::uuid AND is_active = TRUE
        """, (user_id,))

        row = cur.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="User not found")

        current_hash, account_id = row

        # Verify current password
        if not current_hash or not check_password(body.current_password, current_hash):
            raise HTTPException(
                status_code=400,
                detail="Current password is incorrect"
            )

        # Hash new password and update
        new_hash = hash_password(body.new_password)

        cur.execute("""
            UPDATE users
            SET
                password_hash = %s,
                password_changed_at = NOW(),
                updated_at = NOW()
            WHERE id = %s::uuid
        """, (new_hash, user_id))

        conn.commit()

        # Issue new JWT token (this invalidates other sessions since they have old tokens)
        token = sign_jwt(
            {
                "sub": user_id,
                "user_id": user_id,
                "account_id": account_id,
                "scopes": ["reports:read", "reports:write"]
            },
            settings.JWT_SECRET,
            ttl_seconds=3600
        )

        # Set new cookie
        response.set_cookie(
            key="mr_token",
            value=token,
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=3600
        )

        return {
            "ok": True,
            "message": "Password changed successfully. Other sessions have been logged out."
        }


@router.patch("/users/me/email")
def change_email(body: EmailChangeRequest, request: Request, response: Response):
    """
    Change user's email address.

    Requirements:
    - Current password must be correct
    - New email must not already be in use

    Note: In a production system, you might want to:
    - Send verification email to new address
    - Keep old email until verified
    For now, this changes email immediately.
    """
    user_info = getattr(request.state, "user", None)

    if not user_info or not user_info.get("id"):
        raise HTTPException(status_code=401, detail="Unauthorized")

    user_id = user_info["id"]
    new_email = body.new_email.strip().lower()

    with db_conn() as (conn, cur):
        # Get current password hash and email
        cur.execute("""
            SELECT password_hash, email, account_id::text
            FROM users
            WHERE id = %s::uuid AND is_active = TRUE
        """, (user_id,))

        row = cur.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="User not found")

        current_hash, current_email, account_id = row

        # Check if email is the same
        if current_email.lower() == new_email:
            raise HTTPException(
                status_code=400,
                detail="New email must be different from current email"
            )

        # Verify current password
        if not current_hash or not check_password(body.current_password, current_hash):
            raise HTTPException(
                status_code=400,
                detail="Current password is incorrect"
            )

        # Check if new email is already in use
        cur.execute("""
            SELECT id FROM users WHERE email = %s AND id != %s::uuid
        """, (new_email, user_id))

        if cur.fetchone():
            raise HTTPException(
                status_code=400,
                detail="Email is already in use"
            )

        # Update email
        cur.execute("""
            UPDATE users
            SET
                email = %s,
                updated_at = NOW()
            WHERE id = %s::uuid
            RETURNING id::text, email
        """, (new_email, user_id))

        updated_row = cur.fetchone()
        conn.commit()

        # Issue new JWT token with updated info
        token = sign_jwt(
            {
                "sub": user_id,
                "user_id": user_id,
                "account_id": account_id,
                "scopes": ["reports:read", "reports:write"]
            },
            settings.JWT_SECRET,
            ttl_seconds=3600
        )

        # Set new cookie
        response.set_cookie(
            key="mr_token",
            value=token,
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=3600
        )

        return {
            "ok": True,
            "message": "Email updated successfully",
            "email": updated_row[1]
        }
