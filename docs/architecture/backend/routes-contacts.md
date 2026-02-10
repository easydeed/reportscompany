# Contacts & Contact Groups API

> Manage client contacts, contact groups, and CSV import.
> Files: `apps/api/src/api/routes/contacts.py` and `contact_groups.py`

## Contacts Endpoints

| Method | Path | Purpose | Auth |
|--------|------|---------|------|
| GET | /v1/contacts | List all contacts with groups | Required |
| POST | /v1/contacts | Create contact | Required |
| GET | /v1/contacts/{id} | Get single contact | Required |
| PATCH | /v1/contacts/{id} | Update contact | Required |
| DELETE | /v1/contacts/{id} | Delete contact | Required |
| POST | /v1/contacts/import | Import from CSV | Required |

## Contact Group Endpoints

| Method | Path | Purpose | Auth |
|--------|------|---------|------|
| GET | /v1/contact-groups | List groups with member counts | Required |
| POST | /v1/contact-groups | Create group | Required |
| GET | /v1/contact-groups/{id} | Get group with resolved members | Required |
| POST | /v1/contact-groups/{id}/members | Add members to group | Required |
| DELETE | /v1/contact-groups/{id}/members | Remove member from group | Required |

## Key Functions

### GET /v1/contacts
- Single query with LEFT JOIN to get contacts + their group memberships
- Uses `json_agg` + `FILTER` for efficient group resolution in one round trip
- Returns `{contacts: [{..., groups: [{id, name}]}]}`

### POST /v1/contacts
- **Input:** `{name, email, type, phone, notes}`
- Types: `client`, `list`, `agent`, `group`
- Deduplicates on email within account
- Agent type requires email

### POST /v1/contacts/import
- Accepts CSV file upload
- Expected columns: name (required), email (required), type (optional), group (optional)
- If group column provided: creates group if missing, adds contact as member
- Uses group name cache to avoid repeated lookups
- Returns `{created_contacts, created_groups, errors: [{row, reason}]}`

### GET /v1/contact-groups/{id}
- Returns group metadata + resolved members
- Resolves contact members: fetches name/email from contacts table
- Resolves sponsored_agent members: fetches account name + primary user email
- Member types: `contact` or `sponsored_agent`

### POST /v1/contact-groups/{id}/members
- **Input:** `{members: [{member_type, member_id}]}`
- Validates ownership for each member:
  - contact: must belong to account
  - sponsored_agent: must have sponsor_account_id matching account
- Uses `ON CONFLICT DO NOTHING` for deduplication
- Returns `{ok, added, skipped}`

## Dependencies
- `db.py`: `db_conn()`, `set_rls()`, `fetchone_dict()`, `fetchall_dicts()`

## Related Files
- Frontend: `/app/people` (contacts list)
- Schedule recipients reference contacts and groups by ID
