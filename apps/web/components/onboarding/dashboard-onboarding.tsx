"use client"

import { useEffect, useRef } from "react"
import { useRouter } from "next/navigation"
import { useOnboarding } from "@/hooks/use-api"
import { OnboardingChecklist, type OnboardingStatus } from "./onboarding-checklist"

interface DashboardOnboardingProps {
  className?: string
  /** Server-fetched onboarding status to avoid client-side loading flash */
  initialStatus?: OnboardingStatus | null
}

/**
 * Client component that handles onboarding UI on the dashboard.
 * Shows setup wizard for first-time users and checklist for ongoing onboarding.
 */
export function DashboardOnboarding({ className, initialStatus }: DashboardOnboardingProps) {
  const router = useRouter()
  const { data: fetchedStatus } = useOnboarding()
  const status = (initialStatus ?? fetchedStatus ?? null) as OnboardingStatus | null
  const redirectCheckedRef = useRef(false)

  useEffect(() => {
    if (!status || redirectCheckedRef.current) return
    redirectCheckedRef.current = true

    const notDismissed = !status.is_dismissed
    const notComplete = !status.is_complete
    const lowProgress = status.progress_percent < 50
    const guidedShownThisSession = sessionStorage.getItem("guided_onboarding_shown")
    const guidedSkippedThisSession = sessionStorage.getItem("guided_onboarding_skipped")

    if (notDismissed && notComplete && lowProgress && !guidedShownThisSession && !guidedSkippedThisSession) {
      sessionStorage.setItem("guided_onboarding_shown", "true")
      router.replace("/app/get-started")
    }
  }, [status, router])

  function handleOpenWizard() {
    router.push("/app/get-started")
  }

  return (
    <>
      <OnboardingChecklist 
        className={className} 
        variant="card" 
        onOpenWizard={handleOpenWizard}
        initialStatus={status}
      />
    </>
  )
}
