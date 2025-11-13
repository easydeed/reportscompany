# Task 5: Schedules UI QA & Behavior Fixes

**Estimated Time:** 45 minutes  
**Priority:** MEDIUM  
**Dependencies:** Task 4 (routing must work first)

---

## 🎯 Goal

Ensure Schedules UI works end-to-end with no behavior bugs. Focus on **functionality only** - no design changes.

---

## 📋 Scope

### In Scope (Fix These)
- ✅ UI → API → DB data flow
- ✅ Form validation
- ✅ API error handling
- ✅ Data binding and display
- ✅ Navigation and routing

### Out of Scope (Don't Touch)
- ❌ Colors, spacing, fonts
- ❌ Component architecture
- ❌ CSS or Tailwind changes
- ❌ Layout redesigns

---

## 📂 Pages to QA

### 1. Schedules List (`/app/schedules/page.tsx`)

**Features to test:**
1. List loads without crashing
2. Shows schedules from database
3. "New Schedule" button navigates to `/app/schedules/new`
4. Each schedule row shows: name, report type, city/zips, cadence, next run, status
5. Click row/button navigates to detail page

**Required fixes:**

**Load schedules from API:**
```typescript
'use client';
import { useEffect, useState } from 'react';

export default function SchedulesPage() {
  const [schedules, setSchedules] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  useEffect(() => {
    fetch('/api/proxy/v1/schedules')
      .then(res => {
        if (!res.ok) throw new Error('Failed to fetch schedules');
        return res.json();
      })
      .then(data => {
        setSchedules(data.schedules || []);
        setLoading(false);
      })
      .catch(err => {
        setError(err.message);
        setLoading(false);
      });
  }, []);
  
  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;
  
  return (
    <div className="p-8">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Schedules</h1>
        <a 
          href="/app/schedules/new"
          className="px-4 py-2 bg-violet-600 text-white rounded-lg"
        >
          New Schedule
        </a>
      </div>
      
      {schedules.length === 0 ? (
        <p>No schedules yet. Create your first one!</p>
      ) : (
        <div className="space-y-4">
          {schedules.map(schedule => (
            <div key={schedule.id} className="border p-4 rounded-lg">
              <a href={`/app/schedules/${schedule.id}`}>
                <h3 className="font-semibold">{schedule.name}</h3>
                <p>{schedule.city || schedule.zip_codes?.join(', ')}</p>
                <p>Next run: {schedule.next_run_at}</p>
              </a>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
```

**Check:**
- [ ] API endpoint `/api/proxy/v1/schedules` exists
- [ ] Data displays correctly
- [ ] Links work

---

### 2. New Schedule Form (`/app/schedules/new/page.tsx`)

**Features to test:**
1. All form fields render
2. Validation works (required fields, email format)
3. Submit calls API correctly
4. Success redirects to list or detail page
5. Errors displayed to user

**Required fields:**
- Name
- Report type (dropdown: market_snapshot, new_listings, etc.)
- City OR zip codes
- Lookback days (number, default 30)
- Cadence (radio: weekly/monthly)
- Weekly day (if weekly) OR monthly date (if monthly)
- Send time (hour:minute)
- Recipients (email list, comma-separated)

**Validation rules:**
```typescript
function validateSchedule(data) {
  const errors = [];
  
  if (!data.name?.trim()) {
    errors.push('Name is required');
  }
  
  if (!data.report_type) {
    errors.push('Report type is required');
  }
  
  if (!data.city?.trim() && (!data.zip_codes || data.zip_codes.length === 0)) {
    errors.push('City or ZIP codes required');
  }
  
  if (!data.cadence || !['weekly', 'monthly'].includes(data.cadence)) {
    errors.push('Cadence must be weekly or monthly');
  }
  
  if (data.cadence === 'weekly' && (data.weekly_dow < 0 || data.weekly_dow > 6)) {
    errors.push('Weekly day must be 0-6 (Sun-Sat)');
  }
  
  if (data.cadence === 'monthly' && (data.monthly_dom < 1 || data.monthly_dom > 28)) {
    errors.push('Monthly day must be 1-28');
  }
  
  if (!data.recipients || data.recipients.length === 0) {
    errors.push('At least one recipient required');
  }
  
  // Validate emails
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  const invalidEmails = data.recipients.filter(email => !emailRegex.test(email));
  if (invalidEmails.length > 0) {
    errors.push(`Invalid emails: ${invalidEmails.join(', ')}`);
  }
  
  return errors;
}
```

**API call pattern:**
```typescript
async function createSchedule(data) {
  const response = await fetch('/api/proxy/v1/schedules', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      name: data.name,
      report_type: data.report_type,
      city: data.city || null,
      zip_codes: data.zip_codes || null,
      lookback_days: parseInt(data.lookback_days) || 30,
      cadence: data.cadence,
      weekly_dow: data.cadence === 'weekly' ? data.weekly_dow : null,
      monthly_dom: data.cadence === 'monthly' ? data.monthly_dom : null,
      send_hour: parseInt(data.send_hour) || 9,
      send_minute: parseInt(data.send_minute) || 0,
      recipients: data.recipients,
      active: true,
    }),
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to create schedule');
  }
  
  return response.json();
}
```

**Check:**
- [ ] All fields render correctly
- [ ] Validation prevents invalid submission
- [ ] Errors shown to user
- [ ] Success creates schedule in DB
- [ ] Redirects after success

---

### 3. Schedule Detail (`/app/schedules/[id]/page.tsx`)

**Features to test:**
1. Loads schedule metadata
2. Shows run history (schedule_runs table)
3. Pause/Resume toggle works
4. Edit button navigates to edit form
5. Delete button works (with confirmation)

**Metadata to display:**
- Name
- Report type
- City/ZIP codes
- Cadence (weekly/monthly with details)
- Send time
- Recipients
- Active status
- Next run time

**Run history table:**
```typescript
async function fetchScheduleRuns(scheduleId) {
  const response = await fetch(`/api/proxy/v1/schedules/${scheduleId}/runs`);
  if (!response.ok) throw new Error('Failed to fetch runs');
  return response.json();
}

// Display in table
<table>
  <thead>
    <tr>
      <th>Status</th>
      <th>Started</th>
      <th>Finished</th>
      <th>Report</th>
    </tr>
  </thead>
  <tbody>
    {runs.map(run => (
      <tr key={run.id}>
        <td>{run.status}</td>
        <td>{new Date(run.started_at).toLocaleString()}</td>
        <td>{run.finished_at ? new Date(run.finished_at).toLocaleString() : '-'}</td>
        <td>
          {run.report_run_id && (
            <a href={`/print/${run.report_run_id}`}>View PDF</a>
          )}
        </td>
      </tr>
    ))}
  </tbody>
</table>
```

**Pause/Resume toggle:**
```typescript
async function toggleActive(scheduleId, currentActive) {
  const response = await fetch(`/api/proxy/v1/schedules/${scheduleId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ active: !currentActive }),
  });
  
  if (!response.ok) throw new Error('Failed to update schedule');
  return response.json();
}
```

**Check:**
- [ ] Schedule metadata loads correctly
- [ ] Run history displays (sorted by created_at DESC)
- [ ] Toggle active status works
- [ ] Links to report PDFs work
- [ ] Delete confirmation prevents accidental deletion

---

## 🐛 Common Bugs to Fix

### Bug 1: API Proxy Missing

If `/api/proxy/v1/schedules` doesn't exist:

**Create:** `apps/web/app/api/proxy/v1/schedules/route.ts`

```typescript
import { NextRequest, NextResponse } from 'next/server';

export async function GET(request: NextRequest) {
  const apiBase = process.env.NEXT_PUBLIC_API_BASE;
  const token = request.cookies.get('auth_token')?.value;
  
  const response = await fetch(`${apiBase}/v1/schedules`, {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });
  
  const data = await response.json();
  return NextResponse.json(data);
}

export async function POST(request: NextRequest) {
  const apiBase = process.env.NEXT_PUBLIC_API_BASE;
  const token = request.cookies.get('auth_token')?.value;
  const body = await request.json();
  
  const response = await fetch(`${apiBase}/v1/schedules`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(body),
  });
  
  const data = await response.json();
  return NextResponse.json(data, { status: response.status });
}
```

### Bug 2: Email Recipients Not Array

If recipients input is comma-separated string:

```typescript
// In form submission
const recipientsArray = recipientsInput
  .split(',')
  .map(email => email.trim())
  .filter(email => email.length > 0);
```

### Bug 3: Weekly DOW vs Monday=0/Sunday=0

**Database:** Sunday=0, Monday=1, ..., Saturday=6  
**UI:** Show user-friendly labels

```typescript
const DAYS_OF_WEEK = [
  { value: 0, label: 'Sunday' },
  { value: 1, label: 'Monday' },
  { value: 2, label: 'Tuesday' },
  { value: 3, label: 'Wednesday' },
  { value: 4, label: 'Thursday' },
  { value: 5, label: 'Friday' },
  { value: 6, label: 'Saturday' },
];
```

### Bug 4: Next Run Time Not Calculated

When creating schedule, `next_run_at` should be NULL (ticker calculates on first pickup) or calculated client-side.

**Best approach:** Let backend/ticker calculate, send `null` from UI.

### Bug 5: Run History Unsorted

```typescript
// In API or UI, sort by created_at DESC
const sortedRuns = runs.sort((a, b) => 
  new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
);
```

---

## ✅ Acceptance Criteria

### List Page
- [ ] Loads schedules from API
- [ ] Shows all schedules for current account
- [ ] "New Schedule" button works
- [ ] Clicking schedule navigates to detail page
- [ ] No console errors

### Create Page
- [ ] All fields render correctly
- [ ] Validation prevents invalid data
- [ ] Email validation works
- [ ] Successful creation redirects
- [ ] Created schedule appears in database
- [ ] Form matches API schema exactly

### Detail Page
- [ ] Loads schedule metadata correctly
- [ ] Shows run history (if any)
- [ ] Pause/Resume toggle persists to DB
- [ ] Links to PDF reports work
- [ ] Delete works (with confirmation)

### End-to-End
- [ ] Create schedule via UI → appears in list
- [ ] Wait 60 seconds → ticker processes it
- [ ] Email arrives with correct data
- [ ] Run appears in detail page history

---

## 🧪 Testing Checklist

### Test 1: List Page
```bash
1. Visit /app/schedules
2. Verify schedules load (or "no schedules" message)
3. Click "New Schedule" → goes to /app/schedules/new
4. Click schedule → goes to /app/schedules/[id]
```

### Test 2: Create Schedule
```bash
1. Visit /app/schedules/new
2. Fill out form:
   - Name: "Test Schedule"
   - Type: "market_snapshot"
   - City: "Houston"
   - Lookback: 30
   - Cadence: Weekly, Monday
   - Time: 14:00
   - Recipients: gerardoh@gmail.com
3. Submit
4. Check DB: new row in schedules table
5. Verify redirect to list or detail
```

### Test 3: Detail Page
```bash
1. Visit /app/schedules/[id] (use existing schedule)
2. Verify metadata displays correctly
3. Check run history table
4. Toggle active → check DB updated
5. Click PDF link → opens correct report
```

### Test 4: End-to-End
```bash
1. Create schedule for "Houston" via UI
2. Wait 60-90 seconds
3. Check worker logs → processed
4. Check email → arrives
5. Check detail page → run appears in history
```

---

## 📝 Commit Message

```
fix(web): schedules UI behavior and API integration

- Add API proxy routes for schedules CRUD
- Implement form validation (emails, required fields)
- Fix data binding (weekly_dow, recipients array)
- Add error handling and loading states
- Sort run history by created_at DESC
- Fix pause/resume toggle persistence

Issue: Schedules UI not wired to backend
Fix: Complete UI → API → DB integration
```

---

**After completing this task, perform end-to-end test: create schedule via UI and verify email arrives.**

