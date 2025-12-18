"""Grant admin role to a user."""
import psycopg2

EMAIL_TO_PROMOTE = "info@modernagent.io"

conn = psycopg2.connect(
    'postgresql://mr_staging_db_user:vlFYf9ykajrJC7y62as6RKazBSr37fUU@dpg-d474qiqli9vc738g17e0-a.oregon-postgres.render.com/mr_staging_db'
)
cur = conn.cursor()

print(f"Granting ADMIN role to: {EMAIL_TO_PROMOTE}")

cur.execute("""
    UPDATE users 
    SET role = 'ADMIN' 
    WHERE email = %s
    RETURNING id, email, role
""", (EMAIL_TO_PROMOTE,))

row = cur.fetchone()
if row:
    conn.commit()
    print(f"SUCCESS! User {row[1]} now has role: {row[2]}")
else:
    print(f"ERROR: User with email {EMAIL_TO_PROMOTE} not found")

cur.close()
conn.close()
