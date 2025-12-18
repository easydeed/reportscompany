"""
Migration 0023: Reduce free tier report limits
- Free plan: 50 -> 5 reports/month
- Sponsored_free plan: 75 -> 10 reports/month
"""
import psycopg2

# Connect to staging database
conn = psycopg2.connect(
    'postgresql://mr_staging_db_user:vlFYf9ykajrJC7y62as6RKazBSr37fUU@dpg-d474qiqli9vc738g17e0-a.oregon-postgres.render.com/mr_staging_db'
)
cur = conn.cursor()

# Check current values before migration
print('=== Current Plan Limits ===')
cur.execute("""
    SELECT plan_slug, monthly_report_limit 
    FROM plans 
    WHERE plan_slug IN ('free', 'sponsored_free') 
    ORDER BY plan_slug
""")
for row in cur.fetchall():
    print(f'{row[0]}: {row[1]} reports/month')

print()
print('=== Running Migration 0023 ===')

# Update free plan: 50 -> 5 reports
cur.execute("""
    UPDATE plans
    SET monthly_report_limit = 5,
        updated_at = NOW()
    WHERE plan_slug = 'free'
""")
print(f'Free plan updated: {cur.rowcount} row(s)')

# Update sponsored_free plan: 75 -> 10 reports
cur.execute("""
    UPDATE plans
    SET monthly_report_limit = 10,
        updated_at = NOW()
    WHERE plan_slug = 'sponsored_free'
""")
print(f'Sponsored_free plan updated: {cur.rowcount} row(s)')

conn.commit()

# Verify new values
print()
print('=== Updated Plan Limits ===')
cur.execute("""
    SELECT plan_slug, monthly_report_limit 
    FROM plans 
    WHERE plan_slug IN ('free', 'sponsored_free') 
    ORDER BY plan_slug
""")
for row in cur.fetchall():
    print(f'{row[0]}: {row[1]} reports/month')

cur.close()
conn.close()
print()
print('✅ Migration 0023 completed successfully!')
