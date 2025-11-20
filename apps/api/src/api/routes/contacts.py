"""
Contacts API - Manage client contacts, recipients, and lists.

Used by the People view to show all contacts associated with an account.
Supports affiliates and regular agents.
"""
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, EmailStr
from typing import Literal
from ..db import db_conn, set_rls, fetchall_dicts, fetchone_dict

router = APIRouter(prefix="/v1")


class ContactCreate(BaseModel):
    name: str
    email: EmailStr
    type: Literal["client", "list", "agent"]
    notes: str | None = None


class ContactUpdate(BaseModel):
    name: str | None = None
    email: EmailStr | None = None
    type: Literal["client", "list", "agent"] | None = None
    notes: str | None = None


@router.get("/contacts")
def list_contacts(request: Request):
    """
    List all contacts for the current account.
    
    Returns contacts created by this account for scheduling and People view.
    """
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
            WHERE account_id = %s::uuid
            ORDER BY created_at DESC
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
        
        # Check for duplicate email within account
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
            INSERT INTO contacts (account_id, name, email, type, notes)
            VALUES (%s::uuid, %s, %s, %s, %s)
            RETURNING 
                id::text,
                account_id::text,
                name,
                email,
                type,
                notes,
                created_at,
                updated_at
        """, (account_id, contact.name, contact.email, contact.type, contact.notes))
        
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

