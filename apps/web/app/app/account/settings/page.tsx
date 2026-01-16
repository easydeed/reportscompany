import { redirect } from "next/navigation"

// Redirect old account settings URL to new unified settings
export default function AccountSettingsRedirect() {
  redirect("/app/settings/profile")
}
