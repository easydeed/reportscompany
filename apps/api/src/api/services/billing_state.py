"""
Billing State Service - PASS 2

Manages stripe_subscription_id and billing_status on accounts table.
Keeps database in sync with Stripe subscription events.
"""

from uuid import UUID
from typing import Optional
import logging

logger = logging.getLogger(__name__)


def update_account_billing_state(
    cur,
    *,
    account_id: UUID | str,
    subscription: dict | None
):
    """
    Update stripe_subscription_id and billing_status on accounts.
    
    Args:
        cur: Database cursor
        account_id: Account UUID
        subscription: Stripe subscription dict or None
    
    Behavior:
        - If subscription provided: Set subscription_id and status from Stripe
        - If subscription is None: Clear subscription_id, set status to 'canceled'
    
    Returns:
        Number of rows updated (should be 1 for success, 0 if account not found)
    """
    if subscription:
        subscription_id = subscription.get("id")
        status = subscription.get("status")  # active, past_due, canceled, etc.
        
        logger.info(
            f"Updating account {account_id}: subscription_id={subscription_id}, status={status}"
        )
        
        cur.execute("""
            UPDATE accounts
            SET 
                stripe_subscription_id = %s,
                billing_status = %s
            WHERE id = %s::uuid
        """, (subscription_id, status, str(account_id)))
        
    else:
        # Subscription deleted/canceled
        logger.info(f"Clearing subscription for account {account_id}: status=canceled")
        
        cur.execute("""
            UPDATE accounts
            SET 
                stripe_subscription_id = NULL,
                billing_status = 'canceled'
            WHERE id = %s::uuid
        """, (str(account_id),))
    
    rows_updated = cur.rowcount
    
    if rows_updated == 0:
        logger.warning(f"Account {account_id} not found when updating billing state")
    
    return rows_updated

