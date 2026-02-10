# Contacts Page

> `apps/web/app/app/people/page.tsx`

## Route: `/app/people`

Unified contacts management page. Combines regular contacts and sponsored agents (for affiliates) into a single view.

### API Calls (parallel on mount)

| Endpoint | Purpose |
|----------|---------|
| `GET /v1/contacts` | Fetch all contacts |
| `GET /v1/contact-groups` | Fetch all groups |
| `GET /v1/affiliate/overview` | Fetch sponsored accounts (403 for non-affiliates, expected) |

### Features

**People Tab:**
- Unified list of contacts + sponsored agents
- Search by name/email
- Filter by type: All, Agents, Groups, Sponsored Agents
- Bulk selection with checkboxes
- Per-contact actions: Edit, Manage Groups, Delete
- Per-sponsored-agent actions: Edit (view-only fields + unsponsor toggle)

**Groups Tab:**
- Create groups with name/description
- View/manage group members
- Add contacts or sponsored agents to groups
- Remove members from groups

**Add Contact Dialog:**
- Type-first form: Agent, Group, Client, List
- Fields adapt based on type (email required for agents, optional for others)

**Import Dialog:**
- CSV upload (`POST /v1/contacts/import`)
- Expected columns: name, email, type (optional), group (optional)
- Shows import summary with error details

**Manage Groups Dialog (per contact):**
- Shows current group memberships
- Add/remove from groups in one dialog

### Contact Types

- `client` - Individual client
- `list` - Recipient list
- `agent` - External agent (requires email)
- `group` - Office/company group

### API Calls for Mutations

| Action | Endpoint |
|--------|----------|
| Add contact | `POST /v1/contacts` |
| Update contact | `PATCH /v1/contacts/{id}` |
| Delete contact | `DELETE /v1/contacts/{id}` |
| Import CSV | `POST /v1/contacts/import` (FormData) |
| Create group | `POST /v1/contact-groups` |
| Add to group | `POST /v1/contact-groups/{groupId}/members` |
| Remove from group | `DELETE /v1/contact-groups/{groupId}/members` |
| View group detail | `GET /v1/contact-groups/{groupId}` |
| Unsponsor agent | `POST /v1/affiliate/accounts/{accountId}/unsponsor` |

## Key Files

- `apps/web/app/app/people/page.tsx` - Main page (large file, ~1800 lines)
