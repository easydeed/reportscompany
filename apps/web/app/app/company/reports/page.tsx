import { redirect } from "next/navigation"

// The company's reports are a view of Activity (D-317). This path stays so
// links and bookmarks to it still land somewhere.
export default function CompanyReportsPage() {
  redirect("/app/company/activity")
}
