"""Check for admin users in the database."""
import psycopg2

conn = psycopg2.connect(
    'postgresql://mr_staging_db_user:vlFYf9ykajrJC7y62as6RKazBSr37fUU@dpg-d474qiqli9vc738g17e0-a.oregon-postgres.render.com/mr_staging_db'
)
cur = conn.cursor()

print("=== Users with admin role ===")
cur.execute("SELECT id, email, role, first_name, last_name FROM users WHERE UPPER(role) = 'ADMIN'")
rows = cur.fetchall()
if rows:
    for row in rows:
        print(f"  ID: {str(row[0])[:8]}... Email: {row[1]}, Role: {row[2]}, Name: {row[3]} {row[4]}")
else:
    print("  No admin users found!")

print()
print("=== Potential admin candidates (your emails) ===")
cur.execute("""
    SELECT id, email, role, first_name, last_name 
    FROM users 
    WHERE email ILIKE '%modernagent%' 
       OR email ILIKE '%trendyreports%'
       OR email ILIKE '%easydeed%'
    LIMIT 10
""")
for row in cur.fetchall():
    print(f"  ID: {str(row[0])[:8]}... Email: {row[1]}, Role: {row[2] or 'NULL'}, Name: {row[3]} {row[4]}")

cur.close()
conn.close()
