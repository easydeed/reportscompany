#!/usr/bin/env python3
"""
Check what data exists for affiliate accounts.
"""

import os
import psycopg
from psycopg.rows import dict_row

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://mr_staging_db_user:vlFYf9ykajrJC7y62as6RKazBSr37fUU@dpg-d474qiqli9vc738g17e0-a.oregon-postgres.render.com/mr_staging_db"
)

def main():
    print("\n" + "="*80)
    print("Checking Affiliate Data")
    print("="*80 + "\n")
    
    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            # Find all affiliate accounts
            print("1. All Affiliate Accounts:")
            print("-"*80)
            cur.execute("""
                SELECT id::text, name, plan_slug, created_at
                FROM accounts
                WHERE account_type = 'INDUSTRY_AFFILIATE'
                ORDER BY created_at DESC
            """)
            
            affiliates = cur.fetchall()
            for aff in affiliates:
                print(f"  ID: {aff['id']}")
                print(f"  Name: {aff['name']}")
                print(f"  Plan: {aff['plan_slug']}")
                print(f"  Created: {aff['created_at']}")
                
                # Check for contacts
                cur.execute("SELECT COUNT(*) as count FROM contacts WHERE account_id = %s::uuid", (aff['id'],))
                contact_count = cur.fetchone()['count']
                
                # Check for groups
                cur.execute("SELECT COUNT(*) as count FROM contact_groups WHERE account_id = %s::uuid", (aff['id'],))
                group_count = cur.fetchone()['count']
                
                # Check for sponsored accounts
                cur.execute("SELECT COUNT(*) as count FROM accounts WHERE sponsor_account_id = %s::uuid", (aff['id'],))
                sponsored_count = cur.fetchone()['count']
                
                print(f"  Contacts: {contact_count}")
                print(f"  Groups: {group_count}")
                print(f"  Sponsored Agents: {sponsored_count}")
                print()
            
            if not affiliates:
                print("  No affiliate accounts found!")
                print()
            
            # Show all contacts
            print("\n2. All Contacts (any account):")
            print("-"*80)
            cur.execute("""
                SELECT 
                    c.id::text,
                    c.account_id::text,
                    a.name as account_name,
                    c.name as contact_name,
                    c.email,
                    c.type
                FROM contacts c
                JOIN accounts a ON c.account_id = a.id
                ORDER BY c.created_at DESC
                LIMIT 20
            """)
            
            contacts = cur.fetchall()
            if contacts:
                for contact in contacts:
                    print(f"  {contact['contact_name']} ({contact['email']}) [{contact['type']}]")
                    print(f"    Account: {contact['account_name']} ({contact['account_id']})")
            else:
                print("  No contacts found in database!")
            
            # Show all groups
            print("\n3. All Contact Groups:")
            print("-"*80)
            cur.execute("""
                SELECT 
                    cg.id::text,
                    cg.account_id::text,
                    a.name as account_name,
                    cg.name as group_name,
                    cg.description,
                    COUNT(cgm.id) as member_count
                FROM contact_groups cg
                JOIN accounts a ON cg.account_id = a.id
                LEFT JOIN contact_group_members cgm ON cgm.group_id = cg.id
                GROUP BY cg.id, cg.account_id, a.name, cg.name, cg.description
                ORDER BY cg.created_at DESC
            """)
            
            groups = cur.fetchall()
            if groups:
                for group in groups:
                    print(f"  {group['group_name']} ({group['member_count']} members)")
                    print(f"    Account: {group['account_name']} ({group['account_id']})")
                    if group['description']:
                        print(f"    Description: {group['description']}")
                    print()
            else:
                print("  No groups found in database!")
    
    print("="*80)
    print("[COMPLETE] Data check finished")
    print("="*80 + "\n")

if __name__ == "__main__":
    main()

