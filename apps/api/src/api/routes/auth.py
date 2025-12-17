from fastapi import APIRouter, HTTPException, Request, Response, status, BackgroundTasks
from pydantic import BaseModel, EmailStr
import psycopg
import logging
import uuid
from datetime import datetime
from ..settings import settings
from ..auth import sign_jwt, check_password, hash_password
from ..services.email import send_welcome_email

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1")

class LoginIn(BaseModel):
    email: EmailStr
    password: str

class LoginOut(BaseModel):
    access_token: str
    token_type: str = "bearer"

class RegisterIn(BaseModel):
    name: str
    email: EmailStr
    password: str

@router.post("/auth/login")
def login(body: LoginIn, response: Response):
    with psycopg.connect(settings.DATABASE_URL, autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute("""
              SELECT id::text, account_id::text, password_hash FROM users WHERE email=%s AND is_active=TRUE
            """, (body.email,))
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=401, detail="Invalid credentials")
            user_id, default_account_id, pw_hash = row
            if not pw_hash or not check_password(body.password, pw_hash):
                raise HTTPException(status_code=401, detail="Invalid credentials")
            
            # Prioritize INDUSTRY_AFFILIATE account if user belongs to one
            # This ensures affiliates land in their affiliate dashboard by default
            cur.execute("""
                SELECT a.id::text, a.account_type
                FROM account_users au
                JOIN accounts a ON a.id = au.account_id
                WHERE au.user_id = %s::uuid
                ORDER BY 
                    CASE 
                        WHEN a.account_type = 'INDUSTRY_AFFILIATE' THEN 1
                        WHEN a.id = %s::uuid THEN 2
                        ELSE 3
                    END
                LIMIT 1
            """, (user_id, default_account_id))
            account_row = cur.fetchone()
            account_id = account_row[0] if account_row else default_account_id

    token = sign_jwt({
        "sub": user_id,
        "user_id": user_id,
        "account_id": account_id,
        "scopes": ["reports:read", "reports:write"]
    }, settings.JWT_SECRET, ttl_seconds=3600)
    
    # Set HTTP-only cookie
    response.set_cookie(
        key="mr_token",
        value=token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=3600
    )
    
    return {"access_token": token}

# Optional seed endpoint for dev (remove/guard in prod)
class SeedIn(BaseModel):
    account_id: str
    email: EmailStr
    password: str
    name: str = "Demo User"

@router.post("/auth/seed-dev", status_code=status.HTTP_201_CREATED)
def seed_dev(body: SeedIn):
    with psycopg.connect(settings.DATABASE_URL, autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO users (account_id, email, password_hash, role) VALUES (%s,%s,%s,'owner') ON CONFLICT (email) DO NOTHING",
                        (body.account_id, body.email, hash_password(body.password)))
    return {"ok": True}


# Phase 29C: Accept Invite endpoint

class AcceptInviteRequest(BaseModel):
    token: str
    password: str


class AcceptInviteResponse(BaseModel):
    ok: bool
    access_token: str
    token_type: str = "bearer"
    user: dict


@router.post("/auth/register")
def register(body: RegisterIn, response: Response, background_tasks: BackgroundTasks):
    """
    Register a new user with a free account.

    Creates:
    - A new user with hashed password
    - A new REGULAR account on the free plan
    - Links user as OWNER of the account
    - Sends welcome email
    - Returns auth session (JWT + cookie)
    """
    name = body.name.strip()
    email = body.email.strip().lower()
    password = body.password
    
    # Basic validation
    if not name or not email or not password:
        raise HTTPException(
            status_code=400,
            detail="Name, email, and password are required"
        )
    
    if len(password) < 8:
        raise HTTPException(
            status_code=400,
            detail="Password must be at least 8 characters"
        )
    
    with psycopg.connect(settings.DATABASE_URL, autocommit=False) as conn:
        with conn.cursor() as cur:
            # 1. Check if email already exists
            cur.execute("""
                SELECT id FROM users WHERE email = %s
            """, (email,))
            
            if cur.fetchone():
                raise HTTPException(
                    status_code=400,
                    detail="Email is already registered."
                )
            
            # 2. Create account on free plan
            # Generate a URL-safe slug from the user's name + short unique suffix
            base_slug = name.lower().replace(' ', '-').replace('.', '').replace(',', '').replace("'", '')[:40]
            unique_suffix = uuid.uuid4().hex[:8]
            account_slug = f"{base_slug}-{unique_suffix}"
            
            cur.execute("""
                INSERT INTO accounts (name, slug, account_type, plan_slug)
                VALUES (%s, %s, 'REGULAR', 'free')
                RETURNING id::text
            """, (f"{name}'s Account", account_slug))
            
            account_id = cur.fetchone()[0]
            
            # 3. Create user
            password_hash = hash_password(password)
            
            cur.execute("""
                INSERT INTO users (account_id, email, password_hash, is_active, email_verified)
                VALUES (%s::uuid, %s, %s, TRUE, TRUE)
                RETURNING id::text
            """, (account_id, email, password_hash))
            
            user_id = cur.fetchone()[0]
            
            # 4. Link user to account as OWNER
            cur.execute("""
                INSERT INTO account_users (account_id, user_id, role)
                VALUES (%s::uuid, %s::uuid, 'OWNER')
            """, (account_id, user_id))
            
            conn.commit()
            
            # 5. Generate JWT and set cookie
            token = sign_jwt(
                {
                    "sub": user_id,
                    "user_id": user_id,
                    "account_id": account_id,
                    "scopes": ["reports:read", "reports:write"]
                },
                settings.JWT_SECRET,
                ttl_seconds=7 * 24 * 3600  # 7 days for new users
            )
            
            response.set_cookie(
                key="mr_token",
                value=token,
                httponly=True,
                secure=True,
                samesite="lax",
                max_age=7 * 24 * 60 * 60  # 7 days
            )

            # 6. Send welcome email in background
            try:
                background_tasks.add_task(send_welcome_email, email, name)
                logger.info(f"Welcome email queued for {email}")
            except Exception as e:
                # Don't fail registration if email fails
                logger.error(f"Failed to queue welcome email for {email}: {e}")

            return {"ok": True}


@router.post("/auth/accept-invite", response_model=AcceptInviteResponse)
def accept_invite(body: AcceptInviteRequest, response: Response):
    """
    Accept an invitation and activate a sponsored agent account.
    
    Phase 29C: Completes the invite flow by:
    - Validating the invite token
    - Setting the user's password
    - Marking the token as used
    - Returning auth session
    """
    token = body.token.strip()
    password = body.password
    
    # Validate password requirements
    if len(password) < 8:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "invalid_password",
                "message": "Password must be at least 8 characters long"
            }
        )
    
    with psycopg.connect(settings.DATABASE_URL, autocommit=False) as conn:
        with conn.cursor() as cur:
            # 1. Validate token from signup_tokens
            cur.execute("""
                SELECT user_id::text, account_id::text, expires_at, used_at
                FROM signup_tokens
                WHERE token = %s
            """, (token,))
            
            token_row = cur.fetchone()
            
            if not token_row:
                raise HTTPException(
                    status_code=400,
                    detail={
                        "error": "invalid_token",
                        "message": "Invite link is invalid or expired."
                    }
                )
            
            user_id, account_id, expires_at, used_at = token_row
            
            # Check if token already used
            if used_at is not None:
                raise HTTPException(
                    status_code=400,
                    detail={
                        "error": "invalid_token",
                        "message": "Invite link is invalid or expired."
                    }
                )
            
            # Check if token expired
            now = datetime.now()
            if expires_at and expires_at < now:
                raise HTTPException(
                    status_code=400,
                    detail={
                        "error": "invalid_token",
                        "message": "Invite link is invalid or expired."
                    }
                )
            
            # 2. Load user and verify they exist
            cur.execute("""
                SELECT id::text, email, is_active
                FROM users
                WHERE id = %s::uuid
            """, (user_id,))
            
            user_row = cur.fetchone()
            
            if not user_row:
                raise HTTPException(
                    status_code=400,
                    detail={
                        "error": "user_not_found",
                        "message": "Associated user account not found."
                    }
                )
            
            user_id_confirmed, email, is_active = user_row
            
            if not is_active:
                raise HTTPException(
                    status_code=400,
                    detail={
                        "error": "account_inactive",
                        "message": "This account has been deactivated."
                    }
                )
            
            # 3. Hash password and update user
            password_hash = hash_password(password)
            
            cur.execute("""
                UPDATE users
                SET password_hash = %s, email_verified = TRUE
                WHERE id = %s::uuid
            """, (password_hash, user_id))
            
            # 4. Mark token as used
            cur.execute("""
                UPDATE signup_tokens
                SET used_at = NOW()
                WHERE token = %s
            """, (token,))
            
            conn.commit()
            
            # 5. Generate auth session (JWT)
            access_token = sign_jwt(
                {
                    "sub": user_id,
                    "user_id": user_id,
                    "account_id": account_id,
                    "scopes": ["reports:read", "reports:write"]
                },
                settings.JWT_SECRET,
                ttl_seconds=7 * 24 * 3600  # 7 days for new users
            )
            
            # 6. Set HTTP-only cookie (same pattern as login)
            response.set_cookie(
                key="mr_token",
                value=access_token,
                httponly=True,
                secure=True,
                samesite="lax",
                max_age=7 * 24 * 60 * 60  # 7 days
            )
            
            # 7. Return response
            return {
                "ok": True,
                "access_token": access_token,
                "token_type": "bearer",
                "user": {
                    "id": user_id,
                    "email": email,
                    "primary_account_id": account_id
                }
            }











