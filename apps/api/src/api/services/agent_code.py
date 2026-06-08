"""
Agent Code Generation Service

Generates short, unambiguous, *permanent* codes for agent CMA pages.

Format: 4 characters from a Crockford-style alphabet that excludes the
common "look-alike" characters (0/O, 1/I/l, 5/S, 2/Z, etc.) so codes
read cleanly on business cards, in email signatures, and over the
phone. 27^4 = 531,441 combinations — plenty of room for a long time.

Codes are CASE-INSENSITIVE: lookups in `get_agent_by_code` use
`LOWER()` so both new lowercase codes and historical uppercase codes
continue to resolve correctly.
"""

import logging
import secrets
from typing import Optional

logger = logging.getLogger(__name__)

# Crockford-style alphabet — excludes confusing characters:
#   0/O, 1/I/l, 5/S, 2/Z, plus uppercase look-alikes.
CLEAN_ALPHABET = "346789abcdefghjkmnpqrtuvwxy"


def _clean_random(length: int = 4) -> str:
    """Generate a random string from the unambiguous alphabet."""
    return "".join(secrets.choice(CLEAN_ALPHABET) for _ in range(length))


def generate_unique_agent_code(cur, max_attempts: int = 20) -> str:
    """
    Mint a unique, unused 4-character agent code.

    27^4 = 531,441 combinations, so collisions are extremely rare. If
    we somehow hit 20 in a row at 4 chars we expand to 6 (387,420,489
    combinations) and finally fall back to 8 chars as a hard guarantee.

    The caller is responsible for writing the code to the appropriate
    column (the function doesn't UPDATE — it just returns a free code).
    """
    for length in (4, 6, 8):
        for _ in range(max_attempts):
            code = _clean_random(length)
            cur.execute(
                "SELECT 1 FROM users WHERE LOWER(agent_code) = %s",
                (code,),
            )
            if not cur.fetchone():
                return code
    # 20 collisions at every length is statistically impossible; if we
    # somehow get here something else is wrong. Surface it.
    raise RuntimeError("Could not generate a unique agent code after retries")


# ── Backwards-compatible aliases ──────────────────────────────────────
# Older call sites used these names. They still work, but new callers
# should prefer generate_unique_agent_code(cur).

def generate_agent_code(length: int = 4) -> str:
    """Random code (no uniqueness check). Prefer generate_unique_agent_code."""
    return _clean_random(length)


def create_unique_agent_code(conn, cursor, user_id: str, max_attempts: int = 20) -> str:
    """Generate AND persist a unique code on the users row."""
    code = generate_unique_agent_code(cursor, max_attempts=max_attempts)
    cursor.execute(
        "UPDATE users SET agent_code = %s WHERE id = %s",
        (code, user_id),
    )
    conn.commit()
    logger.info("Generated agent code %s for user %s", code, user_id)
    return code


def get_or_create_agent_code(conn, cursor, user_id: str) -> str:
    """Return existing code, minting one if missing."""
    cursor.execute("SELECT agent_code FROM users WHERE id = %s", (user_id,))
    result = cursor.fetchone()
    if result and result[0]:
        return result[0]
    return create_unique_agent_code(conn, cursor, user_id)


def validate_agent_code(code: str) -> bool:
    """Validate an external code matches our format. Case-insensitive."""
    if not code or len(code) < 3 or len(code) > 20:
        return False
    return all(c in CLEAN_ALPHABET for c in code.lower())


# ── Lookup helpers ────────────────────────────────────────────────────

def get_agent_by_code(cursor, agent_code: str) -> Optional[dict]:
    """
    Look up an agent by their unique code (case-insensitive so old
    uppercase codes and new lowercase codes both resolve).
    Joins accounts to pull branding (logo, primary_color).
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
            u.landing_page_visits,
            a.logo_url,
            a.primary_color,
            a.website_url,
            u.job_title,
            a.secondary_color
        FROM users u
        JOIN accounts a ON a.id = u.account_id
        WHERE LOWER(u.agent_code) = LOWER(%s)
        """,
        (agent_code,),
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
        "landing_page_headline": row[11] or "What's Your Home Worth?",
        "landing_page_subheadline": row[12] or "Get a free, professional property report in seconds.",
        "landing_page_theme_color": row[13] or "#4F46E5",
        "landing_page_enabled": row[14] if row[14] is not None else True,
        "landing_page_visits": row[15] or 0,
        "logo_url": row[16],
        "primary_color": row[17],
        "website_url": row[18],
        "job_title": row[19],
        "accent_color": row[20],
    }


def increment_landing_page_visits(conn, cursor, agent_code: str) -> None:
    """
    Increment the visit counter for an agent's landing page
    (case-insensitive match so historical uppercase codes still work).
    """
    cursor.execute(
        "UPDATE users SET landing_page_visits = landing_page_visits + 1 "
        "WHERE LOWER(agent_code) = LOWER(%s)",
        (agent_code,),
    )
    conn.commit()
