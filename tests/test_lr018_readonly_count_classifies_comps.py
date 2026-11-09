"""The LR-018 read-only count says what it claims to (D-377).

`scripts/readonly/lr018_asking_price_reports.sql` is what the operator runs
against production before any decision about historical reports. Jerry's
decision is to count first and change nothing. So the count has to be right:
- an asking price shown as a sale is found in both stored shapes;
- a real recorded sale is not counted;
- the agent shape's genuine ambiguity is reported as `possible`, not folded
  into `definite`;
- the script stays read-only and selects no contact details.

This seeds one report per table with a comp of every kind, runs the script's
own statements, and checks the verdicts.
"""
import json
import os
import re
import uuid
from pathlib import Path

import pytest

psycopg = pytest.importorskip("psycopg")
DB_URL = os.getenv("DATABASE_URL")
SQL = Path(__file__).resolve().parents[1] / "scripts/readonly/lr018_asking_price_reports.sql"


def _statements():
    text = "\n".join(l for l in SQL.read_text().splitlines() if not l.strip().startswith("--"))
    parts = [p.strip().rstrip(";").strip() for p in re.split(r";\s*\n", text) if p.strip()]
    return [p for p in parts if p.upper() not in ("BEGIN TRANSACTION READ ONLY", "ROLLBACK")]


@pytest.fixture
def seeded():
    if not DB_URL:
        if os.getenv("GITHUB_ACTIONS"):
            pytest.fail("DATABASE_URL is not set in CI; this test must not skip there")
        pytest.skip("Set DATABASE_URL")
    tag = uuid.uuid4().hex[:8]
    acc, user, cr, pr = (str(uuid.uuid4()) for _ in range(4))
    consumer_comps = [
        # asking price shown as a sale: no close price, counted as closed
        {"status": "Closed", "price": 950000, "list_price": 950000, "close_price": None},
        # a recorded sale
        {"status": "Closed", "price": 610000, "list_price": 625000, "close_price": 610000},
        # an active listing: never counted as a sale
        {"status": "Active", "price": 700000, "list_price": 700000, "close_price": None},
    ]
    agent_comps = [
        # collapsed to list price, no sold date: definite
        {"status": "Closed", "sale_price": 880000, "list_price": 880000, "sold_date": ""},
        # equal to list price but with a sold date: a sale at asking, or not: possible
        {"status": "Closed", "sale_price": 640000, "list_price": 640000, "sold_date": "2026-09-01"},
        # sold below asking: a recorded sale
        {"status": "Sold", "sale_price": 590000, "list_price": 615000, "sold_date": "2026-08-12"},
    ]
    with psycopg.connect(DB_URL, autocommit=True) as conn:
        conn.execute("INSERT INTO accounts (id, name, slug, account_type, plan_slug) "
                     "VALUES (%s, 'LR-018 Count', %s, 'REGULAR', 'free')", (acc, f"lr018-{tag}"))
        conn.execute("INSERT INTO users (id, account_id, email, first_name, last_name) "
                     "VALUES (%s, %s, %s, 'Dana', 'Ortiz')", (user, acc, f"lr018-{tag}@example.com"))
        conn.execute("INSERT INTO consumer_reports (id, agent_id, agent_code, consumer_phone, "
                     "property_address, comparables, status) VALUES (%s, %s, 'L18', '6265550123', "
                     "'1 Count St', %s, 'sent')", (cr, user, json.dumps(consumer_comps)))
        conn.execute("INSERT INTO property_reports (id, account_id, report_type, property_address, "
                     "property_city, property_state, property_zip, comparables, status) VALUES "
                     "(%s, %s, 'seller', '2 Count St', 'La Verne', 'CA', '91750', %s, 'complete')",
                     (pr, acc, json.dumps(agent_comps)))
    yield {"consumer": cr, "agent": pr}
    with psycopg.connect(DB_URL, autocommit=True) as conn:
        conn.execute("DELETE FROM property_reports WHERE id = %s", (pr,))
        conn.execute("DELETE FROM consumer_reports WHERE id = %s", (cr,))
        conn.execute("DELETE FROM users WHERE id = %s", (user,))
        conn.execute("DELETE FROM accounts WHERE id = %s", (acc,))


def _run_first_query_for(conn, ids):
    """The first SELECT, narrowed to the seeded reports so other rows do not count."""
    first = _statements()[0]
    narrowed = first.replace("FROM judged\nWHERE verdict IN ('definite', 'possible')",
                             "FROM judged\nWHERE verdict IN ('definite', 'possible') AND id = ANY(%s::uuid[])")
    assert narrowed != first, "the script's first query changed shape; update this test"
    return conn.execute(narrowed, (ids,)).fetchall()


def test_the_count_finds_asking_prices_in_both_shapes(seeded):
    with psycopg.connect(DB_URL) as conn:
        rows = _run_first_query_for(conn, [seeded["consumer"], seeded["agent"]])
    got = {(source, verdict): (reports, comps) for source, _status, verdict, reports, comps, *_ in rows}
    assert got == {
        ("consumer_reports", "definite"): (1, 1),   # the $950,000 asking price only
        ("property_reports", "definite"): (1, 1),   # collapsed to list, no sold date
        ("property_reports", "possible"): (1, 1),   # equal to list, with a sold date
    }, got


def test_every_statement_runs_and_the_script_is_read_only():
    text = SQL.read_text()
    assert "BEGIN TRANSACTION READ ONLY;" in text and text.rstrip().endswith("ROLLBACK;")
    body = "\n".join(l for l in text.splitlines() if not l.strip().startswith("--")).upper()
    for verb in ("INSERT ", "UPDATE ", "DELETE ", "ALTER ", "DROP ", "TRUNCATE ", "CREATE "):
        assert verb not in body, f"read-only script contains {verb.strip()}"
    for contact in ("CONSUMER_PHONE", "CONSUMER_EMAIL", "PROPERTY_ADDRESS", "ADDRESS'", "EMAIL"):
        assert contact not in body, f"script selects {contact}"
    if not DB_URL:
        pytest.skip("Set DATABASE_URL")
    with psycopg.connect(DB_URL) as conn:
        conn.read_only = True
        for stmt in _statements():
            conn.execute(stmt).fetchall()
        conn.rollback()
