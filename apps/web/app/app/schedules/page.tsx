import { SchedulesListShell, type SchedulesListShellProps } from "@/components/v0-styling/SchedulesListShell"
import { cookies } from "next/headers"
import { getApiBase } from "@/lib/get-api-base"

export default async function SchedulesPage() {
  let schedules: any[] = []

  try {
    const API_BASE = getApiBase()
    const cookieStore = await cookies()
    const token = cookieStore.get("mr_token")?.value

    if (token) {
      const res = await fetch(`${API_BASE}/v1/schedules`, {
        headers: {
          Cookie: `mr_token=${token}`,
        },
        cache: "no-store",
      })

      if (res.ok) {
        const data = await res.json()
        // Backend returns { schedules: [...], count: n }
        schedules = Array.isArray(data) ? data : (Array.isArray(data?.schedules) ? data.schedules : [])
      }
    }
  } catch (error) {
    console.error("Failed to fetch schedules:", error)
  }

  // Map fetched data to shell props
  const shellProps: SchedulesListShellProps = {
    schedules,
  };

  return <SchedulesListShell {...shellProps} />;
}
