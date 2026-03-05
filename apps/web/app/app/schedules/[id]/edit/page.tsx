"use client"

import { use } from "react"
import { UnifiedReportWizard } from "@/components/unified-wizard"

interface PageProps {
  params: Promise<{ id: string }>
}

export default function EditSchedulePage({ params }: PageProps) {
  const resolvedParams = use(params)
  return <UnifiedReportWizard defaultMode="schedule" scheduleId={resolvedParams.id} />
}
