"""
Affiliate Services — Rewritten for performance.

BEFORE: get_sponsored_accounts ran 1 + N queries (N = sponsored account count).
        get_affiliate_overview called get_sponsored_accounts just to count/sum.
        Route called both = everything ran twice.
AFTER:  get_sponsored_accounts runs exactly 2 queries (main + batch groups).
        get_affiliate_overview runs 1 lightweight aggregate query.
        Route calls each once.
"""

from typing import Dict, Any, List


def get_sponsored_accounts(cur, affiliate_account_id: str) -> List[Dict[str, Any]]:
    """
    Get all sponsored accounts with usage metrics and group memberships.
    Uses exactly 2 queries regardless of account count (was 1 + N).
    """
    # Query 1: All sponsored accounts with report stats and invite status
    cur.execute("""
        SELECT
            a.id::text AS account_id,
            a.name,
            a.plan_slug,
            a.account_type,
            a.created_at,
            COALESCE(rg.report_count, 0) AS reports_this_month,
            rg.last_report_at,
            CASE
                WHEN usr.email_verified = false OR usr.password_hash IS NULL THEN 'pending'
                WHEN usr.is_active = false THEN 'deactivated'
                ELSE 'active'
            END AS status,
            usr.email,
            (SELECT MAX(st.created_at) FROM signup_tokens st WHERE st.user_id = usr.id) AS last_invite_sent
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
        ) rg ON rg.account_id = a.id
        LEFT JOIN account_users au ON au.account_id = a.id AND au.role = 'OWNER'
        LEFT JOIN users usr ON usr.id = au.user_id
        WHERE a.sponsor_account_id = %s::uuid
        ORDER BY rg.report_count DESC NULLS LAST, a.created_at DESC
    """, (affiliate_account_id,))

    rows = cur.fetchall()
    if not rows:
        return []

    account_ids = [row[0] for row in rows]

    # Query 2: ALL group memberships in ONE batch (was: 1 query per account)
    cur.execute("""
        SELECT
            cgm.member_id::text AS account_id,
            cg.id::text AS group_id,
            cg.name AS group_name
        FROM contact_group_members cgm
        JOIN contact_groups cg ON cgm.group_id = cg.id
        WHERE cgm.member_type = 'sponsored_agent'
          AND cgm.member_id = ANY(%s::uuid[])
          AND cgm.account_id = %s::uuid
    """, (account_ids, affiliate_account_id))

    groups_by_account: Dict[str, list] = {}
    for group_row in cur.fetchall():
        aid = group_row[0]
        if aid not in groups_by_account:
            groups_by_account[aid] = []
        groups_by_account[aid].append({
            "id": group_row[1],
            "name": group_row[2],
        })

    return [
        {
            "account_id": row[0],
            "name": row[1],
            "plan_slug": row[2],
            "account_type": row[3],
            "created_at": row[4].isoformat() if row[4] else None,
            "reports_this_month": row[5],
            "last_report_at": row[6].isoformat() if row[6] else None,
            "status": row[7] or "pending",
            "email": row[8],
            "last_invite_sent": row[9].isoformat() if row[9] else None,
            "groups": groups_by_account.get(row[0], []),
        }
        for row in rows
    ]


def get_affiliate_overview(cur, affiliate_account_id: str) -> Dict[str, Any]:
    """
    Aggregate metrics for the affiliate dashboard and sidebar.
    Returns agent counts, report totals, active-agent ratio, and at-limit count.
    """
    cur.execute("""
        SELECT
            COUNT(*) AS sponsored_count,
            COALESCE(SUM(u.report_count), 0) AS total_reports_this_month
        FROM accounts a
        LEFT JOIN (
            SELECT account_id, COUNT(*) AS report_count
            FROM report_generations
            WHERE generated_at >= DATE_TRUNC('month', NOW())
              AND status IN ('completed', 'processing')
            GROUP BY account_id
        ) u ON u.account_id = a.id
        WHERE a.sponsor_account_id = %s::uuid
    """, (affiliate_account_id,))
    row = cur.fetchone()
    total_agents = row[0] if row else 0
    total_agent_reports = row[1] if row else 0

    # Active agents (at least 1 report in last 30 days)
    cur.execute("""
        SELECT COUNT(DISTINCT rg.account_id) FROM report_generations rg
        WHERE rg.account_id IN (
            SELECT id FROM accounts WHERE sponsor_account_id = %s::uuid
        )
        AND rg.generated_at >= NOW() - INTERVAL '30 days'
        AND rg.status IN ('completed', 'processing')
    """, (affiliate_account_id,))
    active_agents = cur.fetchone()[0]

    # Agents at their market-report limit this month
    cur.execute("""
        SELECT COUNT(*) FROM (
            SELECT a.id
            FROM accounts a
            LEFT JOIN plans p ON p.plan_slug = a.plan_slug
            LEFT JOIN report_generations rg ON rg.account_id = a.id
                AND rg.generated_at >= date_trunc('month', NOW())
                AND rg.status IN ('completed', 'processing')
            WHERE a.sponsor_account_id = %s::uuid
            GROUP BY a.id, a.market_reports_limit_override, p.market_reports_limit
            HAVING COUNT(rg.id) >= COALESCE(a.market_reports_limit_override, p.market_reports_limit, 3)
        ) at_limit
    """, (affiliate_account_id,))
    agents_at_limit = cur.fetchone()[0]

    return {
        "sponsored_count": total_agents,
        "total_reports_this_month": total_agent_reports,
        "metrics": {
            "total_agents": total_agents,
            "total_agent_reports": total_agent_reports,
            "active_agents": active_agents,
            "active_agents_total": total_agents,
            "agents_at_limit": agents_at_limit,
        },
    }


def verify_affiliate_account(cur, account_id: str) -> bool:
    """Check if account is an industry affiliate."""
    cur.execute(
        "SELECT account_type FROM accounts WHERE id = %s::uuid",
        (account_id,),
    )
    row = cur.fetchone()
    return row[0] == "INDUSTRY_AFFILIATE" if row else False
