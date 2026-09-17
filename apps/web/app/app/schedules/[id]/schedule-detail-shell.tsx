"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { ScheduleDetail } from "@/components/schedules/schedule-detail"
import { VerificationRequiredBanner } from "@/components/shared/verification-required"
import { readVerificationRefusal, type VerificationRefusal } from "@/lib/verification"

export function ScheduleDetailShell({ schedule }: { schedule: any }) {
  const router = useRouter()
  const [verificationRefusal, setVerificationRefusal] = useState<VerificationRefusal | null>(null)

  const handleToggleActive = async (active: boolean) => {
    try {
      const res = await fetch(`/api/proxy/v1/schedules/${schedule.id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ active }),
      })
      // D-019. This did not read the response at all — it refreshed
      // unconditionally, so a refused activation looked exactly like a
      // successful one that had not taken effect yet.
      if (!res.ok) {
        setVerificationRefusal(
          readVerificationRefusal(await res.json().catch(() => ({})))
        )
        return
      }
      setVerificationRefusal(null)
      router.refresh()
    } catch (err) {
      console.error("Failed to toggle schedule:", err)
    }
  }

  const handleDelete = async () => {
    if (!confirm("Are you sure you want to delete this schedule?")) return
    try {
      await fetch(`/api/proxy/v1/schedules/${schedule.id}`, {
        method: "DELETE",
        credentials: "include",
      })
      router.push("/app/schedules")
    } catch (err) {
      console.error("Failed to delete schedule:", err)
    }
  }

  return (
    <>
      {verificationRefusal && (
        <div className="mb-4">
          <VerificationRequiredBanner refusal={verificationRefusal} />
        </div>
      )}
    <ScheduleDetail
      schedule={schedule}
      runs={[]}
      onBack={() => router.back()}
      onToggleActive={handleToggleActive}
      onRunNow={() => {}}
      onEdit={() => router.push(`/app/schedules/${schedule.id}/edit`)}
      onDelete={handleDelete}
    />
    </>
  )
}
