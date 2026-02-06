import { useQuery, useQueryClient } from "@tanstack/react-query"

// ============================================================================
// Core fetch function (reuses the existing proxy pattern)
// ============================================================================

async function apiFetchRQ(path: string, init?: RequestInit) {
  const res = await fetch(`/api/proxy${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...init?.headers,
    },
    credentials: "include",
  })

  if (!res.ok) {
    const text = await res.text().catch(() => "")
    throw new Error(`API ${res.status}: ${text}`)
  }

  return res.json()
}

// ============================================================================
// Query Key Factory
// Organized key structure prevents cache collisions and enables targeted
// invalidation (e.g., invalidate all "reports" queries at once).
// ============================================================================

export const queryKeys = {
  // User / Account
  me: ["me"] as const,
  planUsage: ["plan-usage"] as const,
  onboarding: ["onboarding"] as const,
  branding: ["branding"] as const,
  usage: ["usage"] as const,

  // Reports
  reports: {
    all: ["reports"] as const,
    list: (filters?: Record<string, string>) =>
      ["reports", "list", filters ?? {}] as const,
    detail: (id: string) => ["reports", "detail", id] as const,
  },

  // Property Reports
  propertyReports: {
    all: ["property-reports"] as const,
    list: () => ["property-reports", "list"] as const,
    detail: (id: string) => ["property-reports", "detail", id] as const,
  },

  // Schedules
  schedules: {
    all: ["schedules"] as const,
    list: () => ["schedules", "list"] as const,
    detail: (id: string) => ["schedules", "detail", id] as const,
  },

  // Contacts
  contacts: {
    all: ["contacts"] as const,
    list: () => ["contacts", "list"] as const,
    groups: () => ["contacts", "groups"] as const,
  },

  // Leads
  leads: {
    all: ["leads"] as const,
    list: (filters?: Record<string, string>) =>
      ["leads", "list", filters ?? {}] as const,
    stats: () => ["leads", "stats"] as const,
  },

  // Affiliate
  affiliate: {
    overview: ["affiliate", "overview"] as const,
    accounts: ["affiliate", "accounts"] as const,
    detail: (id: string) => ["affiliate", "detail", id] as const,
  },
} as const

// ============================================================================
// Hooks — Each replaces a useEffect + useState + setLoading + setError block
// ============================================================================

/** Current user profile */
export function useMe() {
  return useQuery({
    queryKey: queryKeys.me,
    queryFn: () => apiFetchRQ("/v1/users/me"),
    staleTime: 5 * 60 * 1000, // Profile rarely changes — 5 min
  })
}

/** Plan usage (shown on dashboard + sidebar) */
export function usePlanUsage() {
  return useQuery({
    queryKey: queryKeys.planUsage,
    queryFn: () => apiFetchRQ("/v1/account/plan-usage"),
    staleTime: 2 * 60 * 1000,
  })
}

/** Dashboard usage data */
export function useUsage() {
  return useQuery({
    queryKey: queryKeys.usage,
    queryFn: () => apiFetchRQ("/v1/usage"),
  })
}

/** Onboarding status */
export function useOnboarding() {
  return useQuery({
    queryKey: queryKeys.onboarding,
    queryFn: () => apiFetchRQ("/v1/onboarding"),
    staleTime: 5 * 60 * 1000,
  })
}

/** Market reports list */
export function useReports() {
  return useQuery({
    queryKey: queryKeys.reports.list(),
    queryFn: () => apiFetchRQ("/v1/reports"),
  })
}

/** Property reports list */
export function usePropertyReports() {
  return useQuery({
    queryKey: queryKeys.propertyReports.list(),
    queryFn: () => apiFetchRQ("/v1/property/reports?limit=100"),
  })
}

/** Schedules list */
export function useSchedules() {
  return useQuery({
    queryKey: queryKeys.schedules.list(),
    queryFn: () => apiFetchRQ("/v1/schedules"),
  })
}

/** Contacts list */
export function useContacts() {
  return useQuery({
    queryKey: queryKeys.contacts.list(),
    queryFn: () => apiFetchRQ("/v1/contacts"),
  })
}

/** Contact groups */
export function useContactGroups() {
  return useQuery({
    queryKey: queryKeys.contacts.groups(),
    queryFn: () => apiFetchRQ("/v1/contact-groups"),
  })
}

/** Leads with optional filters */
export function useLeads(filters?: Record<string, string>) {
  const params = filters
    ? "?" + new URLSearchParams(filters).toString()
    : ""
  return useQuery({
    queryKey: queryKeys.leads.list(filters),
    queryFn: () => apiFetchRQ(`/v1/leads${params}`),
  })
}

/** All leads (for computing stats client-side) */
export function useAllLeads() {
  return useQuery({
    queryKey: queryKeys.leads.all,
    queryFn: () => apiFetchRQ("/v1/leads?limit=100"),
  })
}

/** Affiliate overview */
export function useAffiliateOverview() {
  return useQuery({
    queryKey: queryKeys.affiliate.overview,
    queryFn: () => apiFetchRQ("/v1/affiliate/overview"),
    retry: false, // Don't retry 403 (not affiliate)
  })
}

/** Branding settings */
export function useBranding() {
  return useQuery({
    queryKey: queryKeys.branding,
    queryFn: () => apiFetchRQ("/v1/account/branding"),
    staleTime: 5 * 60 * 1000,
  })
}

// ============================================================================
// Cache Invalidation Helper
// Use after mutations (create report, delete schedule, etc.)
// ============================================================================

export function useInvalidate() {
  const qc = useQueryClient()
  return {
    /** Invalidate all queries matching a key prefix */
    invalidate: (...key: readonly unknown[]) => qc.invalidateQueries({ queryKey: key }),
    /** Invalidate specific common groups */
    reports: () => qc.invalidateQueries({ queryKey: queryKeys.reports.all }),
    propertyReports: () => qc.invalidateQueries({ queryKey: queryKeys.propertyReports.all }),
    schedules: () => qc.invalidateQueries({ queryKey: queryKeys.schedules.all }),
    contacts: () => qc.invalidateQueries({ queryKey: queryKeys.contacts.all }),
    leads: () => qc.invalidateQueries({ queryKey: queryKeys.leads.all }),
    planUsage: () => qc.invalidateQueries({ queryKey: queryKeys.planUsage }),
    usage: () => qc.invalidateQueries({ queryKey: queryKeys.usage }),
    onboarding: () => qc.invalidateQueries({ queryKey: queryKeys.onboarding }),
  }
}
