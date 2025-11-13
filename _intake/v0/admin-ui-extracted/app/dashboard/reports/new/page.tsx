"use client"

import { useRouter } from "next/navigation"
import Wizard from "@/components/report-wizard"

export default function NewReportPage() {
  const router = useRouter()

  const handleSubmit = async (payload: any) => {
    console.log("[v0] Report payload:", payload)
    // TODO: Make API call to POST /v1/reports
    // For now, just log and redirect
    alert("Report generation started! (API integration pending)")
    router.push("/dashboard/reports")
  }

  const handleCancel = () => {
    router.push("/dashboard/reports")
  }

  return <Wizard onSubmit={handleSubmit} onCancel={handleCancel} />
}
