# Cursor Prompt: Fix Schedule Recipients (The Only Showstopper)

## The Bug

`apps/web/components/unified-wizard/index.tsx` line ~183 in `handleSubmit()`:
```ts
recipients: [],
```

Every schedule is created with zero recipients. The backend `ScheduleCreate` schema 
in `schedules.py` requires `min_items=1`:
```python
recipients: List[Union[RecipientInput, EmailStr]] = Field(..., min_items=1)
```

This means schedule creation either fails silently (422 swallowed by try/catch) 
or creates a schedule that never sends to anyone.

## The Fix

A working recipients component ALREADY EXISTS:
`apps/web/components/schedule-builder/sections/recipients-section.tsx`

It fetches contacts from `GET /api/proxy/v1/contacts` and groups from 
`GET /api/proxy/v1/contact-groups`. It renders search, contact/group toggles, 
selected pills with remove buttons. It returns `Recipient[]` objects.

The unified wizard's `WizardState` in `types.ts` already has:
```ts
recipients: Recipient[]
```

And `INITIAL_STATE` already initializes it to `[]`.

The `Recipient` type is already defined:
```ts
export type Recipient =
  | { type: "contact"; id: string; name: string; email: string }
  | { type: "group"; id: string; name: string; memberCount: number }
  | { type: "manual_email"; email: string }
```

### Step 1: Wire RecipientsSection into StepDeliver

In `apps/web/components/unified-wizard/step-deliver.tsx`, find the 
`ScheduleOptions` component. Replace the placeholder div:

```tsx
{/* Recipients placeholder — future: contact/group search */}
<div className="rounded-lg border border-dashed border-gray-300 p-3 text-center text-xs text-gray-400">
  Recipient search (contacts &amp; groups) coming soon.
</div>
```

Replace with the actual recipients section. You can either:

**Option A (import existing):** Import `RecipientsSection` from the old schedule builder:
```tsx
import { RecipientsSection } from "@/components/schedule-builder/sections/recipients-section"
```

Then render it:
```tsx
<RecipientsSection
  recipients={state.recipients}
  onChange={(patch) => onChange(patch as Partial<WizardState>)}
  hasRecipients={state.recipients.length > 0}
/>
```

**Option B (copy inline):** If there's a type mismatch between the old 
`ScheduleBuilderState` and the unified `WizardState`, copy the recipients 
UI code directly into `ScheduleOptions`. The key logic is:
- On mount, fetch contacts from `/api/proxy/v1/contacts` and groups from `/api/proxy/v1/contact-groups`
- Show a search input that filters contacts by name/email
- Show groups as toggleable items with member count
- Show selected recipients as pills with X buttons
- Store selections in `state.recipients` via `onChange({ recipients: [...] })`

### Step 2: Pass recipients in handleSubmit

In `index.tsx` `handleSubmit()`, replace:
```ts
recipients: [],
```

With:
```ts
recipients: state.recipients.map(r => {
  if (r.type === "manual_email") return r.email;
  if (r.type === "contact") return { type: "contact", id: r.id, email: r.email };
  if (r.type === "group") return { type: "group", id: r.id };
  return r;
}),
```

**CHECK FIRST:** Read `RecipientInput` in `schedules.py` to see the exact 
format the backend expects. Match it. The above is a guess — the backend 
might expect plain email strings, or typed objects, or a mix.

### Step 3: Require at least one recipient for schedule mode

In `index.tsx`, update the `canContinue` check for step 3:

```ts
// BEFORE:
case 3: return state.deliveryMode === "send_now"
  ? (state.viewInBrowser || state.downloadPdf || state.sendViaEmail)
  : !!state.scheduleName.trim()

// AFTER:
case 3: return state.deliveryMode === "send_now"
  ? (state.viewInBrowser || state.downloadPdf || state.sendViaEmail)
  : !!state.scheduleName.trim() && state.recipients.length > 0
```

This prevents the "Create Schedule" button from being active until 
at least one recipient is added.

### Step 4: Also clean up cadence (quick win)

In `step-deliver.tsx` `ScheduleOptions`, the frequency grid shows 4 options 
including biweekly and quarterly. The backend only accepts `weekly | monthly`:

```python
cadence: str = Field(..., pattern="^(weekly|monthly)$")
```

Remove the options the backend can't store:

```tsx
// BEFORE:
{(["weekly", "biweekly", "monthly", "quarterly"] as Cadence[]).map((c) => (

// AFTER:
{(["weekly", "monthly"] as Cadence[]).map((c) => (
```

Change `grid-cols-4` to `grid-cols-2` on that container.

In `index.tsx` `handleSubmit()`, remove the cadenceMap and send directly:
```ts
// BEFORE:
const cadenceMap: Record<string, string> = {
  weekly: "weekly",
  biweekly: "weekly",
  monthly: "monthly",
  quarterly: "monthly",
}
// ...
cadence: cadenceMap[state.cadence] || "weekly",

// AFTER:
cadence: state.cadence,
```

## Testing

1. Go to `/app/schedules/new`
2. Pick a story → pick area → go to Deliver step
3. Verify: Schedule mode shows recipient search (not "coming soon" placeholder)
4. Search for a contact → add them → verify pill appears
5. Add a second recipient (group or manual email)
6. Verify: "Create Schedule" button is disabled until name + recipients are filled
7. Submit → verify no errors
8. Go to `/app/schedules` → verify the new schedule shows recipients
9. Verify: cadence only shows Weekly and Monthly (no biweekly/quarterly)
