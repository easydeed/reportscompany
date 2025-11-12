import AppLayoutClient from "../app-layout"
import { apiFetch } from "@/lib/api"

export default async function AppLayout({ children }: { children: React.ReactNode }) {
  let isAdmin = false
  try {
    const me = await apiFetch("/v1/me")
    isAdmin = me?.role === "ADMIN"
  } catch (error) {
    // User not authenticated or API error
    console.error("Failed to fetch user role:", error)
  }

  return <AppLayoutClient isAdmin={isAdmin}>{children}</AppLayoutClient>
}

