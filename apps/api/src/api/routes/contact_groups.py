from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from typing import Literal, List, Dict, Any

from ..db import db_conn, set_rls, fetchone_dict, fetchall_dicts
from .reports import require_account_id  # Reuse existing dependency

router = APIRouter(prefix="/v1")


class ContactGroupCreate(BaseModel):
  name: str
  description: str | None = None


class GroupMemberInput(BaseModel):
  member_type: Literal["contact", "sponsored_agent"]
  member_id: str


class GroupMembersAddRequest(BaseModel):
  members: List[GroupMemberInput]


@router.get("/contact-groups")
def list_contact_groups(request: Request, account_id: str = Depends(require_account_id)):
  """
  List all contact groups for the current account with member counts.
  """
  with db_conn() as (conn, cur):
    set_rls((conn, cur), account_id)

    cur.execute(
      """
      SELECT
        cg.id::text,
        cg.name,
        cg.description,
        cg.created_at,
        cg.updated_at,
        COALESCE(m.member_count, 0) AS member_count
      FROM contact_groups cg
      LEFT JOIN (
        SELECT group_id, COUNT(*) AS member_count
        FROM contact_group_members
        WHERE account_id = %s::uuid
        GROUP BY group_id
      ) m ON m.group_id = cg.id
      WHERE cg.account_id = %s::uuid
      ORDER BY cg.created_at DESC
      """,
      (account_id, account_id),
    )

    groups = list(fetchall_dicts(cur))

  return {"groups": groups}


@router.post("/contact-groups")
def create_contact_group(payload: ContactGroupCreate, request: Request, account_id: str = Depends(require_account_id)):
  """
  Create a new contact group for the current account.
  """
  with db_conn() as (conn, cur):
    set_rls((conn, cur), account_id)

    cur.execute(
      """
      INSERT INTO contact_groups (account_id, name, description)
      VALUES (%s::uuid, %s, %s)
      RETURNING
        id::text,
        account_id::text,
        name,
        description,
        created_at,
        updated_at
      """,
      (account_id, payload.name, payload.description),
    )

    group = fetchone_dict(cur)

  return group


@router.get("/contact-groups/{group_id}")
def get_contact_group(group_id: str, request: Request, account_id: str = Depends(require_account_id)):
  """
  Get a single contact group and its resolved members.
  """
  with db_conn() as (conn, cur):
    set_rls((conn, cur), account_id)

    # Load group
    cur.execute(
      """
      SELECT
        id::text,
        account_id::text,
        name,
        description,
        created_at,
        updated_at
      FROM contact_groups
      WHERE id = %s::uuid AND account_id = %s::uuid
      """,
      (group_id, account_id),
    )
    group = fetchone_dict(cur)

    if not group:
      raise HTTPException(status_code=404, detail="Group not found")

    # Load raw members
    cur.execute(
      """
      SELECT
        id::text,
        member_type,
        member_id::text,
        created_at
      FROM contact_group_members
      WHERE group_id = %s::uuid AND account_id = %s::uuid
      ORDER BY created_at ASC
      """,
      (group_id, account_id),
    )
    member_rows = list(fetchall_dicts(cur))

    members: List[Dict[str, Any]] = []

    for row in member_rows:
      member_type = row["member_type"]
      member_id = row["member_id"]

      if member_type == "contact":
        # Resolve contact details
        cur.execute(
          """
          SELECT name, email
          FROM contacts
          WHERE id = %s::uuid AND account_id = %s::uuid
          """,
          (member_id, account_id),
        )
        contact = cur.fetchone()
        if contact:
          name, email = contact
          members.append(
            {
              "id": row["id"],
              "member_type": member_type,
              "member_id": member_id,
              "name": name,
              "email": email,
            }
          )
      elif member_type == "sponsored_agent":
        # Resolve sponsored agent details (account + primary user email)
        cur.execute(
          """
          SELECT a.name, u.email
          FROM accounts a
          LEFT JOIN LATERAL (
            SELECT email
            FROM users
            WHERE account_id = a.id
            ORDER BY created_at
            LIMIT 1
          ) u ON TRUE
          WHERE a.id = %s::uuid AND a.sponsor_account_id = %s::uuid
          """,
          (member_id, account_id),
        )
        agent = cur.fetchone()
        if agent:
          name, email = agent
          members.append(
            {
              "id": row["id"],
              "member_type": member_type,
              "member_id": member_id,
              "name": name,
              "email": email,
            }
          )
      # Unknown types are ignored

  return {"group": group, "members": members}


@router.post("/contact-groups/{group_id}/members")
def add_group_members(
  group_id: str,
  payload: GroupMembersAddRequest,
  request: Request,
  account_id: str = Depends(require_account_id),
):
  """
  Add members (contacts or sponsored agents) to a group.
  """
  if not payload.members:
    raise HTTPException(status_code=400, detail="No members provided")

  with db_conn() as (conn, cur):
    set_rls((conn, cur), account_id)

    # Verify group ownership
    cur.execute(
      "SELECT id FROM contact_groups WHERE id = %s::uuid AND account_id = %s::uuid",
      (group_id, account_id),
    )
    if not cur.fetchone():
      raise HTTPException(status_code=404, detail="Group not found")

    added = 0
    skipped = 0

    for member in payload.members:
      if member.member_type == "contact":
        # Verify contact belongs to account
        cur.execute(
          "SELECT 1 FROM contacts WHERE id = %s::uuid AND account_id = %s::uuid",
          (member.member_id, account_id),
        )
        if not cur.fetchone():
          skipped += 1
          continue
      elif member.member_type == "sponsored_agent":
        # Verify sponsorship
        cur.execute(
          """
          SELECT 1
          FROM accounts
          WHERE id = %s::uuid AND sponsor_account_id = %s::uuid
          """,
          (member.member_id, account_id),
        )
        if not cur.fetchone():
          skipped += 1
          continue
      else:
        skipped += 1
        continue

      # Insert member (deduplicated by unique constraint)
      cur.execute(
        """
        INSERT INTO contact_group_members (group_id, account_id, member_type, member_id)
        VALUES (%s::uuid, %s::uuid, %s, %s::uuid)
        ON CONFLICT (group_id, member_type, member_id) DO NOTHING
        """,
        (group_id, account_id, member.member_type, member.member_id),
      )
      if cur.rowcount > 0:
        added += 1
      else:
        skipped += 1

  return {"ok": True, "added": added, "skipped": skipped}


class GroupMemberDelete(BaseModel):
  member_type: Literal["contact", "sponsored_agent"]
  member_id: str


@router.delete("/contact-groups/{group_id}/members")
def remove_group_member(
  group_id: str,
  payload: GroupMemberDelete,
  request: Request,
  account_id: str = Depends(require_account_id),
):
  """
  Remove a specific member from a group.
  """
  with db_conn() as (conn, cur):
    set_rls((conn, cur), account_id)

    # Ensure group is owned by this account
    cur.execute(
      "SELECT 1 FROM contact_groups WHERE id = %s::uuid AND account_id = %s::uuid",
      (group_id, account_id),
    )
    if not cur.fetchone():
      raise HTTPException(status_code=404, detail="Group not found")

    cur.execute(
      """
      DELETE FROM contact_group_members
      WHERE group_id = %s::uuid
        AND account_id = %s::uuid
        AND member_type = %s
        AND member_id = %s::uuid
      """,
      (group_id, account_id, payload.member_type, payload.member_id),
    )

    deleted = cur.rowcount > 0

  if not deleted:
    raise HTTPException(status_code=404, detail="Member not found in group")

  return {"ok": True}


