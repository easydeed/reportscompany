# PEOPLE SYSTEM AUDIT vs FINAL SPEC

**Date**: Nov 24, 2025  
**Purpose**: Compare actual implementation against the final spec to identify gaps

---

## AUDIT STATUS LEGEND

✅ **IMPLEMENTED & WORKING** - Matches spec, tested  
🟡 **PARTIALLY IMPLEMENTED** - Exists but incomplete or buggy  
❌ **MISSING** - Not implemented  
🔍 **NEEDS VERIFICATION** - Code exists but not tested

---

## 1. DATA MODEL

### 1.1 Contacts Table

| Requirement | Status | Notes |
|-------------|--------|-------|
| `id`, `account_id`, `type`, `name`, `email`, `phone`, `notes` | ✅ | Migration 0014 added `phone`, nullable `email` |
| `type` = "agent", "client", "list", "group" | ✅ | CHECK constraint updated |
| `email` nullable for "group" | ✅ | Migration 0014 |
| RLS enforces `account_id` | ✅ | Verified in migrations |

### 1.2 Groups Tables

| Requirement | Status | Notes |
|-------------|--------|-------|
| `contact_groups` table exists | ✅ | Has `id`, `account_id`, `name`, `description` |
| `contact_group_members` table exists | ✅ | Has `group_id`, `member_type`, `member_id` |
| `member_type` = "contact" or "sponsored_agent" | ✅ | Verified in schema |
| RLS on both tables | ✅ | Policies exist |
| CASCADE delete on `group_id` | 🔍 | Need to verify FK constraint |

### 1.3 Schedule Recipients

| Requirement | Status | Notes |
|-------------|--------|-------|
| Typed recipients JSON | ✅ | `{"type": "contact", "id": "..."}` etc |
| Worker resolves `type: "group"` | ✅ | Implemented in worker |

---

## 2. BACKEND API

### 2.1 Contacts API

| Endpoint | Status | Issues |
|----------|--------|--------|
| `GET /v1/contacts` returns `groups[]` | ✅ | Phase 2 backend added LEFT JOIN |
| `POST /v1/contacts` type validation | 🟡 | **VERIFY**: Group validation logic |
| `PATCH /v1/contacts/{id}` | ✅ | Exists with ownership check |
| `DELETE /v1/contacts/{id}` | ✅ | Exists |
| `POST /v1/contacts/import` | ✅ | CSV import with group support |

**ACTION NEEDED**: Verify `POST /v1/contacts` validation for type="group"

### 2.2 Groups API

| Endpoint | Status | Issues |
|----------|--------|--------|
| `GET /v1/contact-groups` | ✅ | Returns groups with `member_count` |
| `POST /v1/contact-groups` | ✅ | Creates empty groups |
| `GET /v1/contact-groups/{id}` | ✅ | Returns members with names/emails |
| `POST /v1/contact-groups/{id}/members` | ✅ | Adds members with validation |
| `DELETE /v1/contact-groups/{id}/members` | ✅ | Removes members |

### 2.3 Affiliate Control

| Endpoint | Status | Issues |
|----------|--------|--------|
| `GET /v1/affiliate/overview` with `groups[]` | ✅ | Phase 2 backend added |
| `POST /v1/affiliate/accounts/{id}/unsponsor` | ✅ | Phase 3 backend added |

---

## 3. FRONTEND UX

### 3.1 Top Summary Cards

| Requirement | Status | Issues |
|-------------|--------|--------|
| Count cards for Contacts, Agents, Groups | ❌ | **MISSING** - No count cards shown |

**ACTION NEEDED**: Add count cards above People table

### 3.2 Tabs

| Requirement | Status | Issues |
|-------------|--------|--------|
| "People" and "Groups" tabs | ✅ | Exists in current UI |

### 3.3 People Tab - Table

| Requirement | Status | Issues |
|-------------|--------|--------|
| Checkbox column for row selection | ✅ | Phase 2 added |
| Name, Email, Type, Groups columns | ✅ | All present |
| Groups rendered as chips/badges | ✅ | Phase 2 added |
| Search bar (name/email) | ✅ | Phase 2 added |
| Filter dropdown (All/Agents/Groups/etc) | ✅ | Phase 2 added |

### 3.4 Add Contact Modal - TYPE-FIRST

| Requirement | Status | Issues |
|-------------|--------|--------|
| Type field FIRST | ✅ | Phase 1 refactored to type-first |
| Conditional fields based on type | ✅ | Phase 1 implemented |
| Group: Name + Notes only | ✅ | Email/Phone hidden |
| Agent: Name, Email, Phone, Notes | ✅ | All shown + validation |
| Submit only relevant fields | 🟡 | **VERIFY**: Backend receives correct fields |

**ACTION NEEDED**: Test that Group contacts can be created without email

### 3.5 Edit Contact Modal

| Requirement | Status | Issues |
|-------------|--------|--------|
| Edit button on contact rows | ✅ | Phase 1 added |
| Opens with existing values | ✅ | Implemented |
| Conditional fields by type | 🟡 | **VERIFY**: Edit modal respects type |
| PATCH on submit | ✅ | Phase 1 implemented |

**ACTION NEEDED**: Verify edit modal shows correct fields per type

### 3.6 Managing Group Membership (From People Tab)

| Requirement | Status | Issues |
|-------------|--------|--------|
| "Add to Group" action on rows | ✅ | Exists |
| Opens modal with group list | ✅ | Implemented |
| Can multi-select groups | ✅ | Checkboxes shown |
| Calls POST for each selected | ✅ | Implemented |
| Optional "Manage Groups" view | ❌ | **MISSING** - Can't view/remove memberships from contact side |

**ACTION NEEDED**: Add "Manage Groups" action to see and remove memberships

### 3.7 Groups Tab - Managing Groups

| Requirement | Status | Issues |
|-------------|--------|--------|
| "New Group" button | ✅ | Exists |
| Creates empty group (no members) | ✅ | Spec says no members required |
| "View / Manage" action per group | ❌ | **MISSING** - No actions column on Groups tab |
| Group detail view with members list | ❌ | **MISSING** - Can't view group members |
| "Add Members" button in detail view | ❌ | **MISSING** - Can't add from group side |
| "Remove" button per member | ❌ | **MISSING** - Can't remove from group side |

**CRITICAL ISSUE**: Groups tab is **read-only**. Can't manage members from group side.

### 3.8 Sponsored Agent Edit/Unsponsor

| Requirement | Status | Issues |
|-------------|--------|--------|
| Edit button on sponsored agent rows | ✅ | Phase 3 added |
| Modal with name (readonly), email | ✅ | Implemented |
| Toggle "Sponsored by your account" | ✅ | Phase 3 added |
| Calls unsponsor endpoint | ✅ | Phase 3 implemented |
| Agent disappears after unsponsor | 🔍 | **NEEDS TEST** |

---

## 4. SCHEDULES INTEGRATION

| Requirement | Status | Issues |
|-------------|--------|--------|
| Can select People as recipients | ✅ | Exists |
| Can select Groups | ✅ | Groups section in wizard |
| Does NOT create/edit groups/contacts | ✅ | Correct behavior |
| Worker resolves typed recipients | ✅ | Implemented |

---

## 5. QA CHECKLIST STATUS

### ✅ Contacts API
- [x] GET /v1/contacts returns groups array
- [⚠️] POST /v1/contacts enforces type-specific validation (needs verification)
- [x] PATCH /v1/contacts/{id} works
- [x] POST /v1/contacts/import works

### ✅ Groups API
- [x] GET /v1/contact-groups returns name + member_count
- [x] POST /v1/contact-groups can create empty groups
- [x] GET /v1/contact-groups/{id} returns members
- [x] POST/DELETE members endpoints work

### ❌ People UI – Top Cards
- [ ] **MISSING**: Count cards not shown

### 🟡 People UI – Table
- [x] Groups column with tags
- [x] Search bar
- [x] Filter dropdown
- [x] Row checkboxes
- [⚠️] **VERIFY**: All filters work correctly

### 🟡 Add Contact Modal
- [x] Type first
- [x] Conditional fields
- [⚠️] **VERIFY**: Backend validation works for each type

### 🟡 Edit Contact Modal
- [x] Opens with existing values
- [x] PATCH works
- [⚠️] **VERIFY**: Conditional fields in edit mode

### ❌ Groups Tab
- [x] Lists groups with member counts
- [x] Can create empty group
- [ ] **MISSING**: Can't manage members from group side
- [ ] **MISSING**: No "View/Manage" action
- [ ] **MISSING**: No "Add Members" from group detail
- [ ] **MISSING**: No "Remove" member action

### 🟡 Sponsored Agents (Affiliate)
- [x] Appear on People tab
- [x] Edit/Unsponsor modal exists
- [⚠️] **NEEDS TEST**: Unsponsored agent behavior

---

## 6. CRITICAL GAPS TO FIX

### Priority 1: Groups Tab is Read-Only
**Problem**: Can't manage group members from the Groups side. The spec says:
> "View / Manage: Opens detail view with members list and Add Members / Remove buttons"

**Current**: Groups tab just lists groups. No actions column.

**Fix Required**:
1. Add "Actions" column to Groups tab
2. Add "View/Manage" button per group row
3. Create group detail dialog/page showing:
   - Group name + description (editable?)
   - Members list table
   - "Add Members" button (opens picker)
   - "Remove" button per member
4. Wire up POST/DELETE member endpoints

### Priority 2: Top Count Cards Missing
**Problem**: Spec requires count cards at top of People page.

**Fix Required**:
1. Add 3-4 cards above the tabs showing:
   - Total Contacts count
   - Agents count (type="agent")
   - Groups count (type="group" or contact_groups count)
   - Sponsored Agents count (for affiliates only)
2. Cards should update when data changes

### Priority 3: "Manage Groups" Per Contact
**Problem**: Can add contact to groups, but can't see which groups they're in or remove them.

**Fix Required**:
1. Add "Manage Groups" action to contact rows
2. Opens modal showing current group memberships
3. Show "Remove from Group" button per membership
4. Call DELETE /v1/contact-groups/{id}/members

---

## 7. VERIFICATION NEEDED

These exist in code but need functional testing:

1. **Group contact creation**: Create a contact with type="group", no email. Should work.
2. **Edit modal conditional fields**: Edit a group contact. Should NOT show email/phone.
3. **Unsponsor behavior**: Unsponsor an agent. Verify they disappear from People list.
4. **Filter "Groups"**: Click filter dropdown → "Groups". Should show only type="group" contacts.
5. **CSV import with groups**: Upload CSV with `group` column. Verify groups created and contacts added.

---

## 8. FIX PLAN - CONCRETE STEPS

### Step 1: Add Top Count Cards
**File**: `apps/web/app/app/people/page.tsx`

Add above the tabs:
```tsx
<div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
  <Card>
    <CardContent className="pt-6">
      <div className="text-2xl font-bold">{contacts.length}</div>
      <p className="text-sm text-muted-foreground">Total Contacts</p>
    </CardContent>
  </Card>
  {/* ... more cards */}
</div>
```

### Step 2: Add Groups Tab Actions
**File**: `apps/web/app/app/people/page.tsx`

In Groups tab:
1. Add "Actions" column to groups table
2. Add "View/Manage" button per row
3. Create `GroupDetailDialog` component
4. Show members list with "Remove" buttons
5. Add "Add Members" button that opens picker

### Step 3: Add "Manage Groups" Per Contact
**File**: `apps/web/app/app/people/page.tsx`

In People tab:
1. Add "Manage Groups" to actions dropdown/menu
2. Create `ManageGroupsDialog` component
3. Show current memberships from `person.groups`
4. Add "Remove from Group" button per membership
5. Call DELETE endpoint on remove

### Step 4: Verification Testing
Run through QA checklist:
1. Test group contact creation (no email)
2. Test edit modal for different types
3. Test unsponsor flow
4. Test all filters
5. Test CSV import with groups

---

## 9. WHEN IS PEOPLE "DONE"?

People is done when:

✅ All 8 QA checklist items from section 5 are green  
✅ All Priority 1-3 gaps are fixed  
✅ All verification tests pass  

**Then**: Stop touching People. Move to Billing.

---

## READY FOR IMPLEMENTATION

This audit document provides:
- ✅ Current status of every requirement
- ✅ Specific gaps identified
- ✅ Concrete fix steps
- ✅ Definition of "done"

**Next**: Execute fix plan, starting with Priority 1 (Groups Tab management).

