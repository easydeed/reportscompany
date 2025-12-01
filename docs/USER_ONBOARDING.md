# User Onboarding System

This document describes the comprehensive user onboarding system implementation.

## Overview

The onboarding system provides a seamless first-time user experience through:

1. **Setup Wizard** - Step-by-step modal for new users
2. **Onboarding Checklist** - Persistent progress tracker
3. **Empty States** - Contextual guidance when no data exists
4. **Welcome Email** - Automated email on registration

---

## Features

### 1. Setup Wizard

A multi-step modal that guides new users through initial setup:

| Step | Description |
|------|-------------|
| Welcome | Overview of what's coming |
| Profile | First name, last name, company, phone |
| Branding | Logo upload, primary color |
| Complete | Success message + CTA to create first report |

**Behavior:**
- Automatically shown on first visit (if no onboarding progress)
- Can be dismissed and will show checklist instead
- Saves progress at each step
- Skippable steps available

### 2. Onboarding Checklist

A card component showing onboarding progress:

**Regular Agent Steps:**
1. Complete your profile (required)
2. Set up branding (optional)
3. Generate first report (required)
4. Set up automated reports (optional)

**Industry Affiliate Steps:**
1. Complete your profile (required)
2. Set up white-label branding (required)
3. Invite your first agent (required)

**Features:**
- Auto-detects completed steps based on user activity
- Progress bar with percentage
- Links to relevant pages
- Dismissable (hides from dashboard)
- Three variants: `card`, `inline`, `minimal`

### 3. Empty State Components

Contextual guidance when users have no data:

| Variant | Use Case |
|---------|----------|
| `reports` | No reports page |
| `schedules` | No schedules page |
| `contacts` | No contacts page |
| `branding` | Branding not configured |
| `generic` | Default fallback |

### 4. Welcome Email

Automated email sent on registration:

- Branded HTML template
- Plain text fallback
- Getting started checklist
- CTA to login

---

## Files Created/Modified

### Database Migration

| File | Description |
|------|-------------|
| `db/migrations/0018_user_onboarding.sql` | Onboarding tracking tables |

**Schema Changes:**

```sql
-- New fields on users table
ALTER TABLE users ADD COLUMN onboarding_completed_at TIMESTAMP;
ALTER TABLE users ADD COLUMN onboarding_step VARCHAR(50);
ALTER TABLE users ADD COLUMN onboarding_data JSONB;

-- New table for step tracking
CREATE TABLE onboarding_progress (
    user_id UUID REFERENCES users(id),
    step_key VARCHAR(50),
    completed_at TIMESTAMP,
    skipped_at TIMESTAMP,
    metadata JSONB
);
```

### Backend API

| File | Description |
|------|-------------|
| `apps/api/src/api/routes/onboarding.py` | **NEW** - Onboarding endpoints |
| `apps/api/src/api/services/email.py` | **NEW** - Email service with Resend |
| `apps/api/src/api/settings.py` | Added email configuration |
| `apps/api/src/api/routes/auth.py` | Updated to send welcome email |
| `apps/api/src/api/main.py` | Registered onboarding router |

### Frontend Proxy Routes

| File | Description |
|------|-------------|
| `apps/web/app/api/proxy/v1/onboarding/route.ts` | GET onboarding status |
| `apps/web/app/api/proxy/v1/onboarding/complete-step/route.ts` | POST complete step |
| `apps/web/app/api/proxy/v1/onboarding/dismiss/route.ts` | POST dismiss |

### Frontend Components

| File | Description |
|------|-------------|
| `apps/web/components/onboarding/onboarding-checklist.tsx` | Checklist component |
| `apps/web/components/onboarding/setup-wizard.tsx` | Wizard modal |
| `apps/web/components/onboarding/empty-state.tsx` | Empty state components |
| `apps/web/components/onboarding/dashboard-onboarding.tsx` | Dashboard wrapper |
| `apps/web/components/onboarding/index.ts` | Export barrel |
| `apps/web/app/app/page.tsx` | Updated to include onboarding |

---

## API Endpoints

### GET /v1/onboarding

Get current user's onboarding status.

**Response:**
```json
{
  "user_id": "uuid",
  "is_complete": false,
  "is_dismissed": false,
  "current_step": "branding_setup",
  "progress_percent": 25,
  "completed_count": 1,
  "total_count": 4,
  "steps": [
    {
      "key": "profile_complete",
      "title": "Complete your profile",
      "description": "Add your name, company, and contact info",
      "href": "/app/account/settings",
      "icon": "user",
      "required": true,
      "completed": true,
      "skipped": false,
      "completed_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

### POST /v1/onboarding/complete-step

Mark a step as complete.

**Request:**
```json
{
  "step_key": "profile_complete",
  "metadata": { "source": "wizard" }
}
```

### POST /v1/onboarding/skip-step

Skip an optional step.

**Request:**
```json
{
  "step_key": "branding_setup"
}
```

### POST /v1/onboarding/dismiss

Hide onboarding checklist from dashboard.

### POST /v1/onboarding/reset

Reset onboarding progress (for testing).

---

## Auto-Detection

The system automatically detects completed steps:

| Step | Detection Criteria |
|------|-------------------|
| `profile_complete` | User has first_name AND last_name |
| `branding_setup` | Account has logo_url set |
| `first_report` | At least 1 completed report |
| `first_schedule` | At least 1 active schedule |
| `first_agent_invited` | At least 1 sponsored account (affiliates) |

---

## Configuration

### Environment Variables

Add to your `.env`:

```env
# Email Configuration (Resend)
RESEND_API_KEY=re_xxxxxxxxxxxxx
EMAIL_FROM_ADDRESS=Market Reports <noreply@yourdomain.com>
EMAIL_REPLY_TO=support@yourdomain.com
```

### Resend Setup

1. Create account at [resend.com](https://resend.com)
2. Verify your domain
3. Create API key
4. Add to environment variables

---

## Usage

### Dashboard Integration

The onboarding is automatically shown on the dashboard:

```tsx
import { DashboardOnboarding } from "@/components/onboarding"

// In your page component
<DashboardOnboarding />
```

### Checklist Variants

```tsx
import { OnboardingChecklist } from "@/components/onboarding"

// Full card (default)
<OnboardingChecklist variant="card" />

// Inline banner
<OnboardingChecklist variant="inline" />

// Minimal progress
<OnboardingChecklist variant="minimal" />
```

### Empty States

```tsx
import { EmptyState } from "@/components/onboarding"

// Reports empty state
<EmptyState variant="reports" />

// Custom content
<EmptyState
  variant="generic"
  title="No data yet"
  description="Get started by adding your first item."
  actionLabel="Add Item"
  actionHref="/add"
/>
```

---

## Deployment

1. **Run database migration:**
   ```bash
   psql $DATABASE_URL < db/migrations/0018_user_onboarding.sql
   ```

2. **Set environment variables:**
   ```bash
   RESEND_API_KEY=re_xxxxxxxxxxxxx
   EMAIL_FROM_ADDRESS="Market Reports <noreply@yourdomain.com>"
   EMAIL_REPLY_TO=support@yourdomain.com
   ```

3. **Deploy backend and frontend** as usual

---

## User Flow Diagram

```
┌─────────────────┐
│   Registration  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌─────────────────┐
│  Welcome Email  │────▶│   Login/App     │
└─────────────────┘     └────────┬────────┘
                                 │
                    ┌────────────┴────────────┐
                    │                         │
                    ▼                         ▼
           ┌───────────────┐        ┌───────────────┐
           │ First Visit?  │───No──▶│   Dashboard   │
           └───────┬───────┘        │ + Checklist   │
                   │                └───────────────┘
                  Yes
                   │
                   ▼
           ┌───────────────┐
           │ Setup Wizard  │
           │   (Modal)     │
           └───────┬───────┘
                   │
                   ▼
           ┌───────────────┐
           │   Complete    │
           │   Profile     │
           └───────┬───────┘
                   │
                   ▼
           ┌───────────────┐
           │    Setup      │
           │   Branding    │
           └───────┬───────┘
                   │
                   ▼
           ┌───────────────┐
           │   Create      │
           │ First Report  │
           └───────────────┘
```

---

## Testing Checklist

- [ ] New user sees setup wizard on first login
- [ ] Wizard saves profile data correctly
- [ ] Wizard saves branding data correctly
- [ ] Checklist shows on dashboard after wizard dismissed
- [ ] Steps auto-complete when criteria met
- [ ] Optional steps can be skipped
- [ ] Checklist can be dismissed
- [ ] Welcome email sent on registration
- [ ] Email contains correct login link
- [ ] Affiliate users see different onboarding steps
- [ ] Empty states show appropriate CTAs
- [ ] Progress percentage calculates correctly

---

## Related Documentation

- [ACCOUNT_SETTINGS.md](./ACCOUNT_SETTINGS.md) - Profile settings
- [AUTH_ARCHITECTURE_V1.md](./AUTH_ARCHITECTURE_V1.md) - Authentication
- [EMAIL_SYSTEM.md](./EMAIL_SYSTEM.md) - Email configuration (if exists)
