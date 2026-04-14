"""
Company Admin API Routes (Tier 2 — Title Company)

Provides dashboard, rep management, agent visibility, branding cascade,
and metrics for Title Company administrators.
"""

from fastapi import APIRouter, HTTPException, Request, Depends, BackgroundTasks
from pydantic import BaseModel, EmailStr
from typing import Optional
import secrets
import logging

from ..db import db_conn, fetchall_dicts, fetchone_dict
from ..deps.company import get_company_admin
from ..services.email import send_invite_email

logger = logging.getLogger(__name__)

router = APIRouter()


# ── Request / Response models ────────────────────────────────────────────────

class InviteRepRequest(BaseModel):
    name: str
    email: EmailStr
    first_name: str
    last_name: str
    phone: Optional[str] = None
    title: Optional[str] = None
    office_location: Optional[str] = None


class ResendRepInviteRequest(BaseModel):
    email: EmailStr


class UpdateBrandingRequest(BaseModel):
    brand_display_name: Optional[str] = None
    logo_url: Optional[str] = None
    email_logo_url: Optional[str] = None
    footer_logo_url: Optional[str] = None
    email_footer_logo_url: Optional[str] = None
    primary_color: Optional[str] = None
    accent_color: Optional[str] = None
    rep_photo_url: Optional[str] = None
    contact_line1: Optional[str] = None
    contact_line2: Optional[str] = None
    website_url: Optional[str] = None


# ── Helpers ──────────────────────────────────────────────────────────────────

def _get_company_rep_ids(cur, company_id: str) -> list[str]:
    """Return account IDs of all INDUSTRY_AFFILIATE reps under this company."""
    cur.execute("""
        SELECT id::text FROM accounts
        WHERE parent_account_id = %s::uuid
          AND account_type = 'INDUSTRY_AFFILIATE'
    """, (company_id,))
    return [r[0] for r in cur.fetchall()]


# ── 1. GET /overview ─────────────────────────────────────────────────────────

@router.get("/overview")
def get_overview(company: dict = Depends(get_company_admin)):
    company_id = company["company_account_id"]

    with db_conn() as (conn, cur):
        # ── Company info + plan limit ──
        cur.execute("""
            SELECT a.name,
                   a.plan_slug,
                   COALESCE(a.monthly_report_limit_override,
                            p.monthly_report_limit, 5000) AS report_limit
            FROM accounts a
            LEFT JOIN plans p ON p.plan_slug = a.plan_slug
            WHERE a.id = %s::uuid
        """, (company_id,))
        info_row = cur.fetchone()
        company_name = info_row[0] if info_row else "Unknown"
        plan_slug = info_row[1] if info_row else "affiliate"
        report_limit = info_row[2] if info_row else 5000

        # ── Rep list with agent counts, monthly reports, user info for status ──
        cur.execute("""
            SELECT
                a.id::text            AS rep_id,
                a.name                AS rep_name,
                u.email,
                u.is_active,
                u.email_verified,
                u.password_hash IS NOT NULL AS has_password,
                a.created_at::text    AS created_at,
                (SELECT COUNT(*) FROM accounts sa
                 WHERE sa.sponsor_account_id = a.id)              AS agent_count,
                (SELECT COUNT(*) FROM report_generations rg
                 WHERE rg.account_id IN (
                     SELECT id FROM accounts WHERE sponsor_account_id = a.id
                 )
                 AND rg.generated_at >= date_trunc('month', NOW()))  AS reports_this_month,
                (SELECT MAX(rg2.generated_at)::text
                 FROM report_generations rg2
                 WHERE rg2.account_id IN (
                     SELECT id FROM accounts WHERE sponsor_account_id = a.id
                 ))                                                AS last_activity
            FROM accounts a
            LEFT JOIN account_users au ON au.account_id = a.id AND au.role = 'OWNER'
            LEFT JOIN users u ON u.id = au.user_id
            WHERE a.parent_account_id = %s::uuid
              AND a.account_type = 'INDUSTRY_AFFILIATE'
            ORDER BY a.name
        """, (company_id,))
        cols = [d.name for d in cur.description]
        raw_reps = [dict(zip(cols, row)) for row in cur.fetchall()]

        reps = []
        for r in raw_reps:
            if r.get("is_active") is False:
                status = "deactivated"
            elif r.get("email_verified") and r.get("has_password"):
                status = "active"
            else:
                status = "pending"
            reps.append({
                "id": r["rep_id"],
                "name": r["rep_name"],
                "email": r.get("email") or "",
                "office": "",
                "agent_count": r["agent_count"],
                "reports_this_month": r["reports_this_month"],
                "last_active": r["last_activity"],
                "status": status,
            })

        total_reps = len(reps)
        total_agents = sum(r["agent_count"] for r in reps)

        # ── Reports this month (all reps + their agents) ──
        cur.execute("""
            SELECT COUNT(*) FROM report_generations rg
            WHERE rg.generated_at >= date_trunc('month', NOW())
            AND rg.status IN ('completed', 'processing')
            AND (
                rg.account_id IN (
                    SELECT id FROM accounts WHERE parent_account_id = %s::uuid
                )
                OR rg.account_id IN (
                    SELECT sa.id FROM accounts sa
                    WHERE sa.sponsor_account_id IN (
                        SELECT id FROM accounts WHERE parent_account_id = %s::uuid
                    )
                )
            )
        """, (company_id, company_id))
        total_reports = cur.fetchone()[0]

        # ── Reps added this month ──
        cur.execute("""
            SELECT COUNT(*) FROM accounts
            WHERE parent_account_id = %s::uuid
              AND account_type = 'INDUSTRY_AFFILIATE'
              AND created_at >= date_trunc('month', NOW())
        """, (company_id,))
        reps_change = cur.fetchone()[0]

        # ── Agents added this month ──
        cur.execute("""
            SELECT COUNT(*) FROM accounts sa
            WHERE sa.sponsor_account_id IN (
                SELECT id FROM accounts WHERE parent_account_id = %s::uuid
            )
            AND sa.created_at >= date_trunc('month', NOW())
        """, (company_id,))
        agents_change = cur.fetchone()[0]

        # ── Active agents (30d) — at least 1 report ──
        cur.execute("""
            SELECT COUNT(DISTINCT rg.account_id) FROM report_generations rg
            WHERE rg.generated_at >= NOW() - INTERVAL '30 days'
              AND rg.status IN ('completed', 'processing')
              AND rg.account_id IN (
                  SELECT sa.id FROM accounts sa
                  WHERE sa.sponsor_account_id IN (
                      SELECT id FROM accounts WHERE parent_account_id = %s::uuid
                  )
              )
        """, (company_id,))
        active_agents_30d = cur.fetchone()[0]
        engagement_pct = round(active_agents_30d / total_agents * 100) if total_agents > 0 else 0

        # ── Reports change vs last month ──
        cur.execute("""
            SELECT COUNT(*) FROM report_generations rg
            WHERE rg.generated_at >= date_trunc('month', NOW() - INTERVAL '1 month')
              AND rg.generated_at < date_trunc('month', NOW())
              AND rg.status IN ('completed', 'processing')
              AND (
                  rg.account_id IN (
                      SELECT id FROM accounts WHERE parent_account_id = %s::uuid
                  )
                  OR rg.account_id IN (
                      SELECT sa.id FROM accounts sa
                      WHERE sa.sponsor_account_id IN (
                          SELECT id FROM accounts WHERE parent_account_id = %s::uuid
                      )
                  )
              )
        """, (company_id, company_id))
        last_month_reports = cur.fetchone()[0]
        reports_change_pct = round(((total_reports - last_month_reports) / max(last_month_reports, 1)) * 100)

        # ── Company initials ──
        initials = "".join(w[0].upper() for w in company_name.split()[:2]) if company_name else "CO"

        # ── Activity feed (recent reports across company) ──
        cur.execute("""
            SELECT
                u.first_name || ' ' || COALESCE(u.last_name, '') AS agent_name,
                rg.report_type,
                rg.city,
                rg.generated_at,
                rg.id::text AS rg_id
            FROM report_generations rg
            JOIN account_users au ON au.account_id = rg.account_id AND au.role = 'OWNER'
            JOIN users u ON u.id = au.user_id
            WHERE (
                rg.account_id IN (
                    SELECT id FROM accounts WHERE parent_account_id = %s::uuid
                )
                OR rg.account_id IN (
                    SELECT sa.id FROM accounts sa
                    WHERE sa.sponsor_account_id IN (
                        SELECT id FROM accounts WHERE parent_account_id = %s::uuid
                    )
                )
            )
            ORDER BY rg.generated_at DESC
            LIMIT 10
        """, (company_id, company_id))
        activity_rows = cur.fetchall()
        activity = []
        for row in activity_rows:
            name = (row[0] or "").strip()
            rtype = (row[1] or "report").replace("_", " ")
            city = row[2] or "unknown"
            activity.append({
                "id": row[4],
                "description": f"{name} generated {rtype} for {city}",
                "timestamp": row[3].isoformat() if row[3] else None,
            })

    return {
        "company": {
            "name": company_name,
            "plan": plan_slug.replace("_", " ").title() if plan_slug else "Affiliate",
            "usage": total_reports,
            "limit": report_limit,
            "initials": initials,
        },
        "metrics": {
            "total_reps": total_reps,
            "total_agents": total_agents,
            "reports_this_month": total_reports,
            "active_agents_30d": active_agents_30d,
            "total_agent_seats": total_agents,
            "reps_change": reps_change,
            "agents_change": agents_change,
            "reports_change_pct": reports_change_pct,
            "engagement_pct": engagement_pct,
        },
        "reps": reps,
        "activity": activity,
    }


# ── 2. GET /reps ─────────────────────────────────────────────────────────────

@router.get("/reps")
def list_reps(company: dict = Depends(get_company_admin)):
    company_id = company["company_account_id"]

    with db_conn() as (conn, cur):
        cur.execute("""
            SELECT
                a.id::text             AS rep_id,
                a.name                 AS rep_name,
                u.email,
                u.email_verified,
                u.password_hash IS NOT NULL AS has_password,
                u.is_active,
                a.created_at::text     AS created_at,
                (SELECT COUNT(*) FROM accounts sa
                 WHERE sa.sponsor_account_id = a.id)               AS agent_count,
                (SELECT COUNT(*) FROM report_generations rg
                 WHERE rg.account_id IN (
                     SELECT id FROM accounts WHERE sponsor_account_id = a.id
                 )
                 AND rg.generated_at >= date_trunc('month', NOW())) AS reports_this_month,
                (SELECT MAX(rg2.generated_at)::text
                 FROM report_generations rg2
                 WHERE rg2.account_id IN (
                     SELECT id FROM accounts WHERE sponsor_account_id = a.id
                 ))                                                 AS last_activity
            FROM accounts a
            JOIN account_users au ON au.account_id = a.id AND au.role = 'OWNER'
            JOIN users u ON u.id = au.user_id
            WHERE a.parent_account_id = %s::uuid
              AND a.account_type = 'INDUSTRY_AFFILIATE'
            ORDER BY a.name
        """, (company_id,))
        cols = [d.name for d in cur.description]
        rows = [dict(zip(cols, row)) for row in cur.fetchall()]

    reps = []
    for r in rows:
        if not r["is_active"]:
            status = "deactivated"
        elif r["email_verified"] and r["has_password"]:
            status = "active"
        else:
            status = "pending"

        reps.append({
            "rep_id": r["rep_id"],
            "rep_name": r["rep_name"],
            "email": r["email"],
            "status": status,
            "agent_count": r["agent_count"],
            "reports_this_month": r["reports_this_month"],
            "last_activity": r["last_activity"],
            "created_at": r["created_at"],
        })

    return {"reps": reps}


# ── 3. GET /agents ───────────────────────────────────────────────────────────

@router.get("/agents")
def list_agents(company: dict = Depends(get_company_admin)):
    company_id = company["company_account_id"]

    with db_conn() as (conn, cur):
        cur.execute("""
            SELECT
                agent_acct.id::text     AS agent_id,
                COALESCE(u.first_name || ' ' || u.last_name, u.email) AS agent_name,
                u.email,
                rep_acct.name           AS rep_name,
                u.is_active,
                u.email_verified,
                u.password_hash IS NOT NULL AS has_password,
                agent_acct.plan_slug,
                agent_acct.created_at::text AS created_at,
                (SELECT COUNT(*) FROM report_generations rg
                 WHERE rg.account_id = agent_acct.id
                   AND rg.generated_at >= date_trunc('month', NOW())) AS reports_this_month,
                (SELECT MAX(rg2.generated_at)::text
                 FROM report_generations rg2
                 WHERE rg2.account_id = agent_acct.id)               AS last_activity
            FROM accounts agent_acct
            JOIN accounts rep_acct ON rep_acct.id = agent_acct.sponsor_account_id
            JOIN account_users au  ON au.account_id = agent_acct.id AND au.role = 'OWNER'
            JOIN users u           ON u.id = au.user_id
            WHERE rep_acct.parent_account_id = %s::uuid
              AND rep_acct.account_type = 'INDUSTRY_AFFILIATE'
            ORDER BY rep_acct.name, u.email
        """, (company_id,))
        cols = [d.name for d in cur.description]
        rows = [dict(zip(cols, row)) for row in cur.fetchall()]

    agents = []
    for r in rows:
        if not r["is_active"]:
            status = "deactivated"
        elif r["email_verified"] and r["has_password"]:
            status = "active"
        else:
            status = "pending"

        agents.append({
            "agent_id": r["agent_id"],
            "agent_name": r["agent_name"],
            "email": r["email"],
            "rep_name": r["rep_name"],
            "status": status,
            "plan": r["plan_slug"],
            "reports_this_month": r["reports_this_month"],
            "last_activity": r["last_activity"],
            "created_at": r["created_at"],
        })

    return {"agents": agents}


# ── 4. POST /invite-rep ──────────────────────────────────────────────────────

@router.post("/invite-rep")
def invite_rep(
    body: InviteRepRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    company: dict = Depends(get_company_admin),
):
    company_id = company["company_account_id"]
    email = body.email.strip().lower()

    with db_conn() as (conn, cur):
        # Duplicate check
        cur.execute(
            "SELECT id FROM users WHERE LOWER(email) = %s", (email,)
        )
        if cur.fetchone():
            raise HTTPException(
                status_code=400,
                detail="A user with this email already exists.",
            )

        # Create INDUSTRY_AFFILIATE account under this company
        slug_base = body.name.lower().replace(" ", "-").replace(".", "").replace(",", "").replace("'", "")[:40]
        import time as _time
        slug = f"{slug_base}-{int(_time.time())}"[:50]

        cur.execute("""
            INSERT INTO accounts (name, slug, account_type, plan_slug, parent_account_id)
            VALUES (%s, %s, 'INDUSTRY_AFFILIATE', 'free', %s::uuid)
            RETURNING id::text
        """, (body.name.strip(), slug, company_id))
        rep_account_id = cur.fetchone()[0]

        # Create user
        cur.execute("""
            INSERT INTO users (
                account_id, email, is_active, email_verified, role,
                first_name, last_name, phone, job_title
            ) VALUES (
                %s::uuid, %s, TRUE, FALSE, 'member',
                %s, %s, %s, %s
            )
            RETURNING id::text
        """, (
            rep_account_id, email,
            body.first_name.strip(), body.last_name.strip(),
            body.phone, body.title,
        ))
        user_id = cur.fetchone()[0]

        # Link user → account as OWNER
        cur.execute("""
            INSERT INTO account_users (account_id, user_id, role)
            VALUES (%s::uuid, %s::uuid, 'OWNER')
        """, (rep_account_id, user_id))

        # Signup token
        token = secrets.token_urlsafe(32)
        cur.execute("""
            INSERT INTO signup_tokens (token, user_id, account_id, expires_at)
            VALUES (%s, %s::uuid, %s::uuid, NOW() + INTERVAL '7 days')
        """, (token, user_id, rep_account_id))

        # Cascade company branding to new rep (non-override copy)
        cur.execute("""
            INSERT INTO affiliate_branding (
                account_id, brand_display_name, logo_url, email_logo_url,
                footer_logo_url, email_footer_logo_url,
                primary_color, accent_color, rep_photo_url,
                contact_line1, contact_line2, website_url,
                branding_override
            )
            SELECT
                %s::uuid, brand_display_name, logo_url, email_logo_url,
                footer_logo_url, email_footer_logo_url,
                primary_color, accent_color, NULL,
                contact_line1, contact_line2, website_url,
                FALSE
            FROM affiliate_branding
            WHERE account_id = %s::uuid
        """, (rep_account_id, company_id))

        conn.commit()

    # Send invite email
    inviter_name, company_name = _get_inviter_info(company_id, request)
    try:
        background_tasks.add_task(
            send_invite_email, email, inviter_name, company_name, token,
            body.first_name.strip() if body.first_name else None,
        )
        logger.info(f"Rep invite email queued for {email}")
    except Exception as e:
        logger.error(f"Failed to queue rep invite for {email}: {e}")

    return {
        "ok": True,
        "rep_account_id": rep_account_id,
        "email_queued": True,
    }


# ── 5. POST /resend-rep-invite ───────────────────────────────────────────────

@router.post("/resend-rep-invite")
def resend_rep_invite(
    body: ResendRepInviteRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    company: dict = Depends(get_company_admin),
):
    company_id = company["company_account_id"]
    email = body.email.strip().lower()

    with db_conn() as (conn, cur):
        cur.execute("""
            SELECT u.id::text, u.email_verified,
                   u.password_hash IS NOT NULL AS has_password,
                   a.id::text AS rep_account_id
            FROM users u
            JOIN account_users au ON au.user_id = u.id AND au.role = 'OWNER'
            JOIN accounts a ON a.id = au.account_id
            WHERE LOWER(u.email) = %s
              AND a.parent_account_id = %s::uuid
              AND a.account_type = 'INDUSTRY_AFFILIATE'
        """, (email, company_id))
        row = cur.fetchone()

        if not row:
            raise HTTPException(
                status_code=404,
                detail="Rep not found or not under your company.",
            )

        user_id, email_verified, has_password, rep_account_id = row

        if email_verified and has_password:
            raise HTTPException(
                status_code=400,
                detail="This rep has already accepted their invitation.",
            )

        # Invalidate old tokens
        cur.execute("""
            UPDATE signup_tokens SET used = TRUE
            WHERE user_id = %s::uuid AND used = FALSE
        """, (user_id,))

        token = secrets.token_urlsafe(32)
        cur.execute("""
            INSERT INTO signup_tokens (token, user_id, account_id, expires_at)
            VALUES (%s, %s::uuid, %s::uuid, NOW() + INTERVAL '7 days')
        """, (token, user_id, rep_account_id))

        conn.commit()

    inviter_name, company_name = _get_inviter_info(company_id, request)
    try:
        background_tasks.add_task(
            send_invite_email, email, inviter_name, company_name, token
        )
        logger.info(f"Rep resend invite queued for {email}")
    except Exception as e:
        logger.error(f"Failed to queue rep resend invite for {email}: {e}")

    return {"ok": True, "email_queued": True}


# ── 6. GET /branding ─────────────────────────────────────────────────────────

@router.get("/branding")
def get_branding(company: dict = Depends(get_company_admin)):
    company_id = company["company_account_id"]

    with db_conn() as (conn, cur):
        cur.execute("""
            SELECT brand_display_name, logo_url, email_logo_url,
                   footer_logo_url, email_footer_logo_url,
                   primary_color, accent_color, rep_photo_url,
                   contact_line1, contact_line2, website_url
            FROM affiliate_branding
            WHERE account_id = %s::uuid
        """, (company_id,))
        row = cur.fetchone()

    if not row:
        return {"branding": None}

    return {
        "branding": {
            "brand_display_name": row[0],
            "logo_url": row[1],
            "email_logo_url": row[2],
            "footer_logo_url": row[3],
            "email_footer_logo_url": row[4],
            "primary_color": row[5],
            "accent_color": row[6],
            "rep_photo_url": row[7],
            "contact_line1": row[8],
            "contact_line2": row[9],
            "website_url": row[10],
        }
    }


# ── 7. PATCH /branding ──────────────────────────────────────────────────────

@router.patch("/branding")
def update_branding(
    body: UpdateBrandingRequest,
    company: dict = Depends(get_company_admin),
):
    company_id = company["company_account_id"]

    with db_conn() as (conn, cur):
        # Upsert company's own branding
        cur.execute("""
            INSERT INTO affiliate_branding (
                account_id, brand_display_name, logo_url, email_logo_url,
                footer_logo_url, email_footer_logo_url,
                primary_color, accent_color, rep_photo_url,
                contact_line1, contact_line2, website_url,
                branding_override, updated_at
            ) VALUES (
                %s::uuid, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, TRUE, NOW()
            )
            ON CONFLICT (account_id) DO UPDATE SET
                brand_display_name   = COALESCE(EXCLUDED.brand_display_name, affiliate_branding.brand_display_name),
                logo_url             = COALESCE(EXCLUDED.logo_url, affiliate_branding.logo_url),
                email_logo_url       = COALESCE(EXCLUDED.email_logo_url, affiliate_branding.email_logo_url),
                footer_logo_url      = COALESCE(EXCLUDED.footer_logo_url, affiliate_branding.footer_logo_url),
                email_footer_logo_url= COALESCE(EXCLUDED.email_footer_logo_url, affiliate_branding.email_footer_logo_url),
                primary_color        = COALESCE(EXCLUDED.primary_color, affiliate_branding.primary_color),
                accent_color         = COALESCE(EXCLUDED.accent_color, affiliate_branding.accent_color),
                rep_photo_url        = COALESCE(EXCLUDED.rep_photo_url, affiliate_branding.rep_photo_url),
                contact_line1        = COALESCE(EXCLUDED.contact_line1, affiliate_branding.contact_line1),
                contact_line2        = COALESCE(EXCLUDED.contact_line2, affiliate_branding.contact_line2),
                website_url          = COALESCE(EXCLUDED.website_url, affiliate_branding.website_url),
                branding_override    = TRUE,
                updated_at           = NOW()
            RETURNING
                brand_display_name, logo_url, email_logo_url,
                footer_logo_url, email_footer_logo_url,
                primary_color, accent_color, rep_photo_url,
                contact_line1, contact_line2, website_url
        """, (
            company_id,
            body.brand_display_name, body.logo_url, body.email_logo_url,
            body.footer_logo_url, body.email_footer_logo_url,
            body.primary_color, body.accent_color, body.rep_photo_url,
            body.contact_line1, body.contact_line2, body.website_url,
        ))
        saved = cur.fetchone()

        # Cascade logos, colors, display name, website to child reps
        # that haven't overridden. Rep photo + contact info stay untouched.
        if saved:
            cur.execute("""
                UPDATE affiliate_branding ab SET
                    brand_display_name    = %s,
                    logo_url              = %s,
                    email_logo_url        = %s,
                    footer_logo_url       = %s,
                    email_footer_logo_url = %s,
                    primary_color         = %s,
                    accent_color          = %s,
                    website_url           = %s,
                    updated_at            = NOW()
                FROM accounts a
                WHERE ab.account_id = a.id
                  AND a.parent_account_id = %s::uuid
                  AND a.account_type = 'INDUSTRY_AFFILIATE'
                  AND COALESCE(ab.branding_override, false) = false
            """, (
                saved[0], saved[1], saved[2], saved[3], saved[4],
                saved[5], saved[6], saved[10],
                company_id,
            ))
            reps_updated = cur.rowcount or 0
        else:
            reps_updated = 0

        conn.commit()

    return {
        "ok": True,
        "branding": {
            "brand_display_name": saved[0],
            "logo_url": saved[1],
            "email_logo_url": saved[2],
            "footer_logo_url": saved[3],
            "email_footer_logo_url": saved[4],
            "primary_color": saved[5],
            "accent_color": saved[6],
            "rep_photo_url": saved[7],
            "contact_line1": saved[8],
            "contact_line2": saved[9],
            "website_url": saved[10],
        },
        "reps_updated": reps_updated,
    }


# ── 8. GET /metrics ─────────────────────────────────────────────────────────

@router.get("/metrics")
def get_metrics(company: dict = Depends(get_company_admin)):
    company_id = company["company_account_id"]

    with db_conn() as (conn, cur):
        rep_ids = _get_company_rep_ids(cur, company_id)

        if not rep_ids:
            return {
                "total_reports_30d": 0,
                "report_trend": 0,
                "top_rep": None,
                "top_agent": None,
            }

        # All agent account IDs under company's reps
        cur.execute("""
            SELECT id::text FROM accounts
            WHERE sponsor_account_id = ANY(%s::uuid[])
        """, (rep_ids,))
        agent_ids = [r[0] for r in cur.fetchall()]
        all_ids = rep_ids + agent_ids

        # Total reports last 30 days
        cur.execute("""
            SELECT COUNT(*) FROM report_generations
            WHERE account_id = ANY(%s::uuid[])
              AND generated_at >= NOW() - INTERVAL '30 days'
        """, (all_ids,))
        total_30d = cur.fetchone()[0] or 0

        # Previous 30 days for trend
        cur.execute("""
            SELECT COUNT(*) FROM report_generations
            WHERE account_id = ANY(%s::uuid[])
              AND generated_at >= NOW() - INTERVAL '60 days'
              AND generated_at <  NOW() - INTERVAL '30 days'
        """, (all_ids,))
        prev_30d = cur.fetchone()[0] or 0

        trend = 0
        if prev_30d > 0:
            trend = round(((total_30d - prev_30d) / prev_30d) * 100, 1)

        # Top-performing rep (most agent reports this month)
        if rep_ids:
            cur.execute("""
                SELECT a.name,
                       COUNT(rg.id) AS cnt
                FROM accounts a
                LEFT JOIN accounts sa ON sa.sponsor_account_id = a.id
                LEFT JOIN report_generations rg
                    ON rg.account_id = sa.id
                   AND rg.generated_at >= date_trunc('month', NOW())
                WHERE a.id = ANY(%s::uuid[])
                GROUP BY a.id, a.name
                ORDER BY cnt DESC
                LIMIT 1
            """, (rep_ids,))
            top_rep_row = cur.fetchone()
            top_rep = {"name": top_rep_row[0], "reports": top_rep_row[1]} if top_rep_row else None
        else:
            top_rep = None

        # Top-performing agent
        if agent_ids:
            cur.execute("""
                SELECT COALESCE(u.first_name || ' ' || u.last_name, u.email) AS name,
                       COUNT(rg.id) AS cnt
                FROM accounts a
                JOIN account_users au ON au.account_id = a.id AND au.role = 'OWNER'
                JOIN users u ON u.id = au.user_id
                LEFT JOIN report_generations rg
                    ON rg.account_id = a.id
                   AND rg.generated_at >= date_trunc('month', NOW())
                WHERE a.id = ANY(%s::uuid[])
                GROUP BY u.id, u.first_name, u.last_name, u.email
                ORDER BY cnt DESC
                LIMIT 1
            """, (agent_ids,))
            top_agent_row = cur.fetchone()
            top_agent = {"name": top_agent_row[0], "reports": top_agent_row[1]} if top_agent_row else None
        else:
            top_agent = None

    return {
        "total_reports_30d": total_30d,
        "report_trend": trend,
        "top_rep": top_rep,
        "top_agent": top_agent,
    }


# ── Internal helpers ─────────────────────────────────────────────────────────

def _get_inviter_info(company_id: str, request: Request) -> tuple[str, str]:
    """Return (inviter_name, company_name) for invite emails."""
    with db_conn() as (conn, cur):
        cur.execute(
            "SELECT name FROM accounts WHERE id = %s::uuid", (company_id,)
        )
        row = cur.fetchone()
        company_name = row[0] if row else "Your Company"

    inviter_name = company_name
    user_info = getattr(request.state, "user", None)
    if user_info and user_info.get("id"):
        with db_conn() as (conn, cur):
            cur.execute("""
                SELECT COALESCE(
                    NULLIF(TRIM(first_name || ' ' || last_name), ''),
                    email
                ) FROM users WHERE id = %s::uuid
            """, (user_info["id"],))
            urow = cur.fetchone()
            if urow and urow[0]:
                inviter_name = urow[0]

    return inviter_name, company_name
