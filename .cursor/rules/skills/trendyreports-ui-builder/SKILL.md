---
name: trendyreports-ui-builder
description: Make frontend changes to the TrendyReports Next.js app — React components, pages, styling, wizard flows, sidebar navigation, dashboard UI, billing pages, branding pages, anything in apps/web/. Use this skill whenever a ticket involves modifying user-facing UI, adding React components, updating page layouts, changing Tailwind styles, working with shadcn/ui primitives, fixing React Query hooks, or any user-visible frontend work for TrendyReports. Trigger even when the ticket doesn't explicitly say "UI" — if files under apps/web/ are touched, this skill applies.
---

# TrendyReports UI Builder

You implement frontend changes for TrendyReports. Next.js 16 App Router, React 19, Tailwind v4, shadcn/ui, TanStack Query.

## Always Read First

1. `.cursor/rules/db-schema.md` — database schema reference
2. `../references/architecture.md` — system overview
3. `../references/forbidden.md` — what NEVER to change
4. `../references/conventions.md` — coding patterns

## Your Workflow

For every ticket:

1. **Read the ticket fully.** Identify the EXACT files to change. If unclear, ask before guessing.
2. **Grep before editing.** Find every instance of what you're changing. Don't change one and miss six.
3. **Read existing patterns.** Look at how similar components in `apps/web/components/` are structured. Match the style.
4. **Make the minimum change.** Don't refactor adjacent code unless the ticket asks for it.
5. **Verify the React Query implications.** If you touch a route under `/app/`, confirm `QueryProvider` is in scope.
6. **Check tier-aware rendering.** Pages may render differently for Admin / Company / Affiliate / Agent. Don't break a tier you didn't test.
7. **Do NOT commit or push.** Stage changes only. Let the user review before committing.

## Frontend Architecture Rules

### React Query (CRITICAL)

`QueryProvider` lives at `apps/web/app/app/layout.tsx` root. Every route under `/app/` inherits it.

- NEVER conditionally skip `QueryProvider` based on route type
- NEVER add a route to `BUILDER_ROUTES` without testing React Query still works
- `isBuilderRoute(pathname)` is exported from `app-layout.tsx` — use it for layout decisions

### After Mutations

Always invalidate React Query cache:

```typescript
queryClient.invalidateQueries({ queryKey: queryKeys.reports.list() })
```

Otherwise users see stale data after creating/updating/deleting.

### Sidebar (Tier-Aware)

`apps/web/app/app-layout.tsx` defines navigation per tier:
- Platform Admin (`isPlatformAdmin`) → admin nav
- Company Admin (`accountType === 'TITLE_COMPANY'`) → company nav
- Title Rep (`accountType === 'INDUSTRY_AFFILIATE'`) → rep nav with "MY BOOK" / "MY WORK" / "SETTINGS" sections
- Trial/Sponsored Agent (`sponsor_account_id` set) → agent nav
- Regular Agent → agent nav

When changing nav, check ALL tiers still work.

### Wizard / Builder Mode

`/app/reports/new`, `/app/property/new`, `/app/schedules/new`, `/app/schedules/{id}/edit` render in builder mode (no sidebar, full-bleed canvas).

The check: `isBuilderRoute(pathname)` returns true.

Builder routes still have `QueryProvider` because it's hoisted to layout root.

### Branding Rules

- An agent's reports use the agent's OWN branding ALWAYS — never falls back to sponsor's
- A title rep's reports use the rep's company branding (inherited from parent_account)
- Default brand colors for unbranded: `primary_color: "#4F46E5"`, `accent_color: "#1a1a1a"` (indigo + black)
- Default brand colors for PDF templates: `primary: "#18235c"`, `accent: "#0d9488"` (navy + teal)

### Plan-Aware UI

- Code uses `planSlug === 'starter'` and `planSlug === 'pro'` for conditionals — NEVER change these
- User-facing copy shows "Growth" (starter) and "Growth Plus" (pro) — change in display text only
- Prices: Free $0 / Growth $19 / Growth Plus $29 / Affiliate $99

## Component Patterns

### File Organization

| Pattern | Location |
|---------|----------|
| Page | `apps/web/app/{route}/page.tsx` |
| Layout | `apps/web/app/{route}/layout.tsx` |
| Domain components | `apps/web/components/{domain}/` |
| Shared | `apps/web/components/shared/` |
| UI primitives (shadcn) | `apps/web/components/ui/` |

### Imports

```typescript
// shadcn primitives
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"

// Lucide icons
import { ChevronRight, Settings } from "lucide-react"

// React Query hooks
import { useReports, useDeleteReport } from "@/hooks/use-api"

// Navigation
import Link from "next/link"
import { useRouter, usePathname } from "next/navigation"

// Toast
import { toast } from "sonner"
// OR: import { useToast } from "@/components/ui/use-toast"

// Utilities
import { cn } from "@/lib/utils"
```

### Patterns to Follow

**Button with confirmation:**

```typescript
<AlertDialog>
  <AlertDialogTrigger asChild>
    <Button variant="destructive">Delete</Button>
  </AlertDialogTrigger>
  <AlertDialogContent>
    <AlertDialogHeader>
      <AlertDialogTitle>Are you sure?</AlertDialogTitle>
      <AlertDialogDescription>This cannot be undone.</AlertDialogDescription>
    </AlertDialogHeader>
    <AlertDialogFooter>
      <AlertDialogCancel>Cancel</AlertDialogCancel>
      <AlertDialogAction onClick={handleDelete}>Delete</AlertDialogAction>
    </AlertDialogFooter>
  </AlertDialogContent>
</AlertDialog>
```

**Loading state:**

```typescript
const { data, isLoading, error } = useReports()

if (isLoading) return <PageSkeleton />
if (error) return <ErrorState message={error.message} />
if (!data) return <EmptyState />
```

**Form submission:**

```typescript
const { mutate, isPending } = useCreateReport()

const handleSubmit = () => {
  mutate(
    { report_type, city, lookback_days },
    {
      onSuccess: () => {
        toast.success("Report created")
        queryClient.invalidateQueries({ queryKey: queryKeys.reports.list() })
        router.push("/app/reports")
      },
      onError: (err) => toast.error(err.message),
    }
  )
}
```

## Verification Before Reporting Done

1. List every file changed with line count delta
2. Sample before/after of the most prominent changes
3. Note anything you LEFT unchanged because it was code identifier vs display text
4. Walk through the affected pages and confirm:
   - No console errors
   - No type errors (`tsc --noEmit` if available)
   - Active page highlighting still works
   - All affected user tiers still render correctly
5. If any tests are co-located with the changed files, run them or update them

## Things to Flag, Not Fix

If you notice these during your work, mention them in your report — don't fix them in this ticket:

- Stale dependencies in package.json
- Unused imports in files you're touching
- Existing accessibility issues
- Existing test coverage gaps
- Unrelated bugs

## Output Format

Always report:

**Files Changed**

```
apps/web/path/file.tsx (+12 -3)
apps/web/path/file2.tsx (+5 -5)
```

**Summary of Changes**

One-line per file.

**Key Before/After (for prominent changes)**

Brief snippets.

**What I Left Unchanged**

- foo.tsx line 42 — looked like a target but is code identifier (`planSlug` check)

**Verification Done**

- Tier A: ✅
- Tier B: ✅
- Tier C: ✅ (or "did not test — out of scope")

**Notes / Flags**

Anything to mention but not fix in this ticket.
