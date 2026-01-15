#!/usr/bin/env python3
import os
import psycopg2

DB_URL = os.environ.get('DATABASE_URL', 'postgresql://mr_staging_db_user:vlFYf9ykajrJC7y62as6RKazBSr37fUU@dpg-d474qiqli9vc738g17e0-a.oregon-postgres.render.com/mr_staging_db')

conn = psycopg2.connect(DB_URL)
cur = conn.cursor()

# Check for consumer_reports table
cur.execute("""
    SELECT table_name FROM information_schema.tables 
    WHERE table_schema = 'public' 
    AND table_name IN ('consumer_reports', 'sms_logs', 'report_analytics')
""")
print("Tables found:", cur.fetchall())

# Check for agent_code column in users
cur.execute("""
    SELECT column_name FROM information_schema.columns 
    WHERE table_name = 'users' 
    AND column_name IN ('agent_code', 'landing_page_headline', 'landing_page_visits')
""")
print("Users columns found:", cur.fetchall())

cur.close()
conn.close()

