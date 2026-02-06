"""
Database connection module with connection pooling.

BEFORE: Every db_conn() call opened a new TCP connection (~200ms each).
AFTER:  Connections come from a warm pool (~0ms acquisition).
"""

from contextlib import contextmanager
from typing import Any, Dict, Iterable, Optional
import psycopg
from psycopg import sql
from psycopg_pool import ConnectionPool
from .settings import settings
import logging

logger = logging.getLogger(__name__)

# ============================================================================
# CONNECTION POOL
# Initialized once at first use (lazy singleton), reused for all requests.
# Render Starter PostgreSQL supports ~100 connections.
# We use 2-10 to leave room for worker, migrations, admin tools.
# ============================================================================

_pool: ConnectionPool | None = None


def get_pool() -> ConnectionPool:
    """Get or create the connection pool (lazy singleton)."""
    global _pool
    if _pool is None:
        _pool = ConnectionPool(
            conninfo=settings.DATABASE_URL,
            min_size=2,          # Keep 2 warm connections ready
            max_size=10,         # Scale up to 10 under load
            max_idle=300,        # Close idle connections after 5 min
            max_lifetime=1800,   # Recycle every 30 min (prevents stale)
            timeout=10,          # Max 10s wait for available connection
        )
    return _pool


@contextmanager
def db_conn():
    """
    Get a pooled database connection.
    
    Usage is IDENTICAL to before — no route code needs to change:
        with db_conn() as (conn, cur):
            set_rls(cur, account_id)
            cur.execute(...)
    
    But connections now come from a pool (~0ms) instead of
    being created fresh each time (~200ms).
    """
    pool = get_pool()
    with pool.connection() as conn:
        conn.autocommit = False  # Required for SET LOCAL (RLS)
        with conn.cursor() as cur:
            yield conn, cur
        conn.commit()


@contextmanager
def db_conn_autocommit():
    """
    Pooled connection with autocommit=True.
    Use for simple reads that don't need RLS transactions
    (like middleware lookups).
    """
    pool = get_pool()
    with pool.connection() as conn:
        conn.autocommit = True
        with conn.cursor() as cur:
            yield cur


def set_rls(conn_or_cur, account_id: str, user_id: str | None = None,
            user_role: str | None = None):
    """
    Enforce RLS using Postgres session variables.
    
    FIX (M3): Uses parameterized sql.Literal instead of f-string interpolation
    to prevent SQL injection if account_id is ever malformed.
    """
    if isinstance(conn_or_cur, tuple):
        conn, cur = conn_or_cur
    else:
        cur = conn_or_cur

    cur.execute(
        sql.SQL("SET LOCAL app.current_account_id TO {}").format(sql.Literal(account_id))
    )
    if user_id:
        cur.execute(
            sql.SQL("SET LOCAL app.current_user_id TO {}").format(sql.Literal(user_id))
        )
    if user_role:
        cur.execute(
            sql.SQL("SET LOCAL app.current_user_role TO {}").format(sql.Literal(user_role))
        )


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
