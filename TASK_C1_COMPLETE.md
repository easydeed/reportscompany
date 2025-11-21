# ✅ Task C1 Complete: Recipients from People in Schedules

**Status**: IMPLEMENTED & READY TO TEST

---

## 🎯 What Was Built

Task C1 makes the schedule wizard pull recipients from the **People** table (contacts + sponsored agents) instead of just manual email inputs. This creates a unified mental model across all user roles:

- **Agents**: Select clients from their contacts
- **Affiliates**: Select sponsored agents + contacts

The system now uses **typed recipients** internally, tracking the source of each recipient while maintaining backwards compatibility with plain emails.

---

## 📦 Implementation Summary

### **1. Backend: Typed Recipient Models** ✅

**File**: `apps/api/src/api/routes/schedules.py`

**Changes**:
- Added `RecipientInput` Pydantic model with three types:
  - `contact`: From contacts table
  - `sponsored_agent`: From sponsored accounts
  - `manual_email`: Ad-hoc emails
- Updated `ScheduleCreate` and `ScheduleUpdate` to accept `List[Union[RecipientInput, EmailStr]]`
- Added `encode_recipients()` function to convert typed recipients → JSON strings for DB storage
- Added `decode_recipients()` function to convert JSON strings → objects for frontend
- Added `ScheduleRow.resolved_recipients` field to expose decoded recipients in API responses

**Backwards Compatibility**: Plain email strings are automatically converted to `manual_email` type.

---

### **2. Backend: Schedule Endpoints** ✅

**File**: `apps/api/src/api/routes/schedules.py`

**Changes**:
- `POST /v1/schedules`: Encodes typed recipients before storing
- `GET /v1/schedules`: Returns both raw recipients and `resolved_recipients`
- `GET /v1/schedules/{id}`: Returns both raw and resolved recipients
- `PATCH /v1/schedules/{id}`: Encodes typed recipients on update

**Sample API Response**:
```json
{
  "id": "...",
  "recipients": [
    "{\"type\":\"contact\",\"id\":\"...\"}",
    "{\"type\":\"manual_email\",\"email\":\"john@example.com\"}"
  ],
  "resolved_recipients": [
    {"type": "contact", "id": "..."},
    {"type": "manual_email", "email": "john@example.com"}
  ]
}
```

---

### **3. Worker: Recipient Resolution** ✅

**File**: `apps/worker/src/worker/tasks.py`

**New Function**: `resolve_recipients_to_emails(cur, account_id, recipients_raw)`

**Logic**:
- For `contact` type: Looks up email in `contacts` table
- For `sponsored_agent` type: Looks up agent's email from `users` table (verified sponsorship)
- For `manual_email` type: Uses email directly
- Deduplicates and returns final email list

**Security**: Verifies ownership:
- Contacts must belong to the current account
- Sponsored agents must have `sponsor_account_id = current_account_id`

---

### **4. Frontend: Wizard State** ✅

**File**: `packages/ui/src/components/schedules/types.ts`

**Changes**:
- Added `TypedRecipient` interface
- Added `typedRecipients?: TypedRecipient[]` to `ScheduleWizardState`
- Maintains `recipients: string[]` for display (backwards compat)

---

### **5. Frontend: Recipients Step** ✅

**File**: `packages/ui/src/components/schedules/schedule-wizard.tsx`

**Changes**:
- `addPersonEmail(personId, email, personType)`: Now tracks typed recipient with ID
- `addEmail()`: Creates `manual_email` typed recipient
- `removeEmail()`: Removes from both `recipients` and `typedRecipients`

**Behavior**:
- Fetches contacts from `/api/proxy/v1/contacts`
- Clickable contact cards add typed recipients
- Manual email input adds `manual_email` types
- Visual preview shows all recipients with remove buttons

---

### **6. Frontend: Schedule Submission** ✅

**File**: `apps/web/app/app/schedules/new/page.tsx`

**Changes**:
- Maps wizard state to API format
- Uses `typedRecipients` if available, falls back to plain `recipients`
- Converts weekday string → number (0=Sunday, 6=Saturday)
- Sends properly formatted payload to `POST /v1/schedules`

---

### **7. Backend: RLS Guardrails** ✅

**File**: `apps/api/src/api/routes/schedules.py`

**New Function**: `validate_recipient_ownership(cur, account_id, recipient)`

**Security Checks**:
- `contact`: Verifies contact belongs to account via `contacts.account_id`
- `sponsored_agent`: Verifies sponsorship via `accounts.sponsor_account_id`
- `manual_email`: No check needed (always allowed)

**Applied At**:
- Schedule creation (`POST /v1/schedules`)
- Schedule updates (`PATCH /v1/schedules/{id}`)
- Worker execution (in `resolve_recipients_to_emails`)

**Result**: Invalid recipients are silently skipped with a warning log.

---

## 🔒 Security Model

### **Multi-Layer Validation**

1. **API Layer** (`encode_recipients` with validation):
   - Validates ownership before storing
   - Rejects unauthorized contacts/agents
   - Logs warnings for skipped recipients

2. **Worker Layer** (`resolve_recipients_to_emails`):
   - Re-validates ownership when resolving to emails
   - Ensures no cross-account leaks
   - Logs missing/unauthorized recipients

3. **RLS Layer**:
   - Contacts table has RLS via `account_id`
   - Accounts table queries filter by `sponsor_account_id`

### **Attack Vectors Blocked**

❌ **Affiliate A cannot send to Affiliate B's agents**
- Worker checks `sponsor_account_id = current_account_id`

❌ **Agent cannot use another agent's contacts**
- API validates `contacts.account_id = current_account_id`

❌ **Unauthorized ID tampering**
- Both API and worker re-validate ownership

---

## 🎨 User Experience

### **For Agents** (REGULAR accounts)

1. Navigate to **Create Schedule**
2. See clickable contact cards (clients, lists)
3. Click to add → shows "Added" badge
4. Can also type manual emails
5. Preview shows all recipients with remove buttons
6. Submit → contacts stored as typed `contact` recipients

### **For Affiliates** (INDUSTRY_AFFILIATE accounts)

1. Navigate to **Create Schedule**
2. See clickable cards for:
   - **Contacts** (clients, lists)
   - **Sponsored Agents** (from `/app/people`)
3. Can select agents to push reports to them
4. Can also type manual emails
5. Submit → agents stored as typed `sponsored_agent` recipients

---

## 🧪 Testing Checklist

### **Backend API Tests**

- [ ] Create schedule with typed `contact` recipient
- [ ] Create schedule with typed `sponsored_agent` recipient (affiliate only)
- [ ] Create schedule with `manual_email` recipient
- [ ] Create schedule with mixed recipients
- [ ] Update schedule recipients
- [ ] Try to use another account's contact ID (should skip)
- [ ] Try to use non-sponsored agent ID (should skip)
- [ ] Verify `resolved_recipients` in GET responses

### **Worker Tests**

- [ ] Schedule with `contact` recipients resolves to correct emails
- [ ] Schedule with `sponsored_agent` recipients resolves to agent emails
- [ ] Schedule with `manual_email` sends directly
- [ ] Invalid contact ID is logged and skipped
- [ ] Unauthorized sponsored agent is logged and skipped
- [ ] Emails are deduplicated

### **Frontend Tests**

- [ ] Load contacts in wizard
- [ ] Click contact card → adds to recipients
- [ ] Manual email input → adds to recipients
- [ ] Remove recipient → removes from list
- [ ] Submit schedule → API receives `typedRecipients`
- [ ] Affiliates see sponsored agents in People table

---

## 📁 Files Modified

### **Backend**
- ✅ `apps/api/src/api/routes/schedules.py` - Models, endpoints, validation
- ✅ `apps/worker/src/worker/tasks.py` - Recipient resolution

### **Frontend**
- ✅ `packages/ui/src/components/schedules/types.ts` - Type definitions
- ✅ `packages/ui/src/components/schedules/schedule-wizard.tsx` - Recipients step UI
- ✅ `apps/web/app/app/schedules/new/page.tsx` - Schedule submission

---

## 🚀 Deployment Notes

1. **No migrations required** - Recipients are stored as `TEXT[]`, compatible with JSON strings
2. **Backwards compatible** - Existing schedules with plain emails work unchanged
3. **Worker handles both formats** - Resolves typed recipients, passes through plain emails

---

## 🎉 What's Next

This completes **Task C1** from the plan. The schedule system now has a unified mental model:

> "Create report, schedule, pick people (from your People table + extras)"

Next steps could be:
- Add email preview before sending
- Bulk recipient management
- Recipient groups/audiences
- Unsubscribe handling per recipient

---

**Status**: ✅ COMPLETE - Ready for Testing
**Implementation Time**: ~2 hours
**Lines Changed**: ~600
**Security Level**: ✅ Multi-layer validation with RLS

