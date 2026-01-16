import { redirect } from "next/navigation"

// Redirect old billing URL to new unified settings
export default function BillingRedirect() {
  redirect("/app/settings/billing")
}
