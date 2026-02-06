"""
Contacts API - Manage client contacts, recipients, and lists.

Used by the People view to show all contacts associated with an account.
Supports affiliates and regular agents.
"""
from fastapi import APIRouter, HTTPException, Request, UploadFile, File
from pydantic import BaseModel, EmailStr
from typing import Literal
import csv
import io
from ..db import db_conn, set_rls, fetchall_dicts, fetchone_dict

router = APIRouter(prefix="/v1")


class ContactCreate(BaseModel):
    name: str
    email: EmailStr | None = None
    type: Literal["client", "list", "agent", "group"]
    phone: str | None = None
    notes: str | None = None
    
    def model_post_init(self, __context):
        """Validate fields based on type."""
        if self.type == "agent":
            if not self.email:
                raise ValueError("Email is required for agent contacts")
        elif self.type == "group":
            # Groups don't require email or phone
            pass


class ContactUpdate(BaseModel):
    name: str | None = None
    email: EmailStr | None = None
    type: Literal["client", "list", "agent", "group"] | None = None
    phone: str | None = None
    notes: str | None = None


@router.get("/contacts")
def list_contacts(request: Request):
    """
    List all contacts for the current account.
    
    Returns contacts with their group memberships for the People view.
    Optimized with a single query using LEFT JOIN and array_agg.
    """
    account_id = getattr(request.state, "account_id", None)
    if not account_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    with db_conn() as (conn, cur):
        set_rls((conn, cur), account_id)
        
        # Single query with LEFT JOIN to get contacts + groups in one round trip
        cur.execute("""
            SELECT 
                c.id::text,
                c.account_id::text,
                c.name,
                c.email,
                c.type,
                c.phone,
                c.notes,
                c.created_at,
                c.updated_at,
                COALESCE(
                    json_agg(
                        json_build_object('id', cg.id::text, 'name', cg.name)
                    ) FILTER (WHERE cg.id IS NOT NULL),
                    '[]'::json
                ) AS groups
            FROM contacts c
            LEFT JOIN contact_group_members cgm 
                ON cgm.member_type = 'contact' 
                AND cgm.member_id = c.id 
                AND cgm.account_id = c.account_id
            LEFT JOIN contact_groups cg 
                ON cg.id = cgm.group_id
            WHERE c.account_id = %s::uuid
            GROUP BY c.id, c.account_id, c.name, c.email, c.type, c.phone, c.notes, c.created_at, c.updated_at
            ORDER BY c.created_at DESC
        """, (account_id,))
        
        contacts = list(fetchall_dicts(cur))
        
    return {"contacts": contacts}


@router.post("/contacts")
def create_contact(contact: ContactCreate, request: Request):
    """
    Create a new contact.
    
    Args:
        contact: Contact details (name, email, type, notes)
    
    Returns:
        Created contact with ID
    """
    account_id = getattr(request.state, "account_id", None)
    if not account_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    with db_conn() as (conn, cur):
        set_rls((conn, cur), account_id)
        
        # Check for duplicate email within account (only if email provided)
        if contact.email:
            cur.execute("""
                SELECT id FROM contacts
                WHERE account_id = %s::uuid AND email = %s
            """, (account_id, contact.email))
            
            if cur.fetchone():
                raise HTTPException(
                    status_code=400,
                    detail=f"A contact with email {contact.email} already exists"
                )
        
        # Insert contact
        cur.execute("""
            INSERT INTO contacts (account_id, name, email, type, phone, notes)
            VALUES (%s::uuid, %s, %s, %s, %s, %s)
            RETURNING 
                id::text,
                account_id::text,
                name,
                email,
                phone,
                type,
                notes,
                created_at,
                updated_at
        """, (account_id, contact.name, contact.email, contact.type, contact.phone, contact.notes))
        
        result = fetchone_dict(cur)
        
    return result


@router.get("/contacts/{contact_id}")
def get_contact(contact_id: str, request: Request):
    """Get a specific contact by ID."""
    account_id = getattr(request.state, "account_id", None)
    if not account_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    with db_conn() as (conn, cur):
        set_rls((conn, cur), account_id)
        
        cur.execute("""
            SELECT 
                id::text,
                account_id::text,
                name,
                email,
                type,
                notes,
                created_at,
                updated_at
            FROM contacts
            WHERE id = %s::uuid AND account_id = %s::uuid
        """, (contact_id, account_id))
        
        contact = fetchone_dict(cur)
        
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    return contact


@router.patch("/contacts/{contact_id}")
def update_contact(contact_id: str, updates: ContactUpdate, request: Request):
    """Update a contact."""
    account_id = getattr(request.state, "account_id", None)
    if not account_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    with db_conn() as (conn, cur):
        set_rls((conn, cur), account_id)
        
        # Build dynamic UPDATE
        fields = []
        values = []
        
        if updates.name is not None:
            fields.append("name = %s")
            values.append(updates.name)
        if updates.email is not None:
            fields.append("email = %s")
            values.append(updates.email)
        if updates.type is not None:
            fields.append("type = %s")
            values.append(updates.type)
        if updates.phone is not None:
            fields.append("phone = %s")
            values.append(updates.phone)
        if updates.notes is not None:
            fields.append("notes = %s")
            values.append(updates.notes)
        
        if not fields:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        fields.append("updated_at = now()")
        values.extend([contact_id, account_id])
        
        cur.execute(f"""
            UPDATE contacts
            SET {', '.join(fields)}
            WHERE id = %s::uuid AND account_id = %s::uuid
            RETURNING 
                id::text,
                account_id::text,
                name,
                email,
                type,
                notes,
                created_at,
                updated_at
        """, values)
        
        contact = fetchone_dict(cur)
        
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    return contact


@router.delete("/contacts/{contact_id}")
def delete_contact(contact_id: str, request: Request):
    """Delete a contact."""
    account_id = getattr(request.state, "account_id", None)
    if not account_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    with db_conn() as (conn, cur):
        set_rls((conn, cur), account_id)
        
        cur.execute("""
            DELETE FROM contacts
            WHERE id = %s::uuid AND account_id = %s::uuid
            RETURNING id
        """, (contact_id, account_id))
        
        deleted = cur.fetchone()
        
    if not deleted:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    return {"ok": True, "deleted_id": contact_id}


@router.post("/contacts/import")
def import_contacts(request: Request, file: UploadFile = File(...)):
    """
    Import contacts from a CSV file.

    Expected columns (header row):
      - name (required)
      - email (required)
      - type (optional: client | agent | list; default: client)
      - group (optional: group name; will create group if missing)

    If group is provided, a contact group will be created (if needed) and the
    contact will be added as a member (member_type='contact').
    """
    account_id = getattr(request.state, "account_id", None)
    if not account_id:
        raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        content = file.file.read().decode("utf-8")
    except Exception:
        raise HTTPException(status_code=400, detail="Unable to read uploaded file as UTF-8")

    reader = csv.DictReader(io.StringIO(content))

    created_contacts = 0
    created_groups = 0
    errors: list[dict] = []

    with db_conn() as (conn, cur):
        set_rls((conn, cur), account_id)

        # Cache of group_name -> group_id to avoid repeated lookups
        group_cache: dict[str, str] = {}

        for idx, row in enumerate(reader, start=2):  # start=2 to account for header row
            name = (row.get("name") or "").strip()
            email = (row.get("email") or "").strip()
            raw_type = (row.get("type") or "").strip().lower()
            group_name = (row.get("group") or "").strip()

            if not name or not email:
                errors.append({"row": idx, "reason": "Missing name or email"})
                continue

            contact_type: str
            if raw_type in ("client", "agent", "list"):
                contact_type = raw_type
            else:
                contact_type = "client"

            try:
                # Insert contact (dedupe on email within account)
                cur.execute(
                    """
                    SELECT id FROM contacts
                    WHERE account_id = %s::uuid AND email = %s
                    """,
                    (account_id, email),
                )
                existing = cur.fetchone()

                if existing:
                    contact_id = existing[0]
                else:
                    cur.execute(
                        """
                        INSERT INTO contacts (account_id, name, email, type)
                        VALUES (%s::uuid, %s, %s, %s)
                        RETURNING id::text
                        """,
                        (account_id, name, email, contact_type),
                    )
                    contact_id = cur.fetchone()[0]
                    created_contacts += 1

                # Handle optional group
                if group_name:
                    group_id = group_cache.get(group_name)
                    if not group_id:
                        # Find or create group
                        cur.execute(
                            """
                            SELECT id::text FROM contact_groups
                            WHERE account_id = %s::uuid AND name = %s
                            """,
                            (account_id, group_name),
                        )
                        row_group = cur.fetchone()
                        if row_group:
                            group_id = row_group[0]
                        else:
                            cur.execute(
                                """
                                INSERT INTO contact_groups (account_id, name)
                                VALUES (%s::uuid, %s)
                                RETURNING id::text
                                """,
                                (account_id, group_name),
                            )
                            group_id = cur.fetchone()[0]
                            created_groups += 1

                        group_cache[group_name] = group_id

                    # Insert membership (deduped by unique constraint)
                    cur.execute(
                        """
                        INSERT INTO contact_group_members (group_id, account_id, member_type, member_id)
                        VALUES (%s::uuid, %s::uuid, 'contact', %s::uuid)
                        ON CONFLICT (group_id, member_type, member_id) DO NOTHING
                        """,
                        (group_id, account_id, contact_id),
                    )

            except Exception as e:
                errors.append({"row": idx, "reason": str(e)})

    return {
        "created_contacts": created_contacts,
        "created_groups": created_groups,
        "errors": errors,
    }

