"use client"

import { ScheduleWizard, type ScheduleWizardState } from "@/components/schedules"
import { useRouter } from "next/navigation"

export default function NewSchedulePage() {
  const router = useRouter()

  const handleSubmit = async (data: ScheduleWizardState) => {
    // Parent will wire API call
    console.log("[v0] Create schedule", data)
    // After successful creation, navigate back to schedules list
    router.push("/dashboard/schedules")
  }

  const handleCancel = () => {
    router.push("/dashboard/schedules")
  }

  return <ScheduleWizard onSubmit={handleSubmit} onCancel={handleCancel} />
}
