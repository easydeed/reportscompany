#!/usr/bin/env python3
"""
Phase 2A test-account provisioning (Rev A T2.1).

Provisions throwaway accounts covering all five personas, plus a second
title-company tenant (Company B) with its own reps, agents, and data, so the
T2.2 cross-tenant isolation test has a real target to attempt to read.

Personas (Rev A §1 derivation — account_type is only REGULAR/INDUSTRY_AFFILIATE/
TITLE_COMPANY; COMPANY_REP and SPONSORED are derived by parent/sponsor linkage):

  regular@test-tenant.example.com      REGULAR,            no parent/sponsor         plan free
  affiliate@test-tenant.example.com    INDUSTRY_AFFILIATE, no parent                 plan affiliate
  company-a@test-tenant.example.com    TITLE_COMPANY  (Company A admin)              plan affiliate
  rep-a@test-tenant.example.com        INDUSTRY_AFFILIATE, parent=Company A          plan affiliate
  sponsored-a@test-tenant.example.com  REGULAR, sponsor=Rep A                        plan sponsored_free

Company B (isolation target):
  company-b@test-tenant.example.com    TITLE_COMPANY (Company B admin)
  rep-b@test-tenant.example.com        INDUSTRY_AFFILIATE, parent=Company B
  + report_generations, schedules, contacts, property_reports, affiliate_branding under B

All passwords: TestPass123!  (bcrypt via pgcrypto crypt()).
All emails/slugs prefixed 'test-'/@test-tenant.example.com and use fixed UUIDs (0xA.../0xB...)
so teardown is exact and cannot touch real data.

Usage:
    DATABASE_URL=postgresql://... python scripts/seed_test_accounts.py up
    DATABASE_URL=postgresql://... python scripts/seed_test_accounts.py down
"""
import os
import sys
import psycopg

PW = "TestPass123!"

# Fixed UUIDs — A-tenant 0xaa.., B-tenant 0xbb..
A_CO   = "aaaaaaaa-0000-4000-8000-000000000001"
A_REP  = "aaaaaaaa-0000-4000-8000-000000000002"
A_SPON = "aaaaaaaa-0000-4000-8000-000000000003"
REG    = "cccccccc-0000-4000-8000-000000000001"
AFF    = "cccccccc-0000-4000-8000-000000000002"
B_CO   = "bbbbbbbb-0000-4000-8000-000000000001"
B_REP  = "bbbbbbbb-0000-4000-8000-000000000002"

# account uuid -> (name, slug, account_type, plan_slug, parent, sponsor, email, role_label)
ACCOUNTS = [
    (REG,    "Test Regular Agent",  "test-regular",   "REGULAR",            "free",           None,  None,  "regular@test-tenant.example.com"),
    (AFF,    "Test Affiliate",      "test-affiliate", "INDUSTRY_AFFILIATE", "affiliate",      None,  None,  "affiliate@test-tenant.example.com"),
    (A_CO,   "Test Company A",      "test-company-a", "TITLE_COMPANY",      "affiliate",      None,  None,  "company-a@test-tenant.example.com"),
    (A_REP,  "Test Rep A",          "test-rep-a",     "INDUSTRY_AFFILIATE", "affiliate",      A_CO,  None,  "rep-a@test-tenant.example.com"),
    (A_SPON, "Test Sponsored A",    "test-sponsored-a","REGULAR",           "sponsored_free", None,  A_REP, "sponsored-a@test-tenant.example.com"),
    (B_CO,   "Test Company B",      "test-company-b", "TITLE_COMPANY",      "affiliate",      None,  None,  "company-b@test-tenant.example.com"),
    (B_REP,  "Test Rep B",          "test-rep-b",     "INDUSTRY_AFFILIATE", "affiliate",      B_CO,  None,  "rep-b@test-tenant.example.com"),
]

ALL_ACCT_IDS = [a[0] for a in ACCOUNTS]


def up(cur):
    cur.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto;")
    for aid, name, slug, atype, plan, parent, sponsor, email in ACCOUNTS:
        cur.execute(
            """
            INSERT INTO accounts (id, name, slug, account_type, plan_slug, status, is_active,
                                  parent_account_id, sponsor_account_id, created_at, updated_at)
            VALUES (%s,%s,%s,%s,%s,'active',true,%s,%s,now(),now())
            ON CONFLICT (id) DO UPDATE SET account_type=EXCLUDED.account_type,
                 plan_slug=EXCLUDED.plan_slug, parent_account_id=EXCLUDED.parent_account_id,
                 sponsor_account_id=EXCLUDED.sponsor_account_id;
            """,
            (aid, name, slug, atype, plan, parent, sponsor),
        )
        # user owns its account; password via pgcrypto bcrypt
        cur.execute(
            """
            INSERT INTO users (id, account_id, email, password_hash, role, email_verified, is_active,
                               created_at, updated_at)
            VALUES (%s,%s,%s, crypt(%s, gen_salt('bf')), 'OWNER', true, true, now(), now())
            ON CONFLICT (id) DO UPDATE SET password_hash=EXCLUDED.password_hash,
                 account_id=EXCLUDED.account_id, email_verified=true;
            """,
            (aid, aid, email, PW),  # user id == account id for simplicity (distinct namespace ok)
        )
        cur.execute(
            """
            INSERT INTO account_users (account_id, user_id, role, created_at)
            VALUES (%s,%s,'OWNER',now())
            ON CONFLICT (account_id, user_id) DO UPDATE SET role='OWNER';
            """,
            (aid, aid),
        )

    # --- Data under Company B and Rep B (the isolation target) ---
    # report_generations for Rep B and Company B
    for acct, rtype in [(B_REP, "market_snapshot"), (B_CO, "new_listings")]:
        cur.execute(
            """
            INSERT INTO report_generations (id, account_id, report_type, cities, status, generated_at)
            VALUES (gen_random_uuid(), %s, %s, ARRAY['Irvine'], 'completed', now())
            ON CONFLICT DO NOTHING;
            """,
            (acct, rtype),
        )
    # schedule for Rep B
    cur.execute(
        """
        INSERT INTO schedules (id, account_id, name, report_type, city, cadence, recipients, active, created_at)
        VALUES (gen_random_uuid(), %s, 'B-secret weekly', 'market_snapshot', 'Irvine',
                'weekly', ARRAY['b-client@example.com'], true, now())
        ON CONFLICT DO NOTHING;
        """,
        (B_REP,),
    )
    # contact for Rep B
    cur.execute(
        """
        INSERT INTO contacts (id, account_id, name, email, type, created_at)
        VALUES (gen_random_uuid(), %s, 'B Secret Contact', 'b-secret@example.com', 'client', now())
        ON CONFLICT DO NOTHING;
        """,
        (B_REP,),
    )
    # property_report for Rep B
    cur.execute(
        """
        INSERT INTO property_reports (id, account_id, report_type, property_address, property_city,
                                      property_state, property_zip, status, created_at, updated_at)
        VALUES (gen_random_uuid(), %s, 'seller', '1 Secret St', 'Irvine', 'CA', '92602', 'complete', now(), now())
        ON CONFLICT DO NOTHING;
        """,
        (B_REP,),
    )
    # affiliate_branding for Company B and Rep B
    for acct, nm in [(B_CO, "Company B Brand"), (B_REP, "Rep B Brand")]:
        cur.execute(
            """
            INSERT INTO affiliate_branding (account_id, brand_display_name, primary_color, created_at, updated_at)
            VALUES (%s,%s,'#123456', now(), now())
            ON CONFLICT (account_id) DO UPDATE SET brand_display_name=EXCLUDED.brand_display_name;
            """,
            (acct, nm),
        )

    # Give Company A one report so its own dashboard has a positive control
    cur.execute(
        """
        INSERT INTO report_generations (id, account_id, report_type, cities, status, generated_at)
        VALUES (gen_random_uuid(), %s, 'market_snapshot', ARRAY['Anaheim'], 'completed', now())
        ON CONFLICT DO NOTHING;
        """,
        (A_REP,),
    )
    print(f"[up] provisioned {len(ACCOUNTS)} accounts + Company B data. password={PW}")


def down(cur):
    # child data first (FKs), then memberships, users, accounts — all by our fixed ids
    ids = tuple(ALL_ACCT_IDS)
    for tbl in ("report_generations", "schedules", "contacts", "property_reports", "affiliate_branding"):
        cur.execute(f"DELETE FROM {tbl} WHERE account_id = ANY(%s);", (list(ids),))
    cur.execute("DELETE FROM account_users WHERE account_id = ANY(%s);", (list(ids),))
    cur.execute("DELETE FROM users WHERE account_id = ANY(%s);", (list(ids),))
    # clear parent/sponsor self-refs before deleting to avoid FK ordering issues
    cur.execute("UPDATE accounts SET parent_account_id=NULL, sponsor_account_id=NULL WHERE id = ANY(%s);", (list(ids),))
    cur.execute("DELETE FROM accounts WHERE id = ANY(%s);", (list(ids),))
    print(f"[down] removed {len(ids)} test accounts and their data")


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in ("up", "down"):
        print("usage: seed_test_accounts.py up|down", file=sys.stderr)
        sys.exit(2)
    dsn = os.environ.get("DATABASE_URL")
    if not dsn:
        print("DATABASE_URL not set", file=sys.stderr)
        sys.exit(1)
    with psycopg.connect(dsn, autocommit=False) as conn:
        with conn.cursor() as cur:
            (up if sys.argv[1] == "up" else down)(cur)
        conn.commit()


if __name__ == "__main__":
    main()
