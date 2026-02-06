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
    # Query 1: All sponsored accounts with report stats
    cur.execute("""
        SELECT
            a.id::text AS account_id,
            a.name,
            a.plan_slug,
            a.account_type,
            a.created_at,
            COALESCE(u.report_count, 0) AS reports_this_month,
            u.last_report_at
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
        ) u ON u.account_id = a.id
        WHERE a.sponsor_account_id = %s::uuid
        ORDER BY u.report_count DESC NULLS LAST, a.created_at DESC
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
            "groups": groups_by_account.get(row[0], []),
        }
        for row in rows
    ]


def get_affiliate_overview(cur, affiliate_account_id: str) -> Dict[str, Any]:
    """
    Lightweight aggregate metrics. Does NOT call get_sponsored_accounts().
    Single query, O(1) regardless of account count.
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
    return {
        "sponsored_count": row[0] if row else 0,
        "total_reports_this_month": row[1] if row else 0,
    }


def verify_affiliate_account(cur, account_id: str) -> bool:
    """Check if account is an industry affiliate."""
    cur.execute(
        "SELECT account_type FROM accounts WHERE id = %s::uuid",
        (account_id,),
    )
    row = cur.fetchone()
    return row[0] == "INDUSTRY_AFFILIATE" if row else False
