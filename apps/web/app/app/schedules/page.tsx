import { apiFetch } from "@/lib/api"
import { SchedulesListShell, type SchedulesListShellProps } from "@/components/v0-styling/SchedulesListShell"

export default async function SchedulesPage() {
  let items: any[] = []
  
  try {
    items = await apiFetch("/v1/schedules")
  } catch (error) {
    console.error("Failed to fetch schedules:", error)
  }

  // Map fetched data to shell props
  const shellProps: SchedulesListShellProps = {
    schedules: items || [],
  };

  return <SchedulesListShell {...shellProps} />;
}
