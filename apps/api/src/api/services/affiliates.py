"""
Affiliate Services

Phase 29C: Industry affiliate account management
"""

from typing import Dict, Any, List


def get_sponsored_accounts(cur, affiliate_account_id: str) -> List[Dict[str, Any]]:
    """
    Get all accounts sponsored by this affiliate.
    
    Args:
        cur: Database cursor
        affiliate_account_id: Affiliate account UUID
    
    Returns:
        List of sponsored accounts with usage metrics
    """
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
    
    accounts = []
    for row in cur.fetchall():
        accounts.append({
            "account_id": row[0],
            "name": row[1],
            "plan_slug": row[2],
            "account_type": row[3],
            "created_at": row[4].isoformat() if row[4] else None,
            "reports_this_month": row[5],
            "last_report_at": row[6].isoformat() if row[6] else None,
        })
    
    return accounts


def get_affiliate_overview(cur, affiliate_account_id: str) -> Dict[str, Any]:
    """
    Get overview metrics for an affiliate account.
    
    Args:
        cur: Database cursor
        affiliate_account_id: Affiliate account UUID
    
    Returns:
        Overview metrics dictionary
    """
    sponsored = get_sponsored_accounts(cur, affiliate_account_id)
    
    total_reports = sum(acc["reports_this_month"] for acc in sponsored)
    
    return {
        "sponsored_count": len(sponsored),
        "total_reports_this_month": total_reports,
    }


def verify_affiliate_account(cur, account_id: str) -> bool:
    """
    Verify that an account is an industry affiliate.
    
    Args:
        cur: Database cursor
        account_id: Account UUID to check
    
    Returns:
        True if account_type is INDUSTRY_AFFILIATE
    """
    cur.execute("""
        SELECT account_type
        FROM accounts
        WHERE id = %s::uuid
    """, (account_id,))
    
    row = cur.fetchone()
    if not row:
        return False
    
    return row[0] == 'INDUSTRY_AFFILIATE'

