"""LR-025 (D-383): 0067 rewrites the stored Home Value Page description only
where it is still the untouched 0039 default (Jerry, 2026-11-11).

Runs the migration file itself, inside a transaction that is rolled back, on
rows made for the test: one still on the default, one an agent edited, one
whose text differs from the default only by its apostrophe, one NULL.
"""
import os
import uuid
from pathlib import Path

import psycopg
import pytest

DB = os.environ.get("DATABASE_URL")
pytestmark = pytest.mark.skipif(not DB, reason="needs DATABASE_URL (real PostgreSQL)")

REPO = Path(__file__).resolve().parents[3]
MIGRATION = REPO / "db/migrations/0067_lead_page_description_default.sql"
OLD = "Find out what your home is worth in today's market."
NEW = "See what homes like yours have sold for."
EDITED = "Thinking of selling? I'll send you the numbers."
CURLY = "Find out what your home is worth in today’s market."


def _setup(cur):
    acc = str(uuid.uuid4())
    tag = uuid.uuid4().hex[:10]
    cur.execute("INSERT INTO accounts (id, name, slug) VALUES (%s, %s, %s)", (acc, f"LR-025 {tag}", f"lr025-{tag}"))
    ids = {}
    for name, value in (("default", OLD), ("edited", EDITED), ("curly", CURLY), ("null", None)):
        uid = str(uuid.uuid4())
        cur.execute("INSERT INTO users (id, account_id, email, landing_page_subheadline) VALUES (%s, %s, %s, %s)",
                    (uid, acc, f"{name}-{tag}@example.com", value))
        ids[name] = uid
    return acc, ids


def _values(cur, ids):
    cur.execute("SELECT id::text, landing_page_subheadline FROM users WHERE id = ANY(%s::uuid[])", (list(ids.values()),))
    by_id = dict(cur.fetchall())
    return {name: by_id[uid] for name, uid in ids.items()}


def test_only_the_untouched_default_is_rewritten_and_new_pages_get_the_new_default():
    with psycopg.connect(DB, autocommit=False) as conn, conn.cursor() as cur:
        try:
            acc, ids = _setup(cur)
            cur.execute(MIGRATION.read_text(encoding="utf-8"))
            after = _values(cur, ids)
            cur.execute(MIGRATION.read_text(encoding="utf-8"))   # a second run changes nothing more
            again = _values(cur, ids)
            fresh = str(uuid.uuid4())
            cur.execute("INSERT INTO users (id, account_id, email) VALUES (%s, %s, %s) RETURNING landing_page_subheadline",
                        (fresh, acc, f"fresh-{fresh[:8]}@example.com"))
            new_page = cur.fetchone()[0]
        finally:
            conn.rollback()
    assert after == {"default": NEW, "edited": EDITED, "curly": CURLY, "null": None}, after
    assert again == after
    assert new_page == NEW, "a page created after 0067 still gets the old default"


def test_the_migration_changes_nothing_but_that_value_and_the_default():
    sql = MIGRATION.read_text(encoding="utf-8")
    body = "\n".join(line for line in sql.splitlines() if not line.lstrip().startswith("--"))
    statements = [s.strip() for s in body.split(";") if s.strip()]
    assert len(statements) == 3, statements
    assert statements[0].startswith("SET LOCAL lock_timeout")
    assert statements[1].split() == ["ALTER", "TABLE", "users", "ALTER", "COLUMN", "landing_page_subheadline",
                                     "SET", "DEFAULT", "'See", "what", "homes", "like", "yours", "have", "sold", "for.'"]
    assert "landing_page_headline" not in body
