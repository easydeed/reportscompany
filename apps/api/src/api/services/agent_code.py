"""
Agent Code Generation Service

Generates unique 6-character codes for agents.
Format: Alphanumeric, uppercase, no confusing characters (0, O, I, L)
"""

import random
import string
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Characters that are easy to read (no 0/O, I/L confusion)
ALLOWED_CHARS = 'ABCDEFGHJKMNPQRSTUVWXYZ23456789'


def generate_agent_code(length: int = 6) -> str:
    """Generate a random agent code."""
    return ''.join(random.choices(ALLOWED_CHARS, k=length))


def create_unique_agent_code(conn, cursor, user_id: str, max_attempts: int = 10) -> str:
    """
    Generate a unique agent code and save to user record.
    Retries if code already exists.
    
    Args:
        conn: Database connection
        cursor: Database cursor
        user_id: User UUID to assign the code to
        max_attempts: Maximum retry attempts
        
    Returns:
        The generated agent code
        
    Raises:
        ValueError: If unable to generate unique code after max attempts
    """
    for _ in range(max_attempts):
        code = generate_agent_code()
        
        # Check if code exists
        cursor.execute("SELECT 1 FROM users WHERE agent_code = %s", (code,))
        existing = cursor.fetchone()
        
        if not existing:
            # Save to user
            cursor.execute(
                "UPDATE users SET agent_code = %s WHERE id = %s",
                (code, user_id)
            )
            conn.commit()
            logger.info(f"Generated agent code {code} for user {user_id}")
            return code
    
    raise ValueError("Could not generate unique agent code after max attempts")


def get_or_create_agent_code(conn, cursor, user_id: str) -> str:
    """
    Get existing code or create new one.
    
    Args:
        conn: Database connection
        cursor: Database cursor
        user_id: User UUID
        
    Returns:
        The user's agent code (existing or newly generated)
    """
    cursor.execute("SELECT agent_code FROM users WHERE id = %s", (user_id,))
    result = cursor.fetchone()
    
    if result and result[0]:
        return result[0]
    
    return create_unique_agent_code(conn, cursor, user_id)


def validate_agent_code(code: str) -> bool:
    """
    Validate that a code follows the expected format.
    
    Args:
        code: The agent code to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not code or len(code) != 6:
        return False
    
    return all(c in ALLOWED_CHARS for c in code.upper())


def get_agent_by_code(cursor, agent_code: str) -> Optional[dict]:
    """
    Look up an agent by their unique code.
    
    Args:
        cursor: Database cursor
        agent_code: The agent's unique code
        
    Returns:
        Agent info dict or None if not found
    """
    cursor.execute(
        """
        SELECT 
            u.id,
            u.account_id,
            u.first_name,
            u.last_name,
            CONCAT(u.first_name, ' ', u.last_name) as full_name,
            u.email,
            u.phone,
            u.company_name,
            COALESCE(u.photo_url, u.avatar_url) as photo_url,
            u.license_number,
            u.agent_code,
            u.landing_page_headline,
            u.landing_page_subheadline,
            u.landing_page_theme_color,
            u.landing_page_enabled,
            u.landing_page_visits
        FROM users u
        WHERE u.agent_code = %s
        """,
        (agent_code.upper(),)
    )
    row = cursor.fetchone()
    
    if not row:
        return None
    
    return {
        "id": str(row[0]),
        "account_id": str(row[1]),
        "first_name": row[2],
        "last_name": row[3],
        "full_name": row[4],
        "email": row[5],
        "phone": row[6],
        "company_name": row[7],
        "photo_url": row[8],
        "license_number": row[9],
        "agent_code": row[10],
        "landing_page_headline": row[11] or "Get Your Free Home Value Report",
        "landing_page_subheadline": row[12] or "Find out what your home is worth in today's market.",
        "landing_page_theme_color": row[13] or "#8B5CF6",
        "landing_page_enabled": row[14] if row[14] is not None else True,
        "landing_page_visits": row[15] or 0,
    }


def increment_landing_page_visits(conn, cursor, agent_code: str) -> None:
    """
    Increment the visit counter for an agent's landing page.
    
    Args:
        conn: Database connection
        cursor: Database cursor
        agent_code: The agent's unique code
    """
    cursor.execute(
        "UPDATE users SET landing_page_visits = landing_page_visits + 1 WHERE agent_code = %s",
        (agent_code.upper(),)
    )
    conn.commit()

