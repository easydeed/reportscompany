"""
User Onboarding Routes

Provides endpoints for:
- GET /v1/onboarding - Get current onboarding status
- POST /v1/onboarding/complete-step - Mark a step as complete
- POST /v1/onboarding/skip-step - Skip a step
- POST /v1/onboarding/dismiss - Dismiss onboarding entirely
"""

from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from ..db import db_conn

router = APIRouter(prefix="/v1")


# ============ Constants ============

# Define onboarding steps in order
ONBOARDING_STEPS = [
    {
        "key": "profile_complete",
        "title": "Complete your profile",
        "description": "Add your name, company, and contact info",
        "href": "/app/account/settings",
        "icon": "user",
        "required": True,
    },
    {
        "key": "branding_setup",
        "title": "Set up your branding",
        "description": "Upload logo and customize colors",
        "href": "/app/branding",
        "icon": "palette",
        "required": False,
    },
    {
        "key": "first_report",
        "title": "Generate your first report",
        "description": "Create a market snapshot report",
        "href": "/app/reports/new",
        "icon": "file-text",
        "required": True,
    },
    {
        "key": "first_schedule",
        "title": "Set up automated reports",
        "description": "Schedule recurring reports for clients",
        "href": "/app/schedules/new",
        "icon": "calendar",
        "required": False,
    },
]

AFFILIATE_ONBOARDING_STEPS = [
    {
        "key": "profile_complete",
        "title": "Complete your profile",
        "description": "Add your name, company, and contact info",
        "href": "/app/account/settings",
        "icon": "user",
        "required": True,
    },
    {
        "key": "branding_setup",
        "title": "Set up white-label branding",
        "description": "Configure your brand for sponsored agents",
        "href": "/app/branding",
        "icon": "palette",
        "required": True,
    },
    {
        "key": "first_agent_invited",
        "title": "Invite your first agent",
        "description": "Sponsor an agent to use your branding",
        "href": "/app/affiliate",
        "icon": "user-plus",
        "required": True,
    },
]


# ============ Models ============

class OnboardingStep(BaseModel):
    key: str
    title: str
    description: str
    href: str
    icon: str
    required: bool
    completed: bool = False
    skipped: bool = False
    completed_at: Optional[datetime] = None


class OnboardingStatus(BaseModel):
    user_id: str
    is_complete: bool
    is_dismissed: bool
    current_step: Optional[str]
    progress_percent: int
    steps: List[OnboardingStep]
    completed_count: int
    total_count: int


class CompleteStepRequest(BaseModel):
    step_key: str
    metadata: Optional[Dict[str, Any]] = None


class SkipStepRequest(BaseModel):
    step_key: str


# ============ Helper Functions ============

def get_steps_for_user(account_type: str) -> List[dict]:
    """Return appropriate onboarding steps based on account type."""
    if account_type == "INDUSTRY_AFFILIATE":
        return AFFILIATE_ONBOARDING_STEPS
    return ONBOARDING_STEPS


def check_auto_completions(cur, user_id: str, account_id: str, account_type: str) -> List[str]:
    """
    Check for automatically completable steps based on user activity.
    Returns list of step keys that should be auto-completed.
    """
    auto_completed = []

    # Check profile completion
    cur.execute("""
        SELECT first_name, last_name, company_name
        FROM users WHERE id = %s::uuid
    """, (user_id,))
    user = cur.fetchone()
    if user and user[0] and user[1]:  # Has first and last name
        auto_completed.append("profile_complete")

    # Check branding setup
    cur.execute("""
        SELECT logo_url, primary_color
        FROM accounts WHERE id = %s::uuid
    """, (account_id,))
    account = cur.fetchone()
    if account and account[0]:  # Has logo
        auto_completed.append("branding_setup")

    # Check first report
    cur.execute("""
        SELECT COUNT(*) FROM report_generations
        WHERE account_id = %s::uuid AND status = 'completed'
    """, (account_id,))
    report_count = cur.fetchone()[0]
    if report_count > 0:
        auto_completed.append("first_report")

    # Check first schedule
    cur.execute("""
        SELECT COUNT(*) FROM schedules
        WHERE account_id = %s::uuid AND active = TRUE
    """, (account_id,))
    schedule_count = cur.fetchone()[0]
    if schedule_count > 0:
        auto_completed.append("first_schedule")

    # For affiliates, check if they've invited an agent
    if account_type == "INDUSTRY_AFFILIATE":
        cur.execute("""
            SELECT COUNT(*) FROM accounts
            WHERE sponsor_account_id = %s::uuid
        """, (account_id,))
        sponsored_count = cur.fetchone()[0]
        if sponsored_count > 0:
            auto_completed.append("first_agent_invited")

    return auto_completed


# ============ Endpoints ============

@router.get("/onboarding", response_model=OnboardingStatus)
def get_onboarding_status(request: Request):
    """
    Get current user's onboarding status.

    Automatically detects completed steps based on user activity.
    """
    user_info = getattr(request.state, "user", None)
    account_id = getattr(request.state, "account_id", None)

    if not user_info or not user_info.get("id"):
        raise HTTPException(status_code=401, detail="Unauthorized")

    user_id = user_info["id"]

    with db_conn() as (conn, cur):
        # Get user's onboarding state and account type
        cur.execute("""
            SELECT u.onboarding_completed_at, u.onboarding_step, u.onboarding_data,
                   a.account_type
            FROM users u
            JOIN accounts a ON a.id = %s::uuid
            WHERE u.id = %s::uuid
        """, (account_id, user_id))

        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="User not found")

        onboarding_completed_at, current_step, onboarding_data, account_type = row
        onboarding_data = onboarding_data or {}

        is_dismissed = onboarding_data.get("dismissed", False)

        # Get steps for this user type
        step_definitions = get_steps_for_user(account_type)

        # Get existing progress records
        cur.execute("""
            SELECT step_key, completed_at, skipped_at
            FROM onboarding_progress
            WHERE user_id = %s::uuid
        """, (user_id,))

        progress_records = {row[0]: {"completed_at": row[1], "skipped_at": row[2]}
                          for row in cur.fetchall()}

        # Check for auto-completions
        auto_completed = check_auto_completions(cur, user_id, account_id, account_type)

        # Auto-complete steps that are detected
        for step_key in auto_completed:
            if step_key not in progress_records or not progress_records[step_key].get("completed_at"):
                cur.execute("""
                    INSERT INTO onboarding_progress (user_id, step_key, completed_at)
                    VALUES (%s::uuid, %s, NOW())
                    ON CONFLICT (user_id, step_key)
                    DO UPDATE SET completed_at = NOW(), updated_at = NOW()
                    WHERE onboarding_progress.completed_at IS NULL
                """, (user_id, step_key))
                progress_records[step_key] = {"completed_at": datetime.now(), "skipped_at": None}

        conn.commit()

        # Build step list with completion status
        steps = []
        completed_count = 0
        first_incomplete = None

        for step_def in step_definitions:
            progress = progress_records.get(step_def["key"], {})
            is_completed = progress.get("completed_at") is not None
            is_skipped = progress.get("skipped_at") is not None

            if is_completed:
                completed_count += 1
            elif first_incomplete is None and not is_skipped:
                first_incomplete = step_def["key"]

            steps.append(OnboardingStep(
                key=step_def["key"],
                title=step_def["title"],
                description=step_def["description"],
                href=step_def["href"],
                icon=step_def["icon"],
                required=step_def["required"],
                completed=is_completed,
                skipped=is_skipped,
                completed_at=progress.get("completed_at"),
            ))

        total_count = len(steps)
        progress_percent = int((completed_count / total_count) * 100) if total_count > 0 else 0
        is_complete = completed_count == total_count or onboarding_completed_at is not None

        return OnboardingStatus(
            user_id=user_id,
            is_complete=is_complete,
            is_dismissed=is_dismissed,
            current_step=first_incomplete,
            progress_percent=progress_percent,
            steps=steps,
            completed_count=completed_count,
            total_count=total_count,
        )


@router.post("/onboarding/complete-step")
def complete_onboarding_step(body: CompleteStepRequest, request: Request):
    """
    Mark an onboarding step as complete.
    """
    user_info = getattr(request.state, "user", None)

    if not user_info or not user_info.get("id"):
        raise HTTPException(status_code=401, detail="Unauthorized")

    user_id = user_info["id"]

    # Validate step key
    all_steps = [s["key"] for s in ONBOARDING_STEPS + AFFILIATE_ONBOARDING_STEPS]
    if body.step_key not in all_steps:
        raise HTTPException(status_code=400, detail=f"Invalid step key: {body.step_key}")

    with db_conn() as (conn, cur):
        cur.execute("""
            INSERT INTO onboarding_progress (user_id, step_key, completed_at, metadata)
            VALUES (%s::uuid, %s, NOW(), %s)
            ON CONFLICT (user_id, step_key)
            DO UPDATE SET
                completed_at = NOW(),
                skipped_at = NULL,
                metadata = COALESCE(onboarding_progress.metadata, '{}') || %s,
                updated_at = NOW()
        """, (user_id, body.step_key, body.metadata or {}, body.metadata or {}))

        # Update user's current step
        cur.execute("""
            UPDATE users SET onboarding_step = %s, updated_at = NOW()
            WHERE id = %s::uuid
        """, (body.step_key, user_id))

        conn.commit()

    return {"ok": True, "step_key": body.step_key, "completed": True}


@router.post("/onboarding/skip-step")
def skip_onboarding_step(body: SkipStepRequest, request: Request):
    """
    Skip an onboarding step (for optional steps).
    """
    user_info = getattr(request.state, "user", None)

    if not user_info or not user_info.get("id"):
        raise HTTPException(status_code=401, detail="Unauthorized")

    user_id = user_info["id"]

    # Validate step key
    all_steps = {s["key"]: s for s in ONBOARDING_STEPS + AFFILIATE_ONBOARDING_STEPS}
    if body.step_key not in all_steps:
        raise HTTPException(status_code=400, detail=f"Invalid step key: {body.step_key}")

    # Check if step is required
    if all_steps[body.step_key]["required"]:
        raise HTTPException(status_code=400, detail="Cannot skip required step")

    with db_conn() as (conn, cur):
        cur.execute("""
            INSERT INTO onboarding_progress (user_id, step_key, skipped_at)
            VALUES (%s::uuid, %s, NOW())
            ON CONFLICT (user_id, step_key)
            DO UPDATE SET
                skipped_at = NOW(),
                updated_at = NOW()
            WHERE onboarding_progress.completed_at IS NULL
        """, (user_id, body.step_key))

        conn.commit()

    return {"ok": True, "step_key": body.step_key, "skipped": True}


@router.post("/onboarding/dismiss")
def dismiss_onboarding(request: Request):
    """
    Dismiss the onboarding checklist (hide it from UI).
    User can still access onboarding via settings.
    """
    user_info = getattr(request.state, "user", None)

    if not user_info or not user_info.get("id"):
        raise HTTPException(status_code=401, detail="Unauthorized")

    user_id = user_info["id"]

    with db_conn() as (conn, cur):
        cur.execute("""
            UPDATE users
            SET
                onboarding_data = COALESCE(onboarding_data, '{}') || '{"dismissed": true}',
                updated_at = NOW()
            WHERE id = %s::uuid
        """, (user_id,))

        conn.commit()

    return {"ok": True, "dismissed": True}


@router.post("/onboarding/reset")
def reset_onboarding(request: Request):
    """
    Reset onboarding progress (for testing or re-onboarding).
    """
    user_info = getattr(request.state, "user", None)

    if not user_info or not user_info.get("id"):
        raise HTTPException(status_code=401, detail="Unauthorized")

    user_id = user_info["id"]

    with db_conn() as (conn, cur):
        # Delete progress records
        cur.execute("""
            DELETE FROM onboarding_progress WHERE user_id = %s::uuid
        """, (user_id,))

        # Reset user onboarding state
        cur.execute("""
            UPDATE users
            SET
                onboarding_completed_at = NULL,
                onboarding_step = 'welcome',
                onboarding_data = '{}',
                updated_at = NOW()
            WHERE id = %s::uuid
        """, (user_id,))

        conn.commit()

    return {"ok": True, "reset": True}
