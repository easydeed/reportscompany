import { redirect } from "next/navigation"

// The company's schedules are a view of Activity (D-317). This path stays so
// links and bookmarks to it still land somewhere.
export default function CompanySchedulesPage() {
  redirect("/app/company/activity?view=schedules")
}
