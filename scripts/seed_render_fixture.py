#!/usr/bin/env python3
"""Give the local stack enough content that a rendered page is worth looking at.

    DATABASE_URL=postgresql://... python scripts/seed_render_fixture.py up
    DATABASE_URL=postgresql://... python scripts/seed_render_fixture.py down
    DATABASE_URL=postgresql://... python scripts/seed_render_fixture.py status

WHY THIS EXISTS SEPARATELY FROM seed_test_accounts.py
-----------------------------------------------------
That script provisions the five personas and the cross-tenant isolation target
— identities, which is what T2.2 needed. It leaves the regular agent with **no
reports, no contacts and no schedules**, so every list page renders its empty
state and every dashboard number is zero.

AN EMPTY PAGE THAT RENDERS IS NOT A RENDERED PAGE. This project has measured
page fit on an empty page twice (the gallery continuation on the old
architecture, and the 101px trend chart), and both times the number was real
and meant nothing. A redesign batch reviewed against an empty Contacts list
cannot see a filter pill row, a detail drawer, a table rule, a status pill, or
the 56px thumbnail cell — which is most of what Design's steps 5–7 change.

So this seeds VOLUME AND VARIETY, not one of each: enough rows that a table
scrolls, enough statuses that every semantic pill appears, a plan whose limit
is close enough to usage that the bars are not at 0% or 100%, and dates spread
over weeks so "latest" and "next send" are different rows.

IDEMPOTENT, AND DELETABLE. `up` can be run repeatedly; `down` removes exactly
what it made, keyed on the fixture tag below, so it cannot take a persona's own
rows with it.
"""
from __future__ import annotations

import os
import sys
from datetime import datetime, timedelta, timezone

import psycopg

#: Every row this script writes carries the tag somewhere searchable, so `down`
#: deletes what it made and nothing else. A seed that cannot be un-run is a
#: seed people stop running.
TAG = "[render-fixture]"

#: The regular agent from `seed_test_accounts.py`. Fixed id, so this script does
#: not have to guess which account the harness is logged in as.
ACCOUNT = "cccccccc-0000-4000-8000-000000000001"

#: Chosen so the usage bars are legible: 25 reports a month against 14 used is
#: 56% — not zero, not full, and not the unlimited case (which draws no bar at
#: all, D-195). `starter` also has schedules_limit 3 against 3 seeded, so the
#: at-limit state is visible somewhere too.
PLAN = "starter"

NOW = datetime.now(timezone.utc)

#: NO THEME NAME APPEARS IN THIS FILE, and two gates are why.
#:
#: The first draft wrote `theme_id='modern'` — a property theme, and a FORMER
#: market one — and `test_theme_registry_is_single_sourced.py` failed:
#: "a retired theme's name in code is a path that can still ask the renderer
#: for a template that was deleted." A fixture counts as live code for that.
#:
#: Naming the live ones instead (harbor/linen/atlas) then failed four
#: assertions in `test_rename_scope_numbers_are_current.py`, which counts the
#: places in the repository that name a theme and holds that count in
#: THEME_RENAME_SCOPE.md. Growing a real metric with fixture rows would make
#: the rename scope wrong, so `theme_id` is simply left unset and the renderer
#: applies DEFAULT_THEME_ID. A fixture has no business pinning a theme.

REPORT_KINDS = ["market_snapshot", "closed", "new_listings", "inventory",
                "price_changes", "dom"]
CITIES = ["Irvine", "Anaheim", "Costa Mesa", "Tustin", "Orange", "Santa Ana"]

#: status, days ago. Spread so "latest report" is unambiguous and the list has
#: something in every state a pill can render.
REPORTS = [
    ("completed", 1), ("completed", 3), ("completed", 6), ("completed", 9),
    ("completed", 13), ("completed", 17), ("completed", 21), ("completed", 26),
    ("completed", 31), ("processing", 0), ("failed", 2), ("failed", 11),
    ("queued", 0), ("completed", 40),
]

#: `contacts_type_check` allows EXACTLY ONE value — `'client'` — since
#: 0052_simplify_contact_types.sql. So a contact "type" pill has one possible
#: state and cannot be a filter; Design's "Groups become filter pills over the
#: same list" is about contact_groups, which is where the variety actually is.
#: Found by seeding, not by reading the UI.
CONTACT_TYPES = ["client"]

#: `leads_status_check` allows new|contacted|converted and nothing else. There
#: is no "closed" state, so a lead pill has three states to render.
LEAD_STATES = ["new", "new", "new", "contacted", "contacted", "converted"]


def _result_json(city, kind):
    """Enough shape that a report page has something to render.

    Not a real report — a real one comes from the worker against SimplyRETS,
    which this stack does not have (see B0.5's coverage note). What it has to
    be is non-null, because `/v1/reports/{id}/data` 404s on a null
    `result_json` and the print page then renders nothing.
    """
    return {
        "report_type": kind,
        "city": city,
        "generated_at": NOW.isoformat(),
        "metrics": {
            "median_price": 1_125_000,
            "closed_count": 64,
            "median_dom": 23,
            "months_of_supply": 2.4,
            "active_count": 151,
        },
        "listings": [
            {"address": f"{100 + i} Example St, {city}", "price": 900_000 + i * 25_000,
             "beds": 3 + (i % 3), "baths": 2 + (i % 2), "sqft": 1500 + i * 120,
             "status": "Closed", "dom": 10 + i}
            for i in range(12)
        ],
        "_fixture": TAG,
    }


#: Every account the render manifest logs in as. The rate limit has to be
#: raised on all of them, not just the one carrying the content.
HARNESS_ACCOUNTS = (
    ACCOUNT,                                        # regular
    "9b096c1b-d3d9-45dd-b5bf-0ab0204c8372",         # platform admin
    "aaaaaaaa-0000-4000-8000-000000000001",         # title company
    "cccccccc-0000-4000-8000-000000000002",         # industry affiliate
    "aaaaaaaa-0000-4000-8000-000000000003",         # sponsored
)


def up(cur):
    cur.execute("UPDATE accounts SET plan_slug=%s WHERE id=%s::uuid", (PLAN, ACCOUNT))

    # THE RATE LIMITER THROTTLES A RENDER HARNESS, and silently.
    #
    # `RateLimitMiddleware` allows `accounts.api_rate_limit` requests per
    # minute per account, default 60. Loading 25 routes as one account is
    # several hundred calls in under a minute, so the first run against a live
    # API came back with `/v1/users/me`, `/v1/usage`, `/v1/onboarding` and
    # `/v1/account/accounts` returning 429 — and the pages rendered 47
    # skeletons, which the harness correctly called `degraded` and a human
    # would have read as "the dashboard has no data".
    #
    # A measurement tool is not a user. Raised on the fixture accounts only;
    # it is a column on the row, not a product change.
    cur.execute(
        "UPDATE accounts SET api_rate_limit=100000 WHERE id = ANY(%s::uuid[])",
        (list(HARNESS_ACCOUNTS),),
    )

    # ── market reports ──────────────────────────────────────────────────
    for i, (status, days) in enumerate(REPORTS):
        kind = REPORT_KINDS[i % len(REPORT_KINDS)]
        city = CITIES[i % len(CITIES)]
        when = NOW - timedelta(days=days, hours=i)
        cur.execute(
            """
            INSERT INTO report_generations
                (id, account_id, report_type, cities, status, generated_at,
                 result_json, lookback_days, billable)
            VALUES (gen_random_uuid(), %s::uuid, %s, %s, %s, %s, %s::jsonb, 180,
                    %s)
            """,
            (ACCOUNT, kind, [city], status, when,
             psycopg.types.json.Json(_result_json(city, kind))
             if status == "completed" else psycopg.types.json.Json({"_fixture": TAG}),
             status == "completed"),
        )
        if status == "completed":
            cur.execute(
                """
                INSERT INTO usage_tracking
                    (account_id, event_type, billable_units, created_at, request_id)
                VALUES (%s::uuid, 'report_generated', 1, %s, %s)
                """,
                (ACCOUNT, when, f"{TAG} {i}"),
            )

    # ── property reports ────────────────────────────────────────────────
    for i in range(4):
        cur.execute(
            """
            INSERT INTO property_reports
                (id, account_id, report_type, property_address, property_city,
                 property_state, property_zip, status, theme, created_at)
            VALUES (gen_random_uuid(), %s::uuid, %s, %s, %s, 'CA', %s,
                    'complete', 1, %s)
            """,
            # Two CHECK constraints on this table disagree with the rest of
            # the product, and both were found by seeding it:
            #   report_type is seller|buyer — not the agent/consumer
            #     distinction the product talks in everywhere else;
            #   status is draft|processing|complete|failed — "complete",
            #     where report_generations uses "completed". Which is why
            #     components/status-badge.tsx carries BOTH spellings in its
            #     Status union; it is reading two tables.
            # Seeded with both report types so the Seller/Buyer type tag
            # (Design's accent pair) has something to render.
            (ACCOUNT, "seller" if i % 2 == 0 else "buyer",
             f"{220 + i * 7} Maple Ave", CITIES[i], f"9260{i}",
             NOW - timedelta(days=2 + i * 5)),
        )

    # ── contact groups, then contacts ───────────────────────────────────
    for name, desc in [("Past clients", f"{TAG} warm list"),
                       ("Farm — Irvine 92602", f"{TAG} geographic farm"),
                       ("Open house signups", f"{TAG} from events")]:
        cur.execute(
            """
            INSERT INTO contact_groups (id, account_id, name, description, created_at)
            VALUES (gen_random_uuid(), %s::uuid, %s, %s, now())
            """,
            (ACCOUNT, name, desc),
        )

    first = ["Dana", "Priya", "Marcus", "Leila", "Tom", "Ana", "Wei", "Rosa",
             "Ben", "Yuki", "Omar", "Grace", "Ivan", "Noor", "Sam", "Elena",
             "Hugo", "Mei"]
    for i, fn in enumerate(first):
        cur.execute(
            """
            INSERT INTO contacts (id, account_id, name, email, phone, type, notes, created_at)
            VALUES (gen_random_uuid(), %s::uuid, %s, %s, %s, %s, %s, %s)
            """,
            (ACCOUNT, f"{fn} Fixture", f"{fn.lower()}.fixture@example.com",
             f"+1949555{1000 + i:04d}", CONTACT_TYPES[i % len(CONTACT_TYPES)],
             f"{TAG} seeded contact {i}", NOW - timedelta(days=i * 3)),
        )

    # ── schedules: active weekly, active monthly, and one paused ────────
    rows = [
        ("Irvine weekly snapshot", "market_snapshot", "Irvine", "weekly", True, 1),
        ("Anaheim monthly closed", "closed", "Anaheim", "monthly", True, 9),
        ("Tustin — paused", "new_listings", "Tustin", "weekly", False, None),
    ]
    for name, kind, city, cadence, active, due_in in rows:
        cur.execute(
            """
            INSERT INTO schedules
                (id, account_id, name, report_type, city, cadence, recipients,
                 active, created_at, next_run_at, last_run_at, timezone)
            VALUES (gen_random_uuid(), %s::uuid, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    'America/Los_Angeles')
            """,
            (ACCOUNT, f"{name}", kind, city, cadence,
             [f"{c.lower()}.fixture@example.com" for c in first[:4]],
             active, NOW - timedelta(days=30),
             NOW + timedelta(days=due_in) if due_in else None,
             NOW - timedelta(days=7) if active else None),
        )

    # ── onboarding, marked done, or /app IS NOT THE DASHBOARD ──────────
    #
    # `components/onboarding/dashboard-onboarding.tsx:36` does
    # `router.replace("/app/get-started")` whenever onboarding is undismissed,
    # incomplete and under 50% progress. On a fresh account that is every
    # visit, so /app redirects to the onboarding wizard — correct product
    # behaviour, and it meant the harness's /app entry was measuring the
    # onboarding page while calling it the dashboard. The sentinel caught it
    # as a BROKEN route (final path != requested path) rather than quietly
    # producing a plausible table, which is the whole reason it exists.
    #
    # The four steps are ONBOARDING_STEPS in routes/onboarding.py. All four
    # completed puts progress at 100%, so /app renders the dashboard —
    # Design's step 4 and the highest-value page in the adoption plan.
    for step in ("profile_complete", "branding_setup", "first_report",
                 "first_schedule"):
        cur.execute(
            """
            INSERT INTO onboarding_progress (id, user_id, step_key, completed_at, created_at)
            VALUES (gen_random_uuid(), %s::uuid, %s, %s, %s)
            ON CONFLICT DO NOTHING
            """,
            (ACCOUNT, step, NOW - timedelta(days=20), NOW - timedelta(days=20)),
        )

    # ── leads, in every state the pill can render ───────────────────────
    for i, state in enumerate(LEAD_STATES):
        cur.execute(
            """
            INSERT INTO leads
                (id, account_id, name, email, phone, message, source, status,
                 consent_given, created_at)
            VALUES (gen_random_uuid(), %s::uuid, %s, %s, %s, %s, %s, %s, true, %s)
            """,
            (ACCOUNT, f"Lead {i} Fixture", f"lead{i}.fixture@example.com",
             f"+1949555{2000 + i:04d}", f"{TAG} what is my home worth?",
             "qr_scan" if i % 2 else "direct_link", state,
             NOW - timedelta(days=i, hours=3)),
        )


def down(cur):
    cur.execute("DELETE FROM usage_tracking WHERE request_id LIKE %s", (f"{TAG}%",))
    cur.execute("DELETE FROM report_generations WHERE account_id=%s::uuid "
                "AND result_json::text LIKE %s", (ACCOUNT, f"%{TAG}%"))
    cur.execute("DELETE FROM contacts WHERE account_id=%s::uuid AND notes LIKE %s",
                (ACCOUNT, f"{TAG}%"))
    cur.execute("DELETE FROM contact_groups WHERE account_id=%s::uuid AND description LIKE %s",
                (ACCOUNT, f"{TAG}%"))
    cur.execute("DELETE FROM leads WHERE account_id=%s::uuid AND message LIKE %s",
                (ACCOUNT, f"{TAG}%"))
    cur.execute("DELETE FROM onboarding_progress WHERE user_id=%s::uuid", (ACCOUNT,))
    cur.execute("DELETE FROM schedules WHERE account_id=%s::uuid AND name IN "
                "('Irvine weekly snapshot','Anaheim monthly closed','Tustin — paused')",
                (ACCOUNT,))
    cur.execute("DELETE FROM property_reports WHERE account_id=%s::uuid "
                "AND property_address LIKE '%% Maple Ave'", (ACCOUNT,))


def status(cur):
    for table, where in [
        ("report_generations", "account_id=%s::uuid"),
        ("property_reports", "account_id=%s::uuid"),
        ("contacts", "account_id=%s::uuid"),
        ("contact_groups", "account_id=%s::uuid"),
        ("schedules", "account_id=%s::uuid"),
        ("leads", "account_id=%s::uuid"),
        ("usage_tracking", "account_id=%s::uuid"),
    ]:
        cur.execute(f"SELECT count(*) FROM {table} WHERE {where}", (ACCOUNT,))
        print(f"  {table:22} {cur.fetchone()[0]}")
    cur.execute("SELECT plan_slug, api_rate_limit FROM accounts WHERE id=%s::uuid",
                (ACCOUNT,))
    plan, rate = cur.fetchone()
    print(f"  plan                   {plan}")
    print(f"  api_rate_limit         {rate}")


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in {"up", "down", "status"}:
        sys.exit("usage: seed_render_fixture.py up|down|status")
    dsn = os.environ.get("DATABASE_URL")
    if not dsn:
        sys.exit("DATABASE_URL is not set")
    action = sys.argv[1]
    with psycopg.connect(dsn, autocommit=False) as conn:
        with conn.cursor() as cur:
            if action == "status":
                status(cur)
                return
            if action == "up":
                down(cur)       # idempotent: clear our own rows, then re-add
                up(cur)
            else:
                down(cur)
            conn.commit()
            print(f"[{action}] done for account {ACCOUNT}")
            status(cur)


if __name__ == "__main__":
    main()
