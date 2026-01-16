"use client"

import { use } from "react"
import { ScheduleBuilder } from "@/components/schedule-builder"

interface PageProps {
  params: Promise<{ id: string }>
}

export default function EditSchedulePage({ params }: PageProps) {
  const resolvedParams = use(params)
  
  return <ScheduleBuilder scheduleId={resolvedParams.id} />
}

