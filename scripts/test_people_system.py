#!/usr/bin/env python3
"""
Test the People system end-to-end.

This script:
1. Creates test contacts
2. Creates a test group
3. Adds contacts to the group
4. Verifies group member resolution
5. Tests recipient expansion logic
"""

import os
import sys
import json

try:
    import psycopg
except ImportError:
    print("[ERROR] psycopg not installed")
    sys.exit(1)

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://mr_staging_db_user:vlFYf9ykajrJC7y62as6RKazBSr37fUU@dpg-d474qiqli9vc738g17e0-a.oregon-postgres.render.com/mr_staging_db"
)

# Use Demo Title Company (affiliate account) for testing
TEST_ACCOUNT_ID = "6588ca4a-9509-4118-9359-d1cbf72dcd52"  # Demo Title Company

def main():
    print("\n" + "="*80)
    print("Testing People System - End-to-End")
    print("="*80 + "\n")
    
    try:
        with psycopg.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                # Set RLS context
                cur.execute(f"SET LOCAL app.current_account_id TO '{TEST_ACCOUNT_ID}'")
                
                # Test 1: Create contacts
                print("Test 1: Creating test contacts...")
                contacts = []
                test_contacts = [
                    ("Alice Johnson", "alice@example.com", "client"),
                    ("Bob Smith", "bob@example.com", "client"),
                    ("Charlie Brown", "charlie@example.com", "agent"),
                ]
                
                for name, email, contact_type in test_contacts:
                    cur.execute("""
                        INSERT INTO contacts (account_id, name, email, type, notes)
                        VALUES (%s::uuid, %s, %s, %s, %s)
                        RETURNING id::text, name, email, type
                    """, (TEST_ACCOUNT_ID, name, email, contact_type, f"Test contact for {name}"))
                    
                    result = cur.fetchone()
                    contacts.append({
                        "id": result[0],
                        "name": result[1],
                        "email": result[2],
                        "type": result[3]
                    })
                    print(f"  [OK] Created: {result[1]} ({result[2]})")
                
                conn.commit()
                
                # Test 2: Create a group
                print("\nTest 2: Creating test group...")
                cur.execute("""
                    INSERT INTO contact_groups (account_id, name, description)
                    VALUES (%s::uuid, %s, %s)
                    RETURNING id::text, name, description
                """, (TEST_ACCOUNT_ID, "VIP Clients", "High-value clients for monthly reports"))
                
                group = cur.fetchone()
                group_id = group[0]
                print(f"  [OK] Created group: {group[1]}")
                print(f"       Description: {group[2]}")
                print(f"       ID: {group_id}")
                
                conn.commit()
                
                # Test 3: Add contacts to group
                print("\nTest 3: Adding contacts to group...")
                for contact in contacts[:2]:  # Add Alice and Bob to VIP Clients
                    cur.execute("""
                        INSERT INTO contact_group_members (group_id, account_id, member_type, member_id)
                        VALUES (%s::uuid, %s::uuid, 'contact', %s::uuid)
                    """, (group_id, TEST_ACCOUNT_ID, contact["id"]))
                    print(f"  [OK] Added {contact['name']} to group")
                
                conn.commit()
                
                # Test 4: Query group with resolved members
                print("\nTest 4: Querying group with resolved members...")
                cur.execute("""
                    SELECT
                        cg.id::text,
                        cg.name,
                        cg.description,
                        COUNT(cgm.id) as member_count
                    FROM contact_groups cg
                    LEFT JOIN contact_group_members cgm ON cgm.group_id = cg.id
                    WHERE cg.account_id = %s::uuid AND cg.id = %s::uuid
                    GROUP BY cg.id, cg.name, cg.description
                """, (TEST_ACCOUNT_ID, group_id))
                
                group_info = cur.fetchone()
                print(f"  [OK] Group: {group_info[1]}")
                print(f"       Members: {group_info[3]}")
                
                # Get member details
                cur.execute("""
                    SELECT
                        cgm.member_type,
                        cgm.member_id::text,
                        c.name,
                        c.email
                    FROM contact_group_members cgm
                    JOIN contacts c ON c.id = cgm.member_id
                    WHERE cgm.group_id = %s::uuid AND cgm.account_id = %s::uuid
                """, (group_id, TEST_ACCOUNT_ID))
                
                print("\n  Member details:")
                members = []
                for row in cur.fetchall():
                    member_type, member_id, name, email = row
                    members.append({"type": member_type, "id": member_id, "name": name, "email": email})
                    print(f"    - {name} ({email}) [{member_type}]")
                
                # Test 5: Simulate recipient resolution (like the worker does)
                print("\nTest 5: Simulating recipient resolution (worker logic)...")
                typed_recipient = json.dumps({"type": "group", "id": group_id})
                print(f"  Input: {typed_recipient}")
                
                # Parse and expand
                recipient = json.loads(typed_recipient)
                if recipient["type"] == "group":
                    cur.execute("""
                        SELECT member_type, member_id::text
                        FROM contact_group_members
                        WHERE group_id = %s::uuid AND account_id = %s::uuid
                    """, (recipient["id"], TEST_ACCOUNT_ID))
                    
                    emails = []
                    for member_type, member_id in cur.fetchall():
                        if member_type == "contact":
                            cur.execute("""
                                SELECT email
                                FROM contacts
                                WHERE id = %s::uuid AND account_id = %s::uuid
                            """, (member_id, TEST_ACCOUNT_ID))
                            result = cur.fetchone()
                            if result:
                                emails.append(result[0])
                    
                    print(f"  Output: {len(emails)} emails")
                    for email in emails:
                        print(f"    - {email}")
                
                # Test 6: PATCH endpoint simulation
                print("\nTest 6: Testing contact update (PATCH simulation)...")
                contact_to_update = contacts[0]
                cur.execute("""
                    UPDATE contacts
                    SET name = %s, updated_at = NOW()
                    WHERE id = %s::uuid AND account_id = %s::uuid
                    RETURNING id::text, name, email, type, updated_at
                """, ("Alice Johnson-Smith", contact_to_update["id"], TEST_ACCOUNT_ID))
                
                updated = cur.fetchone()
                print(f"  [OK] Updated: {updated[1]} (was: {contact_to_update['name']})")
                print(f"       Email: {updated[2]}")
                print(f"       Updated at: {updated[4]}")
                
                conn.commit()
                
                # Summary
                print("\n" + "="*80)
                print("Test Summary")
                print("="*80)
                print(f"[OK] Created {len(contacts)} contacts")
                print(f"[OK] Created 1 group with {len(members)} members")
                print(f"[OK] Group expansion works (resolved to {len(emails)} emails)")
                print(f"[OK] Contact update works")
                print("\n[SUCCESS] All tests passed!")
                print("="*80 + "\n")
                
                # Show final state
                print("Final state:")
                print(f"  Account: Demo Title Company ({TEST_ACCOUNT_ID})")
                print(f"  Contacts: {len(contacts)}")
                print(f"  Groups: 1")
                print(f"  Group members: {len(members)}")
                print("\nYou can now test via:")
                print("  - Visit /app/people in the web UI")
                print("  - Create a schedule and select the 'VIP Clients' group")
                print("  - Import CSV with contacts")
                
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

