import { redirect } from "next/navigation"

// Redirect old branding URL to new unified settings
export default function BrandingRedirect() {
  redirect("/app/settings/branding")
}
