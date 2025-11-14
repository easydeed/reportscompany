from contextlib import contextmanager
from typing import Any, Dict, Iterable, Optional, Tuple
import psycopg
from psycopg import sql
from .settings import settings


@contextmanager
def db_conn():
    # psycopg3 connection; autocommit False so SET LOCAL applies to the tx
    with psycopg.connect(settings.DATABASE_URL, autocommit=False) as conn:
        with conn.cursor() as cur:
            yield conn, cur
        # ensure commit unless caller rolled back
        conn.commit()


def set_rls(cur, account_id: str, user_id: str | None = None, user_role: str | None = None):
    """
    Enforce RLS using Postgres session variables.
    
    Phase 29C: Extended to support multi-account and affiliate context.
    
    Args:
        cur: Database cursor
        account_id: Current account context (required)
        user_id: Current user ID (optional, for Phase 29C multi-account)
        user_role: User's global role (optional, for Phase 29C affiliate/admin features)
    """
    # SET LOCAL expects a plain string value, so we manually quote it
    # (sql.Literal adds unwanted type casts like ::uuid)
    cur.execute(f"SET LOCAL app.current_account_id TO '{account_id}'")
    
    # Phase 29C: Set user context for multi-account RLS (future use)
    if user_id:
        cur.execute(f"SET LOCAL app.current_user_id TO '{user_id}'")
    if user_role:
        cur.execute(f"SET LOCAL app.current_user_role TO '{user_role}'")



def fetchone_dict(cur) -> Optional[Dict[str, Any]]:
    row = cur.fetchone()
    if row is None:
        return None
    cols = [desc.name for desc in cur.description]
    return dict(zip(cols, row))


def fetchall_dicts(cur) -> Iterable[Dict[str, Any]]:
    cols = [desc.name for desc in cur.description]
    for row in cur.fetchall():
        yield dict(zip(cols, row))

