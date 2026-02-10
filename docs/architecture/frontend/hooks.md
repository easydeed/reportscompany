# Custom Hooks

## useUser (`lib/hooks/use-user.ts`)

React Query hook for current user data.

```typescript
export function useUser() {
  return useQuery({
    queryKey: ['user'],
    queryFn: fetchUser,
    staleTime: 10 * 60 * 1000, // 10 min cache
  })
}
```

Fetches `GET /v1/users/me` via proxy. Returns `User` type with fields: id, email, first_name, last_name, avatar_url, role (USER/ADMIN), account_type (REGULAR/INDUSTRY_AFFILIATE), account_id, job_title, company_name, phone, website, email_verified.

## usePlanUsage (`lib/hooks/use-plan-usage.ts`)

React Query hook for account plan and usage data.

```typescript
export function usePlanUsage() {
  return useQuery({
    queryKey: ['plan-usage'],
    queryFn: fetchPlanUsage,
    staleTime: 5 * 60 * 1000, // 5 min cache
  })
}
```

Fetches `GET /v1/account/plan-usage` via proxy. Returns `PlanUsage` type with:
- `plan`: plan_name, plan_slug, monthly_reports_limit
- `info`: reports_this_period, active_schedules
- `limits`: reports_used, reports_limit, schedules_used, schedules_limit

## useToast (`hooks/use-toast.ts`)

Toast notification system inspired by react-hot-toast. Uses an in-memory state store with listener pattern (not React context).

```typescript
const { toast, dismiss, toasts } = useToast()
toast({ title: "Success", description: "Report created" })
toast({ title: "Error", description: "...", variant: "destructive" })
```

Config: `TOAST_LIMIT = 1` (only one toast at a time), `TOAST_REMOVE_DELAY = 1000000ms`.

Works with the `components/ui/toast.tsx` and `components/ui/toaster.tsx` components.

## useGooglePlaces (`hooks/useGooglePlaces.ts`)

Google Places Autocomplete integration hook.

```typescript
const { place, isLoaded, error, reset } = useGooglePlaces(inputRef, {
  onPlaceSelect: (placeResult) => { ... },
  countryRestriction: 'us',
})
```

### How It Works
1. Dynamically loads Google Maps script if not already loaded (uses `NEXT_PUBLIC_GOOGLE_MAPS_API_KEY`)
2. Polls for input element readiness (since refs don't trigger re-renders)
3. Creates `google.maps.places.Autocomplete` on the input with `types: ["address"]`
4. Parses address components on selection: streetNumber, street, address, city, state, zip, county, lat, lng

### PlaceResult Type
```typescript
interface PlaceResult {
  streetNumber: string
  street: string
  address: string      // Full street address
  city: string
  state: string
  zip: string
  county: string
  fullAddress: string  // Google's formatted address
  lat?: number
  lng?: number
}
```

## useMobile (`components/ui/use-mobile.tsx`)

Viewport detection hook. Returns `true` when viewport width is below mobile breakpoint.

## Key Files

- `apps/web/lib/hooks/use-user.ts`
- `apps/web/lib/hooks/use-plan-usage.ts`
- `apps/web/hooks/use-toast.ts`
- `apps/web/hooks/useGooglePlaces.ts`
- `apps/web/components/ui/use-mobile.tsx`
