import AppLayoutClient from "../app-layout"
import { apiFetch } from "@/lib/api"

export default async function AppLayout({ children }: { children: React.ReactNode }) {
  let isAdmin = false
  let isAffiliate = false
  let accountType = ""
  
  try {
    const me = await apiFetch("/v1/me")
    isAdmin = me?.role === "ADMIN"
    isAffiliate = me?.account_type === "INDUSTRY_AFFILIATE"
    accountType = me?.account_type || "REGULAR"
  } catch (error) {
    // User not authenticated or API error
    console.error("Failed to fetch user role:", error)
  }

  return <AppLayoutClient isAdmin={isAdmin} isAffiliate={isAffiliate} accountType={accountType}>{children}</AppLayoutClient>
}

