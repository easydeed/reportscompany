"""
Company Admin API Routes (Tier 2 — Title Company)

Provides dashboard, rep management, agent visibility, branding cascade,
and metrics for Title Company administrators.
"""

from fastapi import APIRouter, HTTPException, Request, Depends, BackgroundTasks
from pydantic import BaseModel, EmailStr, constr, field_validator
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID
import logging

from ..db import db_conn, set_rls, fetchall_dicts, fetchone_dict
from ..verification import block_unverified_send
from ..deps.company import get_company_admin, get_company_member
from ..services.email import send_rep_change_notice_email, send_role_invite_email
from ..services import seats
from ..services.usage import get_full_plan_usage
from ..services.invite_service import (
    copy_branding_to_child,
    create_invited_user,
    find_user_for_resend,
    get_inviter_context,
    regenerate_invite_token,
)

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


class ReassignSeatRequest(BaseModel):
    """The rep who takes the seat (invited here), and where the agents go.

    `agents_to_rep_id` empty: the agents move with the seat, to the new rep.
    Set: another rep of this company who holds a seat takes them instead.
    """
    name: str
    email: EmailStr
    first_name: str
    last_name: str = ""
    phone: Optional[str] = None
    title: Optional[str] = None
    agents_to_rep_id: Optional[UUID] = None


# Hex colour pattern, identical to routes/account.py:74. Written straight into
# affiliate_branding, read back by compute_color_roles(), which parses it as
# hex; an unvalidated value used to raise ValueError out of
# schedule_email_html() and stop every send on the account (D-060).
HEX_COLOR = r'^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$'


class UpdateBrandingRequest(BaseModel):
    brand_display_name: Optional[str] = None
    logo_url: Optional[str] = None
    email_logo_url: Optional[str] = None
    footer_logo_url: Optional[str] = None
    email_footer_logo_url: Optional[str] = None
    primary_color: Optional[constr(pattern=HEX_COLOR)] = None
    accent_color: Optional[constr(pattern=HEX_COLOR)] = None
    rep_photo_url: Optional[str] = None
    contact_line1: Optional[str] = None
    contact_line2: Optional[str] = None
    website_url: Optional[str] = None

    # An emptied colour field means "unset", not "invalid". The admin affiliate
    # form binds a free-text input to the same state as the colour picker
    # (apps/web/app/admin/(dashboard)/affiliates/page.tsx:191) and posts it
    # verbatim, so clearing it would otherwise 422 where it used to store "".
    @field_validator("primary_color", "accent_color", mode="before")
    @classmethod
    def _blank_color_is_unset(cls, v):
        return None if isinstance(v, str) and not v.strip() else v


# ── Helpers ──────────────────────────────────────────────────────────────────

def _utc_iso(ts: Optional[datetime]) -> Optional[str]:
    """`report_generations.generated_at` is `timestamp without time zone`,
    written by NOW() on a UTC database. Sent bare, a browser reads it as its
    own local time — seven or eight hours late in California, so a report
    made last night reads "Today". Say it is UTC."""
    if ts is None:
        return None
    return (ts.replace(tzinfo=timezone.utc) if ts.tzinfo is None else ts).isoformat()


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
def get_overview(company: dict = Depends(get_company_member)):
    company_id = company["company_account_id"]

    with db_conn() as (conn, cur):
        set_rls(cur, company_id)
        # ── Company info + per-product plan limits ──
        cur.execute("""
            SELECT a.name, a.plan_slug
            FROM accounts a
            WHERE a.id = %s::uuid
        """, (company_id,))
        info_row = cur.fetchone()
        company_name = info_row[0] if info_row else "Unknown"
        plan_slug = info_row[1] if info_row else "affiliate"

        full_plan = get_full_plan_usage(cur, company_id)
        plan_limits = full_plan["plan"]
        plan_name = plan_limits["plan_name"]

        # ── Rep list (LATERAL to avoid duplicate-owner rows) ──
        cur.execute("""
            SELECT
                a.id::text            AS rep_id,
                a.name                AS rep_name,
                u.email,
                u.is_active,
                u.email_verified,
                u.password_hash IS NOT NULL AS has_password,
                a.created_at          AS created_at,
                (SELECT COUNT(*) FROM accounts sa
                 WHERE sa.sponsor_account_id = a.id)                    AS agent_count,
                (SELECT COUNT(*) FROM report_generations rg
                 WHERE rg.account_id IN (
                     SELECT id FROM accounts WHERE sponsor_account_id = a.id
                 )
                 AND rg.generated_at >= date_trunc('month', NOW())
                 AND rg.status IN ('completed', 'processing'))          AS reports_this_month,
                (SELECT MAX(rg2.generated_at)
                 FROM report_generations rg2
                 WHERE rg2.account_id IN (
                     SELECT id FROM accounts WHERE sponsor_account_id = a.id
                 )
                 AND rg2.status IN ('completed', 'processing'))         AS last_activity
            FROM accounts a
            LEFT JOIN LATERAL (
                SELECT u2.id, u2.email, u2.is_active, u2.email_verified, u2.password_hash
                FROM account_users au
                JOIN users u2 ON u2.id = au.user_id
                WHERE au.account_id = a.id AND au.role = 'OWNER'
                LIMIT 1
            ) u ON true
            WHERE a.parent_account_id = %s::uuid
              AND a.account_type = 'INDUSTRY_AFFILIATE'
            ORDER BY a.name
        """, (company_id,))
        cols = [d.name for d in cur.description]
        raw_reps = [dict(zip(cols, row)) for row in cur.fetchall()]
        idle_reps = seats.idle_rep_ids(cur, company_id)
        seat_block = seats.seat_summary(cur, company_id)

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
                "last_active": r["last_activity"].isoformat() if r.get("last_activity") else None,
                "status": status,
                "idle": r["rep_id"] in idle_reps,
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

        # ── Active agents (30d) — at least 1 completed report ──
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

        # ── Agents at their market-report limit this month ──
        cur.execute("""
            SELECT COUNT(*) FROM (
                SELECT a.id
                FROM accounts a
                LEFT JOIN plans p ON p.plan_slug = a.plan_slug
                LEFT JOIN report_generations rg ON rg.account_id = a.id
                    AND rg.generated_at >= date_trunc('month', NOW())
                    AND rg.status IN ('completed', 'processing')
                WHERE a.sponsor_account_id IN (
                    SELECT id FROM accounts WHERE parent_account_id = %s::uuid
                )
                GROUP BY a.id, a.market_reports_limit_override, p.market_reports_limit
                HAVING COUNT(rg.id) >= COALESCE(a.market_reports_limit_override, p.market_reports_limit, 3)
            ) at_limit
        """, (company_id,))
        agents_at_limit = cur.fetchone()[0]

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

        # ── Homeowner leads brought in by the company's agents ──
        # A READ of rows the agents' own pages already wrote: `leads` is filled
        # by the property-report lead form (`leads.py`) and the home-value page
        # (`lead_pages.py`), both keyed by the agent's `account_id`. Nothing
        # here captures or creates a lead. Counts only — who the lead is stays
        # with the agent. Market reports never capture leads, so this is a
        # per-agent figure, not a per-report one.
        cur.execute("""
            SELECT
                COUNT(*) FILTER (WHERE l.created_at >= date_trunc('month', NOW())),
                COUNT(*) FILTER (WHERE l.created_at >= date_trunc('month', NOW() - INTERVAL '1 month')
                                   AND l.created_at <  date_trunc('month', NOW()))
            FROM leads l
            WHERE l.account_id IN (
                SELECT sa.id FROM accounts sa
                WHERE sa.sponsor_account_id IN (
                    SELECT id FROM accounts WHERE parent_account_id = %s::uuid
                )
            )
        """, (company_id,))
        leads_this_month, leads_last_month = cur.fetchone()

        # ── Company initials ──
        initials = "".join(w[0].upper() for w in company_name.split()[:2]) if company_name else "CO"

        # ── Activity feed (recent reports across company, LATERAL for owner) ──
        cur.execute("""
            SELECT
                u.first_name || ' ' || COALESCE(u.last_name, '') AS agent_name,
                rg.report_type,
                COALESCE(rg.input_params->>'city', rg.cities[1], 'unknown') AS city,
                rg.generated_at,
                rg.id::text AS rg_id
            FROM report_generations rg
            LEFT JOIN LATERAL (
                SELECT u2.first_name, u2.last_name
                FROM account_users au
                JOIN users u2 ON u2.id = au.user_id
                WHERE au.account_id = rg.account_id AND au.role = 'OWNER'
                LIMIT 1
            ) u ON true
            WHERE rg.status IN ('completed', 'processing')
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
                "timestamp": _utc_iso(row[3]),
            })

    return {
        "company": {
            "name": company_name,
            "plan": plan_name,
            "usage": {
                "market_reports": {
                    "used": total_reports,
                    "limit": plan_limits["market_reports_limit"],
                },
                "schedules": {
                    "used": full_plan["usage"]["schedules_active"],
                    "limit": plan_limits["schedules_limit"],
                },
                "property_reports": {
                    "used": full_plan["usage"]["property_reports_used"],
                    "limit": plan_limits["property_reports_limit"],
                },
            },
            "initials": initials,
        },
        "metrics": {
            "total_reps": total_reps,
            "total_agents": total_agents,
            "reports_this_month": total_reports,
            "active_agents_30d": active_agents_30d,
            "reps_change": reps_change,
            "agents_change": agents_change,
            "reports_change_pct": reports_change_pct,
            "engagement_pct": engagement_pct,
            "agents_at_limit": agents_at_limit,
            # The count `reports_change_pct` divides by. Sent so the page can
            # say "none last month" instead of "up 3600%" when it was zero.
            "reports_last_month": last_month_reports,
            "leads_this_month": leads_this_month,
            "leads_last_month": leads_last_month,
        },
        # `{total, held, open, pending, idle}`, or null when the company is
        # not on seats. Replaces `total_agent_seats`, which was the agent count
        # under a seat name: agents take no seat.
        "seats": seat_block,
        "reps": reps,
        "activity": activity,
        # D-280: whether the person looking can use the admin actions. Every
        # user on the account sees the same numbers; only the admin acts.
        "can_manage": company["is_company_admin"],
    }


# ── 2. GET /reps ─────────────────────────────────────────────────────────────

@router.get("/reps")
def list_reps(company: dict = Depends(get_company_member)):
    company_id = company["company_account_id"]

    with db_conn() as (conn, cur):
        set_rls(cur, company_id)
        cur.execute("""
            SELECT
                a.id::text             AS rep_id,
                a.name                 AS rep_name,
                u.email,
                u.email_verified,
                u.password_hash IS NOT NULL AS has_password,
                u.is_active,
                a.created_at           AS created_at,
                (SELECT COUNT(*) FROM accounts sa
                 WHERE sa.sponsor_account_id = a.id)                    AS agent_count,
                (SELECT COUNT(*) FROM report_generations rg
                 WHERE rg.account_id IN (
                     SELECT id FROM accounts WHERE sponsor_account_id = a.id
                 )
                 AND rg.generated_at >= date_trunc('month', NOW())
                 AND rg.status IN ('completed', 'processing'))          AS reports_this_month,
                (SELECT COUNT(*) FROM report_generations rg3
                 WHERE rg3.account_id IN (
                     SELECT id FROM accounts WHERE sponsor_account_id = a.id
                 )
                 AND rg3.status IN ('completed', 'processing'))         AS total_reports,
                (SELECT MAX(rg2.generated_at)
                 FROM report_generations rg2
                 WHERE rg2.account_id IN (
                     SELECT id FROM accounts WHERE sponsor_account_id = a.id
                 )
                 AND rg2.status IN ('completed', 'processing'))         AS last_activity,
                EXISTS (
                    SELECT 1 FROM rep_seat_assignments s
                     WHERE s.rep_account_id = a.id
                       AND s.company_account_id = a.parent_account_id
                       AND s.ended_at IS NULL)                          AS holds_seat
            FROM accounts a
            LEFT JOIN LATERAL (
                SELECT u2.id, u2.email, u2.is_active, u2.email_verified, u2.password_hash
                FROM account_users au
                JOIN users u2 ON u2.id = au.user_id
                WHERE au.account_id = a.id AND au.role = 'OWNER'
                LIMIT 1
            ) u ON true
            WHERE a.parent_account_id = %s::uuid
              AND a.account_type = 'INDUSTRY_AFFILIATE'
            ORDER BY a.name
        """, (company_id,))
        cols = [d.name for d in cur.description]
        rows = [dict(zip(cols, row)) for row in cur.fetchall()]
        idle_reps = seats.idle_rep_ids(cur, company_id)

    reps = []
    for r in rows:
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
            "status": status,
            "office": "",
            "agent_count": r["agent_count"],
            "reports_this_month": r["reports_this_month"],
            "total_reports": r["total_reports"],
            "last_active": r["last_activity"].isoformat() if r.get("last_activity") else None,
            "joined_date": r["created_at"].isoformat() if r.get("created_at") else None,
            # A joined rep holding a seat whose agents finished no market or
            # property report in 30 days (`seats.idle_rep_ids`).
            "idle": r["rep_id"] in idle_reps,
            # An open seat row. The seat actions — reassign, and for a rep who
            # has not joined, cancel the invite — act on it; a rep without
            # one (switched off, or reassigned away) has neither.
            "holds_seat": bool(r["holds_seat"]),
        })

    return {"reps": reps, "can_manage": company["is_company_admin"]}


# ── 3. GET /agents ───────────────────────────────────────────────────────────

@router.get("/agents")
def list_agents(company: dict = Depends(get_company_member)):
    company_id = company["company_account_id"]

    with db_conn() as (conn, cur):
        set_rls(cur, company_id)
        cur.execute("""
            SELECT
                agent_acct.id::text     AS agent_id,
                COALESCE(u.first_name || ' ' || u.last_name, u.email) AS agent_name,
                u.email,
                rep_acct.id::text       AS rep_id,
                rep_acct.name           AS rep_name,
                u.is_active,
                u.email_verified,
                u.password_hash IS NOT NULL AS has_password,
                agent_acct.plan_slug,
                agent_acct.created_at::text AS created_at,
                (SELECT COUNT(*) FROM report_generations rg
                 WHERE rg.account_id = agent_acct.id
                   AND rg.generated_at >= date_trunc('month', NOW())
                   AND rg.status IN ('completed', 'processing'))     AS reports_this_month,
                (SELECT MAX(rg2.generated_at)::text
                 FROM report_generations rg2
                 WHERE rg2.account_id = agent_acct.id
                   AND rg2.status IN ('completed', 'processing'))    AS last_activity
            FROM accounts agent_acct
            JOIN accounts rep_acct ON rep_acct.id = agent_acct.sponsor_account_id
            LEFT JOIN LATERAL (
                SELECT u2.id, u2.first_name, u2.last_name, u2.email,
                       u2.is_active, u2.email_verified, u2.password_hash
                FROM account_users au
                JOIN users u2 ON u2.id = au.user_id
                WHERE au.account_id = agent_acct.id AND au.role = 'OWNER'
                LIMIT 1
            ) u ON true
            WHERE rep_acct.parent_account_id = %s::uuid
              AND rep_acct.account_type = 'INDUSTRY_AFFILIATE'
            ORDER BY rep_acct.name, u.email
        """, (company_id,))
        cols = [d.name for d in cur.description]
        rows = [dict(zip(cols, row)) for row in cur.fetchall()]

    agents = []
    for r in rows:
        if r.get("is_active") is False:
            status = "deactivated"
        elif r.get("email_verified") and r.get("has_password"):
            status = "active"
        else:
            status = "pending"

        agents.append({
            "agent_id": r["agent_id"],
            "agent_name": r.get("agent_name") or r.get("email") or "",
            "email": r.get("email") or "",
            # D-276: keyed by id as well as name. Two reps can share a name;
            # the People page and the ?rep= filter join on this.
            "rep_id": r["rep_id"],
            "rep_name": r["rep_name"],
            "status": status,
            "plan": r["plan_slug"],
            "reports_this_month": r["reports_this_month"],
            "last_activity": r["last_activity"],
            "created_at": r["created_at"],
        })

    return {"agents": agents}


# ── 4b. GET /reports and GET /schedules — cross-org visibility ───────────────

@router.get("/reports")
def get_company_reports(
    rep_id: str = None,
    limit: int = 50,
    offset: int = 0,
    company: dict = Depends(get_company_member),
):
    """All reports across reps and agents under this company."""
    company_id = company["company_account_id"]

    with db_conn() as (conn, cur):
        set_rls(cur, company_id)
        cur.execute("""
            SELECT id FROM accounts
            WHERE parent_account_id = %s::uuid AND account_type = 'INDUSTRY_AFFILIATE'
        """, (company_id,))
        rep_ids = [row[0] for row in cur.fetchall()]

        if not rep_ids:
            return {"reports": [], "total": 0}

        # A caller-supplied rep_id must belong to THIS company. Without this
        # check the sponsored-agent lookup below accepts any rep id and leaks
        # another company's agents' reports. Compare as text: rep_ids holds
        # UUID objects, rep_id is a query-string str.
        if rep_id:
            matched_rep = next((r for r in rep_ids if str(r) == rep_id), None)
            if matched_rep is None:
                raise HTTPException(
                    status_code=404,
                    detail="Rep not found or not under your company.",
                )
            # Keep the row's own value (UUID), not the raw string — the id lists
            # are combined and passed to ANY(%s), which rejects mixed types.
            scoped_rep_ids = [matched_rep]
            cur.execute("""
                SELECT id FROM accounts WHERE sponsor_account_id = %s::uuid
            """, (rep_id,))
        else:
            scoped_rep_ids = rep_ids
            cur.execute("""
                SELECT id FROM accounts WHERE sponsor_account_id = ANY(%s)
            """, (rep_ids,))
        agent_ids = [row[0] for row in cur.fetchall()]

        # Scope to the requested rep only — previously every rep of the company
        # was appended regardless of the filter, so the filter never narrowed.
        all_ids = agent_ids + scoped_rep_ids
        if not all_ids:
            return {"reports": [], "total": 0}

        cur.execute("""
            SELECT COUNT(*) FROM report_generations WHERE account_id = ANY(%s)
        """, (all_ids,))
        total = cur.fetchone()[0]

        cur.execute("""
            SELECT rg.id::text, rg.report_type, rg.status, rg.generated_at,
                   COALESCE(rg.input_params->>'city', rg.cities[1], 'Unknown') AS city,
                   rg.pdf_url, a.name AS account_name,
                   CASE WHEN a.account_type = 'INDUSTRY_AFFILIATE' THEN 'Rep'
                        ELSE 'Agent' END AS user_type,
                   u.first_name || ' ' || COALESCE(u.last_name, '') AS user_name,
                   a.id::text, COALESCE(sp.id, a.id)::text, COALESCE(sp.name, a.name)
            FROM report_generations rg
            JOIN accounts a ON a.id = rg.account_id
            -- An agent's rep is their sponsor; a rep is their own.
            LEFT JOIN accounts sp ON sp.id = a.sponsor_account_id
            LEFT JOIN account_users au ON au.account_id = a.id AND au.role = 'OWNER'
            LEFT JOIN users u ON u.id = au.user_id
            WHERE rg.account_id = ANY(%s)
            ORDER BY rg.generated_at DESC
            LIMIT %s OFFSET %s
        """, (all_ids, limit, offset))
        reports = [
            {
                "id": r[0], "report_type": r[1], "status": r[2],
                "generated_at": _utc_iso(r[3]),
                "city": r[4], "pdf_url": r[5],
                "account_name": r[6], "user_type": r[7],
                "user_name": (r[8] or "").strip(),
                "account_id": r[9], "rep_id": r[10], "rep_name": r[11],
            }
            for r in cur.fetchall()
        ]

    return {"reports": reports, "total": total}


@router.get("/schedules")
def get_company_schedules(
    rep_id: str = None,
    company: dict = Depends(get_company_member),
):
    """All schedules across reps and agents under this company."""
    company_id = company["company_account_id"]

    with db_conn() as (conn, cur):
        set_rls(cur, company_id)
        cur.execute("""
            SELECT id FROM accounts
            WHERE parent_account_id = %s::uuid AND account_type = 'INDUSTRY_AFFILIATE'
        """, (company_id,))
        rep_ids = [row[0] for row in cur.fetchall()]

        if not rep_ids:
            return {"schedules": [], "total": 0}

        # A caller-supplied rep_id must belong to THIS company. Without this
        # check the sponsored-agent lookup below accepts any rep id and leaks
        # another company's agents' schedules. Compare as text: rep_ids holds
        # UUID objects, rep_id is a query-string str.
        if rep_id:
            matched_rep = next((r for r in rep_ids if str(r) == rep_id), None)
            if matched_rep is None:
                raise HTTPException(
                    status_code=404,
                    detail="Rep not found or not under your company.",
                )
            # Keep the row's own value (UUID), not the raw string — the id lists
            # are combined and passed to ANY(%s), which rejects mixed types.
            scoped_rep_ids = [matched_rep]
            cur.execute("""
                SELECT id FROM accounts WHERE sponsor_account_id = %s::uuid
            """, (rep_id,))
        else:
            scoped_rep_ids = rep_ids
            cur.execute("""
                SELECT id FROM accounts WHERE sponsor_account_id = ANY(%s)
            """, (rep_ids,))
        agent_ids = [row[0] for row in cur.fetchall()]

        # Scope to the requested rep only — previously every rep of the company
        # was appended regardless of the filter, so the filter never narrowed.
        all_ids = agent_ids + scoped_rep_ids
        if not all_ids:
            return {"schedules": [], "total": 0}

        cur.execute("""
            SELECT s.id::text, s.name, s.report_type,
                   COALESCE(s.city, 'Unknown') AS area,
                   s.cadence, s.active, s.last_run_at, s.next_run_at,
                   a.name AS account_name,
                   CASE WHEN a.account_type = 'INDUSTRY_AFFILIATE' THEN 'Rep'
                        ELSE 'Agent' END AS user_type,
                   u.first_name || ' ' || COALESCE(u.last_name, '') AS user_name,
                   s.send_hour, s.send_minute, s.timezone,
                   (SELECT COUNT(*) FROM schedule_runs sr WHERE sr.schedule_id = s.id) AS total_runs,
                   a.id::text, COALESCE(sp.id, a.id)::text, COALESCE(sp.name, a.name),
                   s.weekly_dow, s.monthly_dom
            FROM schedules s
            JOIN accounts a ON a.id = s.account_id
            LEFT JOIN accounts sp ON sp.id = a.sponsor_account_id
            LEFT JOIN account_users au ON au.account_id = a.id AND au.role = 'OWNER'
            LEFT JOIN users u ON u.id = au.user_id
            WHERE s.account_id = ANY(%s)
            ORDER BY s.created_at DESC
        """, (all_ids,))
        schedules = [
            {
                "id": r[0], "name": r[1], "report_type": r[2],
                "area": r[3], "cadence": r[4], "active": r[5],
                "last_run_at": r[6].isoformat() if r[6] else None,
                "next_run_at": r[7].isoformat() if r[7] else None,
                "account_name": r[8], "user_type": r[9],
                "user_name": (r[10] or "").strip(),
                "send_hour": r[11], "send_minute": r[12], "timezone": r[13],
                "total_runs": r[14],
                "account_id": r[15], "rep_id": r[16], "rep_name": r[17],
                "weekly_dow": r[18], "monthly_dom": r[19],
            }
            for r in cur.fetchall()
        ]

    return {"schedules": schedules, "total": len(schedules)}


# ── 4. POST /invite-rep ──────────────────────────────────────────────────────

def _company_inviter_user_id(request: Request) -> Optional[str]:
    u = getattr(request.state, "user", None) or {}
    return u.get("id")


@router.post("/invite-rep")
def invite_rep(
    body: InviteRepRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    company: dict = Depends(get_company_admin),
):
    company_id = company["company_account_id"]
    try:
        with db_conn() as (conn, cur):
            set_rls(cur, company_id)
            # D-019. An invite is an email to a stranger, sent in this
            # company's name.
            block_unverified_send(
                cur, company_id,
                action="invite a rep",
                to_emails=[body.email] if body.email else None,
            )
            # A pending invite holds a seat. Locks the company row first, so a
            # second invite for the last seat waits and then sees this one.
            seats.reserve_seat(cur, company_id)
            result = create_invited_user(
                cur,
                role="title_rep",
                email=body.email,
                first_name=body.first_name.strip(),
                last_name=(body.last_name or "").strip(),
                phone=body.phone,
                job_title=body.title,
                account_name=body.name.strip(),
                parent_account_id=company_id,
            )
            copy_branding_to_child(
                cur, source_account_id=company_id, target_account_id=result["account_id"]
            )
            seats.open_seat(cur, company_id, result["account_id"])
            ctx = get_inviter_context(
                cur, account_id=company_id, inviter_user_id=_company_inviter_user_id(request)
            )
            conn.commit()

        rep_account_id = result["account_id"]
        background_tasks.add_task(
            send_role_invite_email,
            result["email"],
            ctx["inviter_name"],
            ctx["company_name"],
            result["token"],
            invitee_first_name=body.first_name.strip(),
            role="title_rep",
        )
        logger.info(f"Rep invite email queued for {result['email']}")
        return {
            "ok": True,
            "rep_account_id": rep_account_id,
            "email_queued": True,
        }
    except seats.SeatsFull as e:
        raise HTTPException(status_code=409, detail={"error": "seats_full", "message": str(e)})
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to invite rep: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"error": "invite_failed", "message": f"Failed to create rep invitation: {str(e)}"},
        )


# ── 5. POST /resend-rep-invite ───────────────────────────────────────────────

@router.post("/resend-rep-invite")
def resend_rep_invite(
    body: ResendRepInviteRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    company: dict = Depends(get_company_admin),
):
    company_id = company["company_account_id"]
    try:
        with db_conn() as (conn, cur):
            set_rls(cur, company_id)
            # D-019. Same as invite-rep: this puts mail in someone's inbox.
            block_unverified_send(
                cur, company_id,
                action="resend a rep invite",
                to_emails=[body.email] if body.email else None,
            )
            user = find_user_for_resend(
                cur,
                email=body.email,
                parent_account_id=company_id,
                account_type="INDUSTRY_AFFILIATE",
            )
            if not user:
                raise HTTPException(
                    status_code=404,
                    detail="Rep not found or not under your company.",
                )
            if user["already_accepted"]:
                raise HTTPException(
                    status_code=400,
                    detail="This rep has already accepted their invitation.",
                )
            token = regenerate_invite_token(
                cur, user_id=user["user_id"], account_id=user["account_id"]
            )
            ctx = get_inviter_context(
                cur, account_id=company_id, inviter_user_id=_company_inviter_user_id(request)
            )
            conn.commit()

        background_tasks.add_task(
            send_role_invite_email,
            user["email"],
            ctx["inviter_name"],
            ctx["company_name"],
            token,
            invitee_first_name=(user.get("first_name") or "").strip(),
            role="title_rep",
        )
        logger.info(f"Rep resend invite queued for {user['email']}")
        return {"ok": True, "email_queued": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to resend rep invite: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"error": "resend_failed", "message": str(e)},
        )


# ── 5b. Seats ────────────────────────────────────────────────────────────────
#
# Seats are REP seats (services/seats.py has the model and the compliance
# line). Every handler passes the caller's company id into the service, which
# puts it in the predicate of every rep it touches: a rep id from another
# company is a 404, never a read or a write.

@router.get("/seats")
def get_seats(company: dict = Depends(get_company_member)):
    """The seat count, who holds what, every past reassignment, and the
    plan the company's agents are on."""
    company_id = company["company_account_id"]
    with db_conn() as (conn, cur):
        set_rls(cur, company_id)
        return {
            "seats": seats.seat_summary(cur, company_id),
            "history": seats.seat_history(cur, company_id),
            # What an agent gets, for Plan & Seats: agents take no seat.
            "agent_plan": seats.agent_plan(cur),
            "can_manage": company["is_company_admin"],
        }


@router.post("/reps/{rep_id}/reassign")
def reassign_rep_seat(
    rep_id: UUID,
    body: ReassignSeatRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    company: dict = Depends(get_company_admin),
):
    """Move a rep's seat to a new rep, and their agents with it.

    One transaction: the new rep is invited into the seat, the agents move to
    them (or to `agents_to_rep_id`), the leaving rep's scheduled sends go
    where the agents go, the leaving rep is switched off, and the move is
    recorded. Each moved agent is told who their rep is now.
    """
    company_id = company["company_account_id"]
    actor = _company_inviter_user_id(request)
    rep_id = str(rep_id)
    agents_to = str(body.agents_to_rep_id) if body.agents_to_rep_id else None
    try:
        with db_conn() as (conn, cur):
            set_rls(cur, company_id)
            # D-019: this sends an invite and one notice per agent, all in the
            # company's name.
            block_unverified_send(
                cur, company_id,
                action="reassign a rep seat",
                to_emails=[body.email] + seats.agent_emails_for(cur, company_id, rep_id),
            )
            created = {}

            def create_successor(cur):
                result = create_invited_user(
                    cur,
                    role="title_rep",
                    email=body.email,
                    first_name=body.first_name.strip(),
                    last_name=(body.last_name or "").strip(),
                    phone=body.phone,
                    job_title=body.title,
                    account_name=body.name.strip(),
                    parent_account_id=company_id,
                )
                copy_branding_to_child(
                    cur, source_account_id=company_id, target_account_id=result["account_id"]
                )
                created.update(result)
                return result["account_id"]

            outcome = seats.reassign_seat(
                cur,
                company_id=company_id,
                from_rep_id=rep_id,
                create_successor=create_successor,
                agents_to_rep_id=agents_to,
                actor_user_id=actor,
            )
            ctx = get_inviter_context(cur, account_id=company_id, inviter_user_id=actor)
            # The name and address the agents are told about: the new rep's,
            # or the existing rep's when the company sent the agents there.
            if outcome["agents_to_rep_id"] == outcome["successor_rep_id"]:
                rep_name, rep_email = body.name.strip(), created["email"]
            else:
                cur.execute(
                    """
                    SELECT a.name, u.email FROM accounts a
                      JOIN account_users au ON au.account_id = a.id AND au.role = 'OWNER'
                      JOIN users u ON u.id = au.user_id
                     WHERE a.id = %s::uuid AND a.parent_account_id = %s::uuid
                     LIMIT 1
                    """,
                    (outcome["agents_to_rep_id"], company_id),
                )
                rep_name, rep_email = cur.fetchone()
            conn.commit()
    except seats.SeatNotFound:
        raise HTTPException(status_code=404, detail="Rep not found under your company, or holds no seat.")
    except seats.SeatConflict as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ValueError as e:          # the new rep's email is already registered
        raise HTTPException(status_code=409, detail=str(e))

    background_tasks.add_task(
        send_role_invite_email,
        created["email"], ctx["inviter_name"], ctx["company_name"], created["token"],
        invitee_first_name=body.first_name.strip(), role="title_rep",
    )
    for r in outcome["notice_recipients"]:
        background_tasks.add_task(
            send_rep_change_notice_email,
            r["email"],
            first_name=r["first_name"],
            company_name=ctx["company_name"],
            new_rep_name=rep_name,
            new_rep_email=rep_email,
        )
    return {
        "ok": True,
        "new_rep_account_id": outcome["successor_rep_id"],
        "agents_to_rep_id": outcome["agents_to_rep_id"],
        "agents_moved": len(outcome["agents_moved"]),
        "schedules_moved": outcome["schedules_moved"],
        "notices_queued": len(outcome["notice_recipients"]),
    }


@router.post("/reps/{rep_id}/cancel-invite")
def cancel_rep_invite(
    rep_id: UUID,
    request: Request,
    company: dict = Depends(get_company_admin),
):
    """Withdraw a rep invite that has not been accepted, freeing its seat."""
    company_id = company["company_account_id"]
    try:
        with db_conn() as (conn, cur):
            set_rls(cur, company_id)
            seats.cancel_rep_invite(
                cur, company_id=company_id, rep_id=str(rep_id),
                actor_user_id=_company_inviter_user_id(request),
            )
            conn.commit()
    except seats.SeatNotFound:
        raise HTTPException(status_code=404, detail="Rep not found under your company, or holds no seat.")
    except seats.SeatConflict as e:
        raise HTTPException(status_code=409, detail=str(e))
    return {"ok": True}


# ── 6. GET /branding ─────────────────────────────────────────────────────────

@router.get("/branding")
def get_branding(company: dict = Depends(get_company_member)):
    company_id = company["company_account_id"]

    with db_conn() as (conn, cur):
        set_rls(cur, company_id)
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
        return {"branding": None, "can_manage": company["is_company_admin"]}

    return {
        "can_manage": company["is_company_admin"],
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


# ── 6b. GET /settings ───────────────────────────────────────────────────────

#: account_users.role as the company's Settings page says it (D-280).
_ROLE_LABEL = {"OWNER": "admin"}


@router.get("/settings")
def get_settings(company: dict = Depends(get_company_member)):
    """The company's details and everyone on the account, for Settings.

    Read-only for everyone on the account. `postal_address` is shown, never
    set here (B5 is gated: the slot exists, the value comes from elsewhere).
    Adding or removing people has no endpoint yet, so none is offered.
    """
    company_id = company["company_account_id"]
    with db_conn() as (conn, cur):
        set_rls(cur, company_id)
        cur.execute(
            """
            SELECT a.name, ab.website_url, ab.postal_address
              FROM accounts a
              LEFT JOIN affiliate_branding ab ON ab.account_id = a.id
             WHERE a.id = %s::uuid
            """,
            (company_id,),
        )
        name, website, postal = cur.fetchone() or (None, None, None)
        cur.execute(
            """
            SELECT u.id::text, TRIM(COALESCE(u.first_name, '') || ' ' || COALESCE(u.last_name, '')),
                   u.email, au.role
              FROM account_users au
              JOIN users u ON u.id = au.user_id
             WHERE au.account_id = %s::uuid
             ORDER BY (au.role = 'OWNER') DESC, u.email
            """,
            (company_id,),
        )
        people = [
            {"id": r[0], "name": r[1] or "", "email": r[2],
             "role": _ROLE_LABEL.get(r[3], "viewer")}
            for r in cur.fetchall()
        ]
    return {
        "company": {"name": name, "website_url": website, "postal_address": postal},
        "people": people,
        "you": company.get("id"),
        "can_manage": company["is_company_admin"],
    }


# ── 7. PATCH /branding ──────────────────────────────────────────────────────

@router.patch("/branding")
def update_branding(
    body: UpdateBrandingRequest,
    company: dict = Depends(get_company_admin),
):
    company_id = company["company_account_id"]

    with db_conn() as (conn, cur):
        set_rls(cur, company_id)
        # Upsert company's own branding. The FIRST save creates the row, and
        # `brand_display_name` is NOT NULL: a form saved with the name left
        # empty inserted NULL and 500ed, so a new company could not save a
        # colour. Unnamed, the brand is the company's own account name — the
        # same fallback `copy_branding_to_child` gives its reps.
        cur.execute("""
            INSERT INTO affiliate_branding (
                account_id, brand_display_name, logo_url, email_logo_url,
                footer_logo_url, email_footer_logo_url,
                primary_color, accent_color, rep_photo_url,
                contact_line1, contact_line2, website_url,
                branding_override, updated_at
            ) VALUES (
                %s::uuid,
                COALESCE(%s, (SELECT name FROM accounts WHERE id = %s::uuid)),
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, TRUE, NOW()
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
            body.brand_display_name, company_id, body.logo_url, body.email_logo_url,
            body.footer_logo_url, body.email_footer_logo_url,
            body.primary_color, body.accent_color, body.rep_photo_url,
            body.contact_line1, body.contact_line2, body.website_url,
        ))
        saved = cur.fetchone()

        reps_updated = 0
        if saved:
            cascade_vals = (
                saved[0], saved[1], saved[2], saved[3], saved[4],
                saved[5], saved[6], saved[10], company_id,
            )

            # Cascade to child reps that haven't overridden
            try:
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
                """, cascade_vals)
            except Exception as e:
                logger.warning(f"Cascade with branding_override failed, cascading to all: {e}")
                conn.rollback()
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
                """, cascade_vals)
            reps_updated = cur.rowcount or 0

            # Insert branding for reps that don't have a row yet
            try:
                cur.execute("""
                    INSERT INTO affiliate_branding (
                        account_id, brand_display_name, logo_url, email_logo_url,
                        footer_logo_url, email_footer_logo_url,
                        primary_color, accent_color, website_url, branding_override
                    )
                    SELECT a.id, %s, %s, %s, %s, %s, %s, %s, %s, false
                    FROM accounts a
                    WHERE a.parent_account_id = %s::uuid
                      AND a.account_type = 'INDUSTRY_AFFILIATE'
                      AND NOT EXISTS (SELECT 1 FROM affiliate_branding ab WHERE ab.account_id = a.id)
                """, cascade_vals)
            except Exception:
                cur.execute("""
                    INSERT INTO affiliate_branding (
                        account_id, brand_display_name, logo_url, email_logo_url,
                        footer_logo_url, email_footer_logo_url,
                        primary_color, accent_color, website_url
                    )
                    SELECT a.id, %s, %s, %s, %s, %s, %s, %s, %s
                    FROM accounts a
                    WHERE a.parent_account_id = %s::uuid
                      AND a.account_type = 'INDUSTRY_AFFILIATE'
                      AND NOT EXISTS (SELECT 1 FROM affiliate_branding ab WHERE ab.account_id = a.id)
                """, cascade_vals)
            reps_updated += cur.rowcount or 0

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


# ── 7b. POST /branding/test-email ────────────────────────────────────────────

class CompanyTestEmailRequest(BaseModel):
    report_type: str = "market_snapshot"


@router.post("/branding/test-email")
async def send_company_test_email(
    body: CompanyTestEmailRequest,
    company: dict = Depends(get_company_admin),
):
    """A sample report email in the company's brand, to the signed-in admin.

    To the caller's own address and nobody else's — there is no recipient in
    the request. The same rules as a real send: the brand as the reps' emails
    resolve it, the footer's postal line (the company's, else the platform's),
    and a working unsubscribe link and one-click header signed for this
    company and this address, with the `email_log` row the unsubscribe route
    looks for.
    """
    from .branding_tools import SENDGRID_API_KEY, build_test_email, get_branding_for_account, sendgrid_send
    from .unsubscribe import generate_unsubscribe_token
    from ..settings import settings
    from urllib.parse import quote

    if not SENDGRID_API_KEY:
        raise HTTPException(status_code=503, detail="Email service not configured. Please contact support.")
    company_id = company["company_account_id"]
    with db_conn() as (conn, cur):
        set_rls(cur, company_id)
        cur.execute("SELECT email FROM users WHERE id = %s::uuid", (company.get("id"),))
        row = cur.fetchone()
        if not row or not row[0]:
            raise HTTPException(status_code=401, detail="Not authenticated")
        to = row[0]
        block_unverified_send(cur, company_id, action="send a test email", to_emails=[to])
        branding = get_branding_for_account(cur, company_id)
        # The colours as stored, not as `resolve_brand` fills them: the
        # worker's real email brand (`_resolve_email_brand`) leaves an unset
        # colour unset and the template supplies its default, so the sample
        # must too or it shows a colour no real email carries.
        cur.execute("SELECT primary_color, accent_color, postal_address FROM affiliate_branding "
                    "WHERE account_id = %s::uuid", (company_id,))
        primary, accent, postal = cur.fetchone() or (None, None, None)
        branding = {**branding, "primary_color": primary, "accent_color": accent}

        token = generate_unsubscribe_token(company_id, to)
        q = f"token={token}&email={quote(to, safe='')}"
        base = settings.APP_BASE.rstrip("/")
        subject, html = build_test_email(
            branding, body.report_type,
            unsubscribe_url=f"{base}/api/v1/email/unsubscribe?{q}", postal_address=postal)
        # Logged BEFORE the send, as the worker does: the unsubscribe route
        # finds the account to verify the token against in email_log.
        cur.execute(
            """INSERT INTO email_log (account_id, provider, to_emails, subject, status)
               VALUES (%s::uuid, 'sendgrid', %s, %s, 'queued') RETURNING id""",
            (company_id, [to], subject))
        log_id = cur.fetchone()[0]
        conn.commit()

    status_code = await sendgrid_send(
        to=to, subject=subject, html=html,
        from_name=branding.get("brand_display_name") or "TrendyReports",
        headers={"List-Unsubscribe": f"<{base}/api/v1/email/unsubscribe/one-click?{q}>",
                 "List-Unsubscribe-Post": "List-Unsubscribe=One-Click"})
    with db_conn() as (conn, cur):
        set_rls(cur, company_id)
        cur.execute("UPDATE email_log SET response_code = %s, status = %s WHERE id = %s",
                    (status_code, "sent" if status_code == 202 else "failed", log_id))
        conn.commit()
    if status_code != 202:
        raise HTTPException(status_code=502, detail="The test email didn't send. Please try again.")
    return {"ok": True, "sent_to": to}


# ── 8. GET /metrics ─────────────────────────────────────────────────────────

@router.get("/metrics")
def get_metrics(company: dict = Depends(get_company_member)):
    company_id = company["company_account_id"]

    with db_conn() as (conn, cur):
        set_rls(cur, company_id)
        rep_ids = _get_company_rep_ids(cur, company_id)

        if not rep_ids:
            return {
                "total_reports_30d": 0,
                "report_trend": 0,
                "top_rep": None,
                "top_agent": None,
            }

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
              AND status IN ('completed', 'processing')
        """, (all_ids,))
        total_30d = cur.fetchone()[0] or 0

        # Previous 30 days for trend
        cur.execute("""
            SELECT COUNT(*) FROM report_generations
            WHERE account_id = ANY(%s::uuid[])
              AND generated_at >= NOW() - INTERVAL '60 days'
              AND generated_at <  NOW() - INTERVAL '30 days'
              AND status IN ('completed', 'processing')
        """, (all_ids,))
        prev_30d = cur.fetchone()[0] or 0

        trend = 0
        if prev_30d > 0:
            trend = round(((total_30d - prev_30d) / prev_30d) * 100, 1)

        # Top-performing rep
        if rep_ids:
            cur.execute("""
                SELECT a.name,
                       COUNT(rg.id) AS cnt
                FROM accounts a
                LEFT JOIN accounts sa ON sa.sponsor_account_id = a.id
                LEFT JOIN report_generations rg
                    ON rg.account_id = sa.id
                   AND rg.generated_at >= date_trunc('month', NOW())
                   AND rg.status IN ('completed', 'processing')
                WHERE a.id = ANY(%s::uuid[])
                GROUP BY a.id, a.name
                ORDER BY cnt DESC
                LIMIT 1
            """, (rep_ids,))
            top_rep_row = cur.fetchone()
            top_rep = {"name": top_rep_row[0], "reports": top_rep_row[1]} if top_rep_row else None
        else:
            top_rep = None

        # Top-performing agent (LATERAL for owner)
        if agent_ids:
            cur.execute("""
                SELECT COALESCE(u.first_name || ' ' || u.last_name, u.email) AS name,
                       COUNT(rg.id) AS cnt
                FROM accounts a
                LEFT JOIN LATERAL (
                    SELECT u2.id, u2.first_name, u2.last_name, u2.email
                    FROM account_users au
                    JOIN users u2 ON u2.id = au.user_id
                    WHERE au.account_id = a.id AND au.role = 'OWNER'
                    LIMIT 1
                ) u ON true
                LEFT JOIN report_generations rg
                    ON rg.account_id = a.id
                   AND rg.generated_at >= date_trunc('month', NOW())
                   AND rg.status IN ('completed', 'processing')
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


