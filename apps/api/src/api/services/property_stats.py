"""
Property Report Statistics Service

Provides stats at three levels:
1. Agent Level: Individual account stats
2. Affiliate Level: Roll-up of all sponsored agents
3. Admin Level: Platform-wide statistics
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from ..db import db_conn, set_rls, fetchone_dict, fetchall_dicts


def get_agent_stats(account_id: str, from_date: Optional[datetime] = None, to_date: Optional[datetime] = None) -> Dict[str, Any]:
    """
    Get property report statistics for a single agent/account.
    
    Returns:
        - Total reports, completion rate, failure rate
        - Theme distribution
        - Lead metrics and conversion rate
        - Top performing reports
        - Recent activity
    """
    if not to_date:
        to_date = datetime.utcnow()
    if not from_date:
        from_date = to_date - timedelta(days=30)
    
    with db_conn() as (conn, cur):
        set_rls(cur, account_id)
        
        # Get cached stats (fast)
        cur.execute("""
            SELECT * FROM property_report_stats WHERE account_id = %s
        """, (account_id,))
        cached_stats = fetchone_dict(cur)
        
        # Get period-specific stats
        cur.execute("""
            SELECT
                COUNT(*) AS total_reports,
                COUNT(*) FILTER (WHERE status = 'complete') AS completed,
                COUNT(*) FILTER (WHERE status = 'failed') AS failed,
                COUNT(*) FILTER (WHERE status = 'processing') AS processing,
                COUNT(*) FILTER (WHERE report_type = 'seller') AS seller_reports,
                COUNT(*) FILTER (WHERE report_type = 'buyer') AS buyer_reports,
                COUNT(*) FILTER (WHERE theme = 1) AS theme_classic,
                COUNT(*) FILTER (WHERE theme = 2) AS theme_modern,
                COUNT(*) FILTER (WHERE theme = 3) AS theme_elegant,
                COUNT(*) FILTER (WHERE theme = 4) AS theme_teal,
                COUNT(*) FILTER (WHERE theme = 5) AS theme_bold,
                COALESCE(SUM(view_count), 0) AS total_views,
                COALESCE(SUM(unique_visitors), 0) AS unique_visitors,
                COUNT(*) FILTER (WHERE is_active = TRUE AND (expires_at IS NULL OR expires_at > NOW())) AS active_landing_pages
            FROM property_reports
            WHERE account_id = %s AND created_at >= %s AND created_at < %s
        """, (account_id, from_date, to_date))
        period_stats = fetchone_dict(cur) or {}
        
        # Get lead stats for period
        cur.execute("""
            SELECT
                COUNT(*) AS total_leads,
                COUNT(*) FILTER (WHERE source = 'qr_scan') AS leads_from_qr,
                COUNT(*) FILTER (WHERE source = 'direct_link') AS leads_from_direct,
                COUNT(*) FILTER (WHERE status = 'converted') AS leads_converted
            FROM leads
            WHERE account_id = %s AND created_at >= %s AND created_at < %s
        """, (account_id, from_date, to_date))
        lead_stats = fetchone_dict(cur) or {}
        
        # Get top performing reports (by views + leads)
        cur.execute("""
            SELECT 
                pr.id::text,
                pr.property_address,
                pr.property_city,
                pr.theme,
                pr.status,
                pr.view_count,
                pr.unique_visitors,
                pr.created_at,
                COUNT(l.id) AS lead_count
            FROM property_reports pr
            LEFT JOIN leads l ON l.property_report_id = pr.id
            WHERE pr.account_id = %s AND pr.status = 'complete'
            GROUP BY pr.id
            ORDER BY (pr.view_count + COUNT(l.id) * 10) DESC
            LIMIT 5
        """, (account_id,))
        top_reports = [
            {
                "id": r["id"],
                "address": r["property_address"],
                "city": r["property_city"],
                "theme": r["theme"],
                "views": r["view_count"],
                "leads": r["lead_count"],
                "created_at": r["created_at"].isoformat() if r["created_at"] else None
            }
            for r in fetchall_dicts(cur)
        ]
        
        # Get daily trend for charts
        cur.execute("""
            SELECT 
                created_at::date AS date,
                COUNT(*) AS reports
            FROM property_reports
            WHERE account_id = %s AND created_at >= %s AND created_at < %s
            GROUP BY created_at::date
            ORDER BY date
        """, (account_id, from_date, to_date))
        daily_trend = [
            {"date": r["date"].isoformat(), "reports": r["reports"]}
            for r in fetchall_dicts(cur)
        ]
        
        # Calculate conversion rate
        unique_visitors = period_stats.get("unique_visitors", 0)
        total_leads = lead_stats.get("total_leads", 0)
        conversion_rate = round((total_leads / unique_visitors * 100), 2) if unique_visitors > 0 else 0
        
        # Calculate completion rate
        total_reports = period_stats.get("total_reports", 0)
        completed = period_stats.get("completed", 0)
        completion_rate = round((completed / total_reports * 100), 2) if total_reports > 0 else 0
        
        return {
            "period": {
                "from": from_date.isoformat(),
                "to": to_date.isoformat()
            },
            "summary": {
                "total_reports": period_stats.get("total_reports", 0),
                "completed": period_stats.get("completed", 0),
                "failed": period_stats.get("failed", 0),
                "processing": period_stats.get("processing", 0),
                "completion_rate": completion_rate
            },
            "report_types": {
                "seller": period_stats.get("seller_reports", 0),
                "buyer": period_stats.get("buyer_reports", 0)
            },
            "themes": {
                "classic": period_stats.get("theme_classic", 0),
                "modern": period_stats.get("theme_modern", 0),
                "elegant": period_stats.get("theme_elegant", 0),
                "teal": period_stats.get("theme_teal", 0),
                "bold": period_stats.get("theme_bold", 0)
            },
            "engagement": {
                "total_views": period_stats.get("total_views", 0),
                "unique_visitors": unique_visitors,
                "active_landing_pages": period_stats.get("active_landing_pages", 0)
            },
            "leads": {
                "total": total_leads,
                "from_qr": lead_stats.get("leads_from_qr", 0),
                "from_direct": lead_stats.get("leads_from_direct", 0),
                "converted": lead_stats.get("leads_converted", 0),
                "conversion_rate": conversion_rate
            },
            "top_reports": top_reports,
            "daily_trend": daily_trend,
            "all_time": {
                "total_reports": cached_stats.get("total_reports", 0) if cached_stats else 0,
                "total_leads": cached_stats.get("total_leads", 0) if cached_stats else 0,
                "total_views": cached_stats.get("total_views", 0) if cached_stats else 0
            }
        }


def get_affiliate_stats(affiliate_account_id: str, from_date: Optional[datetime] = None, to_date: Optional[datetime] = None) -> Dict[str, Any]:
    """
    Get property report statistics for an affiliate (title company).
    
    Returns:
        - Aggregate stats across all sponsored agents
        - Agent leaderboard
        - Agent activity breakdown
        - Inactive agents
    """
    if not to_date:
        to_date = datetime.utcnow()
    if not from_date:
        from_date = to_date - timedelta(days=30)
    
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    
    with db_conn() as (conn, cur):
        # Admin bypass for cross-account queries
        set_rls(cur, affiliate_account_id, user_role="ADMIN")
        
        # Get all sponsored agents
        cur.execute("""
            SELECT 
                a.id::text AS account_id,
                a.name AS agent_name,
                u.email AS agent_email,
                u.avatar_url,
                a.created_at AS joined_at
            FROM accounts a
            LEFT JOIN account_users au ON au.account_id = a.id AND au.role = 'OWNER'
            LEFT JOIN users u ON u.id = au.user_id
            WHERE a.sponsor_account_id = %s
            ORDER BY a.created_at DESC
        """, (affiliate_account_id,))
        sponsored_agents = list(fetchall_dicts(cur))
        
        agent_ids = [a["account_id"] for a in sponsored_agents]
        
        if not agent_ids:
            return {
                "period": {"from": from_date.isoformat(), "to": to_date.isoformat()},
                "summary": {"total_agents": 0, "active_agents": 0, "inactive_agents": 0},
                "aggregate": {},
                "leaderboard": [],
                "agents": [],
                "inactive_agents": []
            }
        
        # Get aggregate stats for all sponsored agents
        cur.execute("""
            SELECT
                COUNT(*) AS total_reports,
                COUNT(*) FILTER (WHERE status = 'complete') AS completed,
                COUNT(*) FILTER (WHERE status = 'failed') AS failed,
                COALESCE(SUM(view_count), 0) AS total_views,
                COALESCE(SUM(unique_visitors), 0) AS unique_visitors,
                COUNT(*) FILTER (WHERE theme = 1) AS theme_classic,
                COUNT(*) FILTER (WHERE theme = 2) AS theme_modern,
                COUNT(*) FILTER (WHERE theme = 3) AS theme_elegant,
                COUNT(*) FILTER (WHERE theme = 4) AS theme_teal,
                COUNT(*) FILTER (WHERE theme = 5) AS theme_bold,
                COUNT(DISTINCT account_id) AS agents_with_reports
            FROM property_reports
            WHERE account_id = ANY(%s) AND created_at >= %s AND created_at < %s
        """, (agent_ids, from_date, to_date))
        aggregate = fetchone_dict(cur) or {}
        
        # Get lead aggregate
        cur.execute("""
            SELECT
                COUNT(*) AS total_leads,
                COUNT(*) FILTER (WHERE source = 'qr_scan') AS from_qr,
                COUNT(*) FILTER (WHERE source = 'direct_link') AS from_direct,
                COUNT(*) FILTER (WHERE status = 'converted') AS converted
            FROM leads
            WHERE account_id = ANY(%s) AND created_at >= %s AND created_at < %s
        """, (agent_ids, from_date, to_date))
        lead_aggregate = fetchone_dict(cur) or {}
        
        # Get agent leaderboard (by reports + leads)
        cur.execute("""
            SELECT
                a.id::text AS account_id,
                a.name AS agent_name,
                u.email,
                u.avatar_url,
                COUNT(pr.id) AS report_count,
                COALESCE(SUM(pr.view_count), 0) AS views,
                COUNT(l.id) AS lead_count,
                MAX(pr.created_at) AS last_activity
            FROM accounts a
            LEFT JOIN account_users au ON au.account_id = a.id AND au.role = 'OWNER'
            LEFT JOIN users u ON u.id = au.user_id
            LEFT JOIN property_reports pr ON pr.account_id = a.id AND pr.created_at >= %s AND pr.created_at < %s
            LEFT JOIN leads l ON l.account_id = a.id AND l.created_at >= %s AND l.created_at < %s
            WHERE a.sponsor_account_id = %s
            GROUP BY a.id, a.name, u.email, u.avatar_url
            ORDER BY (COUNT(pr.id) + COUNT(l.id) * 5) DESC
            LIMIT 10
        """, (from_date, to_date, from_date, to_date, affiliate_account_id))
        leaderboard = [
            {
                "account_id": r["account_id"],
                "name": r["agent_name"],
                "email": r["email"],
                "avatar": r["avatar_url"],
                "reports": r["report_count"],
                "views": r["views"],
                "leads": r["lead_count"],
                "last_activity": r["last_activity"].isoformat() if r["last_activity"] else None
            }
            for r in fetchall_dicts(cur)
        ]
        
        # Get inactive agents (no reports in 30 days)
        cur.execute("""
            SELECT
                a.id::text AS account_id,
                a.name AS agent_name,
                u.email,
                MAX(pr.created_at) AS last_report_at
            FROM accounts a
            LEFT JOIN account_users au ON au.account_id = a.id AND au.role = 'OWNER'
            LEFT JOIN users u ON u.id = au.user_id
            LEFT JOIN property_reports pr ON pr.account_id = a.id
            WHERE a.sponsor_account_id = %s
            GROUP BY a.id, a.name, u.email
            HAVING MAX(pr.created_at) IS NULL OR MAX(pr.created_at) < %s
            ORDER BY MAX(pr.created_at) NULLS FIRST
        """, (affiliate_account_id, thirty_days_ago))
        inactive_agents = [
            {
                "account_id": r["account_id"],
                "name": r["agent_name"],
                "email": r["email"],
                "last_report": r["last_report_at"].isoformat() if r["last_report_at"] else "Never"
            }
            for r in fetchall_dicts(cur)
        ]
        
        # Calculate rates
        unique_visitors = aggregate.get("unique_visitors", 0)
        total_leads = lead_aggregate.get("total_leads", 0)
        conversion_rate = round((total_leads / unique_visitors * 100), 2) if unique_visitors > 0 else 0
        
        return {
            "period": {
                "from": from_date.isoformat(),
                "to": to_date.isoformat()
            },
            "summary": {
                "total_agents": len(sponsored_agents),
                "active_agents": aggregate.get("agents_with_reports", 0),
                "inactive_agents": len(inactive_agents)
            },
            "aggregate": {
                "total_reports": aggregate.get("total_reports", 0),
                "completed": aggregate.get("completed", 0),
                "failed": aggregate.get("failed", 0),
                "total_views": aggregate.get("total_views", 0),
                "unique_visitors": unique_visitors,
                "total_leads": total_leads,
                "leads_from_qr": lead_aggregate.get("from_qr", 0),
                "leads_from_direct": lead_aggregate.get("from_direct", 0),
                "leads_converted": lead_aggregate.get("converted", 0),
                "conversion_rate": conversion_rate
            },
            "themes": {
                "classic": aggregate.get("theme_classic", 0),
                "modern": aggregate.get("theme_modern", 0),
                "elegant": aggregate.get("theme_elegant", 0),
                "teal": aggregate.get("theme_teal", 0),
                "bold": aggregate.get("theme_bold", 0)
            },
            "leaderboard": leaderboard,
            "inactive_agents": inactive_agents
        }


def get_platform_stats(from_date: Optional[datetime] = None, to_date: Optional[datetime] = None) -> Dict[str, Any]:
    """
    Get platform-wide property report statistics for admin dashboard.
    
    Returns:
        - Platform totals
        - Top affiliates
        - Top agents
        - Theme popularity
        - Account type breakdown
    """
    if not to_date:
        to_date = datetime.utcnow()
    if not from_date:
        from_date = to_date - timedelta(days=30)
    
    with db_conn() as (conn, cur):
        # Admin bypass for all queries
        set_rls(cur, "", user_role="ADMIN")
        
        # Get cached platform stats
        cur.execute("SELECT * FROM platform_property_stats WHERE id = 1")
        cached = fetchone_dict(cur)
        
        # Get period-specific platform stats
        cur.execute("""
            SELECT
                COUNT(*) AS total_reports,
                COUNT(*) FILTER (WHERE status = 'complete') AS completed,
                COUNT(*) FILTER (WHERE status = 'failed') AS failed,
                COUNT(*) FILTER (WHERE status = 'processing') AS processing,
                COALESCE(SUM(view_count), 0) AS total_views,
                COALESCE(SUM(unique_visitors), 0) AS unique_visitors,
                COUNT(*) FILTER (WHERE is_active = TRUE) AS active_landing_pages,
                COUNT(DISTINCT account_id) AS accounts_with_reports,
                COUNT(*) FILTER (WHERE theme = 1) AS theme_classic,
                COUNT(*) FILTER (WHERE theme = 2) AS theme_modern,
                COUNT(*) FILTER (WHERE theme = 3) AS theme_elegant,
                COUNT(*) FILTER (WHERE theme = 4) AS theme_teal,
                COUNT(*) FILTER (WHERE theme = 5) AS theme_bold
            FROM property_reports
            WHERE created_at >= %s AND created_at < %s
        """, (from_date, to_date))
        period_stats = fetchone_dict(cur) or {}
        
        # Get lead stats for period
        cur.execute("""
            SELECT
                COUNT(*) AS total_leads,
                COUNT(*) FILTER (WHERE source = 'qr_scan') AS from_qr,
                COUNT(*) FILTER (WHERE source = 'direct_link') AS from_direct,
                COUNT(*) FILTER (WHERE status = 'converted') AS converted
            FROM leads
            WHERE created_at >= %s AND created_at < %s
        """, (from_date, to_date))
        lead_stats = fetchone_dict(cur) or {}
        
        # Get by account type
        cur.execute("""
            SELECT
                CASE 
                    WHEN a.account_type = 'INDUSTRY_AFFILIATE' THEN 'affiliate'
                    WHEN a.sponsor_account_id IS NOT NULL THEN 'sponsored'
                    ELSE 'regular'
                END AS account_type,
                COUNT(*) AS report_count
            FROM property_reports pr
            JOIN accounts a ON a.id = pr.account_id
            WHERE pr.created_at >= %s AND pr.created_at < %s
            GROUP BY 1
        """, (from_date, to_date))
        by_account_type = {r["account_type"]: r["report_count"] for r in fetchall_dicts(cur)}
        
        # Get top affiliates
        cur.execute("""
            SELECT
                aff.id::text AS affiliate_id,
                aff.name AS affiliate_name,
                COUNT(DISTINCT a.id) AS agent_count,
                COUNT(pr.id) AS report_count,
                COALESCE(SUM(pr.view_count), 0) AS views,
                COUNT(l.id) AS lead_count
            FROM accounts aff
            JOIN accounts a ON a.sponsor_account_id = aff.id
            LEFT JOIN property_reports pr ON pr.account_id = a.id AND pr.created_at >= %s AND pr.created_at < %s
            LEFT JOIN leads l ON l.account_id = a.id AND l.created_at >= %s AND l.created_at < %s
            WHERE aff.account_type = 'INDUSTRY_AFFILIATE'
            GROUP BY aff.id, aff.name
            HAVING COUNT(pr.id) > 0
            ORDER BY COUNT(pr.id) DESC
            LIMIT 10
        """, (from_date, to_date, from_date, to_date))
        top_affiliates = [
            {
                "id": r["affiliate_id"],
                "name": r["affiliate_name"],
                "agents": r["agent_count"],
                "reports": r["report_count"],
                "views": r["views"],
                "leads": r["lead_count"]
            }
            for r in fetchall_dicts(cur)
        ]
        
        # Get top agents
        cur.execute("""
            SELECT
                a.id::text AS account_id,
                a.name AS agent_name,
                u.email,
                CASE 
                    WHEN a.sponsor_account_id IS NOT NULL THEN 'sponsored'
                    ELSE 'regular'
                END AS account_type,
                COUNT(pr.id) AS report_count,
                COALESCE(SUM(pr.view_count), 0) AS views,
                COUNT(l.id) AS lead_count
            FROM accounts a
            LEFT JOIN account_users au ON au.account_id = a.id AND au.role = 'OWNER'
            LEFT JOIN users u ON u.id = au.user_id
            LEFT JOIN property_reports pr ON pr.account_id = a.id AND pr.created_at >= %s AND pr.created_at < %s
            LEFT JOIN leads l ON l.account_id = a.id AND l.created_at >= %s AND l.created_at < %s
            WHERE a.account_type = 'REGULAR'
            GROUP BY a.id, a.name, u.email
            HAVING COUNT(pr.id) > 0
            ORDER BY COUNT(pr.id) DESC
            LIMIT 10
        """, (from_date, to_date, from_date, to_date))
        top_agents = [
            {
                "id": r["account_id"],
                "name": r["agent_name"],
                "email": r["email"],
                "type": r["account_type"],
                "reports": r["report_count"],
                "views": r["views"],
                "leads": r["lead_count"]
            }
            for r in fetchall_dicts(cur)
        ]
        
        # Get daily trend for charts
        cur.execute("""
            SELECT 
                created_at::date AS date,
                COUNT(*) AS reports,
                COALESCE(SUM(view_count), 0) AS views
            FROM property_reports
            WHERE created_at >= %s AND created_at < %s
            GROUP BY created_at::date
            ORDER BY date
        """, (from_date, to_date))
        daily_trend = [
            {"date": r["date"].isoformat(), "reports": r["reports"], "views": r["views"]}
            for r in fetchall_dicts(cur)
        ]
        
        # Calculate rates
        unique_visitors = period_stats.get("unique_visitors", 0)
        total_leads = lead_stats.get("total_leads", 0)
        conversion_rate = round((total_leads / unique_visitors * 100), 2) if unique_visitors > 0 else 0
        
        total_reports = period_stats.get("total_reports", 0)
        completed = period_stats.get("completed", 0)
        completion_rate = round((completed / total_reports * 100), 2) if total_reports > 0 else 0
        
        return {
            "period": {
                "from": from_date.isoformat(),
                "to": to_date.isoformat()
            },
            "summary": {
                "total_reports": total_reports,
                "completed": completed,
                "failed": period_stats.get("failed", 0),
                "processing": period_stats.get("processing", 0),
                "completion_rate": completion_rate,
                "accounts_with_reports": period_stats.get("accounts_with_reports", 0),
                "active_landing_pages": period_stats.get("active_landing_pages", 0)
            },
            "engagement": {
                "total_views": period_stats.get("total_views", 0),
                "unique_visitors": unique_visitors
            },
            "leads": {
                "total": total_leads,
                "from_qr": lead_stats.get("from_qr", 0),
                "from_direct": lead_stats.get("from_direct", 0),
                "converted": lead_stats.get("converted", 0),
                "conversion_rate": conversion_rate
            },
            "by_account_type": {
                "regular": by_account_type.get("regular", 0),
                "sponsored": by_account_type.get("sponsored", 0),
                "affiliate": by_account_type.get("affiliate", 0)
            },
            "themes": {
                "classic": period_stats.get("theme_classic", 0),
                "modern": period_stats.get("theme_modern", 0),
                "elegant": period_stats.get("theme_elegant", 0),
                "teal": period_stats.get("theme_teal", 0),
                "bold": period_stats.get("theme_bold", 0)
            },
            "top_affiliates": top_affiliates,
            "top_agents": top_agents,
            "daily_trend": daily_trend,
            "all_time": {
                "total_reports": cached.get("total_reports", 0) if cached else 0,
                "total_leads": cached.get("total_leads", 0) if cached else 0,
                "total_views": cached.get("total_views", 0) if cached else 0,
                "accounts_with_reports": cached.get("accounts_with_reports", 0) if cached else 0
            }
        }


def refresh_stats(account_id: Optional[str] = None) -> Dict[str, str]:
    """
    Manually trigger stats refresh.
    
    Args:
        account_id: Optional - refresh specific account only
                    If None, refreshes all accounts and platform stats
    """
    with db_conn() as (conn, cur):
        set_rls(cur, "", user_role="ADMIN")
        
        if account_id:
            cur.execute("SELECT refresh_account_property_stats(%s)", (account_id,))
            return {"message": f"Stats refreshed for account {account_id}"}
        else:
            cur.execute("SELECT refresh_all_property_stats()")
            return {"message": "All property report stats refreshed"}

