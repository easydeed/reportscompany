"""
Account Services

Phase 29C: Multi-account and affiliate support services
"""

from typing import List, Dict, Any, Optional


def get_user_accounts(cur, user_id: str) -> List[Dict[str, Any]]:
    """
    Get all accounts the user belongs to with their role.
    
    Phase 29C: Enables multi-account user experience.
    
    Args:
        cur: Database cursor
        user_id: User UUID
    
    Returns:
        List of account dictionaries with role information:
        [
            {
                "account_id": "uuid",
                "name": "Account Name",
                "account_type": "REGULAR" | "INDUSTRY_AFFILIATE",
                "plan_slug": "free",
                "role": "OWNER" | "MEMBER" | "AFFILIATE" | "ADMIN"
            },
            ...
        ]
    """
    cur.execute("""
        SELECT 
            a.id::text AS account_id,
            a.name,
            a.account_type,
            a.plan_slug,
            au.role,
            a.created_at
        FROM accounts a
        JOIN account_users au ON au.account_id = a.id
        WHERE au.user_id = %s::uuid
        ORDER BY 
            CASE WHEN au.role = 'OWNER' THEN 0
                 WHEN au.role = 'MEMBER' THEN 1
                 WHEN au.role = 'AFFILIATE' THEN 2
                 ELSE 3
            END,
            a.created_at ASC
    """, (user_id,))
    
    accounts = []
    for row in cur.fetchall():
        accounts.append({
            "account_id": row[0],
            "name": row[1],
            "account_type": row[2],
            "plan_slug": row[3],
            "role": row[4],
            "created_at": row[5].isoformat() if row[5] else None,
        })
    
    return accounts


def get_default_account_for_user(cur, user_id: str) -> Optional[str]:
    """
    Get the default account ID for a user.
    
    Logic:
    1. First account where role='OWNER'
    2. Otherwise, first account in user's list
    
    Args:
        cur: Database cursor
        user_id: User UUID
    
    Returns:
        Account ID (string) or None if user has no accounts
    """
    accounts = get_user_accounts(cur, user_id)
    
    if not accounts:
        return None
    
    # Prefer OWNER accounts
    for acc in accounts:
        if acc["role"] == "OWNER":
            return acc["account_id"]
    
    # Fallback to first account
    return accounts[0]["account_id"]


def verify_user_account_access(cur, user_id: str, account_id: str) -> bool:
    """
    Verify that a user has access to a specific account.
    
    Args:
        cur: Database cursor
        user_id: User UUID
        account_id: Account UUID to check access for
    
    Returns:
        True if user belongs to the account, False otherwise
    """
    cur.execute("""
        SELECT 1
        FROM account_users
        WHERE user_id = %s::uuid
          AND account_id = %s::uuid
    """, (user_id, account_id))
    
    return cur.fetchone() is not None


def get_account_info(cur, account_id: str) -> Optional[Dict[str, Any]]:
    """
    Get basic account information.
    
    Args:
        cur: Database cursor
        account_id: Account UUID
    
    Returns:
        Account info dict or None if not found
    """
    cur.execute("""
        SELECT 
            id::text,
            name,
            account_type,
            plan_slug,
            sponsor_account_id::text
        FROM accounts
        WHERE id = %s::uuid
    """, (account_id,))
    
    row = cur.fetchone()
    if not row:
        return None
    
    return {
        "account_id": row[0],
        "name": row[1],
        "account_type": row[2],
        "plan_slug": row[3],
        "sponsor_account_id": row[4],
    }

