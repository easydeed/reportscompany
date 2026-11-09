"""The LR-018 read-only count says what it claims to (D-377).

`scripts/readonly/lr018_asking_price_reports.sql` is what the operator runs
against production before any decision about historical reports. Jerry's
decision is to count first and change nothing. So the count has to be right:
- an asking price shown as a sale is DEFINITE only where the stored row can
  prove it (the consumer shape, which keeps `close_price`);
- in the agent shape a sale at the asking price is only POSSIBLE, with or
  without a sold date: a genuine sale at asking has exactly that shape (Codex
  review of #277);
- a comp with no status, no list price to compare against, or only a legacy
  `sold_price` is UNKNOWN, never silently clean;
- a real recorded sale is not counted;
- query 1 is by verdict (overlapping); query 2 counts each report once;
- the script stays read-only and selects no contact details.
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


def _narrowed(stmt):
    """The statement restricted to the seeded reports, so other rows do not count."""
    out = (stmt.replace("FROM consumer_reports r,",
                        "FROM (SELECT * FROM consumer_reports WHERE id = ANY(%(ids)s::uuid[])) r,")
               .replace("FROM property_reports r,",
                        "FROM (SELECT * FROM property_reports WHERE id = ANY(%(ids)s::uuid[])) r,"))
    assert out.count("%(ids)s") == 2, "the script's table sources changed shape; update this test"
    return out


def _ago(days):
    from datetime import date, timedelta
    return (date.today() - timedelta(days=days)).isoformat()


@pytest.fixture
def seeded():
    if not DB_URL:
        if os.getenv("GITHUB_ACTIONS"):
            pytest.fail("DATABASE_URL is not set in CI; this test must not skip there")
        pytest.skip("Set DATABASE_URL")
    tag = uuid.uuid4().hex[:8]
    acc, user = str(uuid.uuid4()), str(uuid.uuid4())
    ids = {k: str(uuid.uuid4()) for k in ("cr_affected", "cr_clean", "pr_mixed", "pr_unknown")}
    consumer = {
        "cr_affected": [
            {"status": "Closed", "price": 950000, "list_price": 950000, "close_price": None},   # definite
            {"status": "Closed", "price": 610000, "list_price": 625000, "close_price": 610000}, # recorded
            {"status": "Active", "price": 700000, "list_price": 700000, "close_price": None},   # not a sale
        ],
        "cr_clean": [
            {"status": "Closed", "price": 640000, "list_price": 650000, "close_price": 640000},
        ],
    }
    agent = {
        "pr_mixed": [
            # equal to asking, no sold date: still only possible
            {"status": "Closed", "sale_price": 880000, "list_price": 880000, "sold_date": ""},
            # equal to asking, with a sold date: possible
            {"status": "Closed", "sale_price": 640000, "list_price": 640000, "sold_date": _ago(30)},
            # sold below asking: recorded
            {"status": "Sold", "sale_price": 590000, "list_price": 615000, "sold_date": _ago(40)},
            # no status: unknown
            {"sale_price": 700000, "list_price": 700000},
            # only a legacy sold_price: unknown
            {"status": "Closed", "sold_price": 655000},
            # a sale with nothing to compare against: unknown
            {"status": "Closed", "sale_price": 600000, "sold_date": _ago(20)},
        ],
        "pr_unknown": [
            {"sale_price": 720000, "list_price": 730000},
        ],
    }
    with psycopg.connect(DB_URL, autocommit=True) as conn:
        conn.execute("INSERT INTO accounts (id, name, slug, account_type, plan_slug) "
                     "VALUES (%s, 'LR-018 Count', %s, 'REGULAR', 'free')", (acc, f"lr018-{tag}"))
        conn.execute("INSERT INTO users (id, account_id, email, first_name, last_name) "
                     "VALUES (%s, %s, %s, 'Dana', 'Ortiz')", (user, acc, f"lr018-{tag}@example.com"))
        for key, comps in consumer.items():
            conn.execute("INSERT INTO consumer_reports (id, agent_id, agent_code, consumer_phone, "
                         "property_address, comparables, status) VALUES (%s, %s, 'L18', '6265550123', "
                         "'1 Count St', %s, 'sent')", (ids[key], user, json.dumps(comps)))
        for key, comps in agent.items():
            conn.execute("INSERT INTO property_reports (id, account_id, report_type, property_address, "
                         "property_city, property_state, property_zip, comparables, status) VALUES "
                         "(%s, %s, 'seller', '2 Count St', 'La Verne', 'CA', '91750', %s, 'complete')",
                         (ids[key], acc, json.dumps(comps)))
    yield ids
    with psycopg.connect(DB_URL, autocommit=True) as conn:
        for key in ("pr_mixed", "pr_unknown"):
            conn.execute("DELETE FROM property_reports WHERE id = %s", (ids[key],))
        for key in ("cr_affected", "cr_clean"):
            conn.execute("DELETE FROM consumer_reports WHERE id = %s", (ids[key],))
        conn.execute("DELETE FROM users WHERE id = %s", (user,))
        conn.execute("DELETE FROM accounts WHERE id = %s", (acc,))


def test_query_one_gives_every_comp_its_verdict(seeded):
    with psycopg.connect(DB_URL) as conn:
        rows = conn.execute(_narrowed(_statements()[0]), {"ids": list(seeded.values())}).fetchall()
    got = {(source, verdict): (reports, comps, undated)
           for source, _status, verdict, reports, comps, undated, *_ in rows}
    assert got == {
        ("consumer_reports", "definite"): (1, 1, 1),
        ("property_reports", "possible"): (1, 2, 1),          # with and without a sold date
        ("property_reports", "unknown: no status"): (2, 2, 2),
        ("property_reports", "unknown: legacy sold_price"): (1, 1, 1),
        ("property_reports", "unknown: no list price"): (1, 1, 0),
    }, got


def test_query_two_counts_each_report_once_under_its_worst_verdict(seeded):
    with psycopg.connect(DB_URL) as conn:
        rows = conn.execute(_narrowed(_statements()[1]), {"ids": list(seeded.values())}).fetchall()
    got = {(source, worst): reports for source, _status, worst, reports in rows}
    assert got == {
        ("consumer_reports", "definite"): 1,
        ("consumer_reports", "clean"): 1,
        ("property_reports", "possible"): 1,
        ("property_reports", "unknown"): 1,
    }, got
    assert sum(got.values()) == len(seeded), "a report was counted twice or not at all"


def test_the_two_copies_of_the_classification_are_identical():
    """A read-only transaction cannot create a view, so the CTE is repeated."""
    def block(stmt):
        return stmt[:stmt.index("SELECT source, report_status") if "worst AS" not in stmt
                    else stmt.index("worst AS")].strip().rstrip(",")
    first, second = _statements()[0], _statements()[1]
    assert block(first) == block(second)


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
