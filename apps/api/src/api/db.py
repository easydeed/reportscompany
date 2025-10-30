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


def set_rls(cur, account_id: str):
    # Enforce RLS using Postgres session variable (matches our RLS policy)
    # Note: SET LOCAL doesn't support parameter binding, so we use sql.Literal
    cur.execute(
        sql.SQL("SET LOCAL app.current_account_id = {}").format(sql.Literal(account_id))
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

