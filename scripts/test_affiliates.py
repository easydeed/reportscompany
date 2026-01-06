#!/usr/bin/env python3
"""Test affiliates query."""
import psycopg

DATABASE_URL = "postgresql://mr_staging_db_user:vlFYf9ykajrJC7y62as6RKazBSr37fUU@dpg-d474qiqli9vc738g17e0-a.oregon-postgres.render.com/mr_staging_db"

def main():
    conn = psycopg.connect(DATABASE_URL)
    cur = conn.cursor()

    print("Testing affiliates query...")
    cur.execute("""
        SELECT
            a.id::text,
            a.name,
            a.slug,
            a.plan_slug,
            a.is_active,
            a.created_at,
            ab.logo_url,
            ab.primary_color,
            ab.brand_display_name,
            (SELECT COUNT(*) FROM accounts sa WHERE sa.sponsor_account_id = a.id) as agent_count,
            (SELECT COUNT(*) FROM report_generations rg
             JOIN accounts sa ON rg.account_id = sa.id
             WHERE sa.sponsor_account_id = a.id
             AND rg.generated_at >= date_trunc('month', CURRENT_DATE)) as reports_this_month
        FROM accounts a
        LEFT JOIN affiliate_branding ab ON ab.account_id = a.id
        WHERE a.account_type = 'INDUSTRY_AFFILIATE'
        ORDER BY a.created_at DESC LIMIT 100
    """)
    rows = cur.fetchall()
    print(f"Found {len(rows)} affiliates")
    for row in rows:
        print(f"  Name: {row[1]}, is_active: {row[4]}, agents: {row[9]}, reports: {row[10]}")

    conn.close()
    print("Done!")

if __name__ == "__main__":
    main()








