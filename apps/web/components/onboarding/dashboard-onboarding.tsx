"use client"

import { useEffect, useState } from "react"
import { useOnboarding } from "@/hooks/use-api"
import { OnboardingChecklist, type OnboardingStatus } from "./onboarding-checklist"
import { SetupWizard } from "./setup-wizard"

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
  const { data: fetchedStatus } = useOnboarding()
  const status = (initialStatus ?? fetchedStatus ?? null) as OnboardingStatus | null
  const [showWizard, setShowWizard] = useState(false)
  const [wizardChecked, setWizardChecked] = useState(false)

  useEffect(() => {
    if (!status || wizardChecked) return
    setWizardChecked(true)

    const notDismissed = !status.is_dismissed
    const notComplete = !status.is_complete
    const lowProgress = status.progress_percent < 50
    const wizardShownThisSession = sessionStorage.getItem("onboarding_wizard_shown")

    if (notDismissed && notComplete && lowProgress && !wizardShownThisSession) {
      setShowWizard(true)
      sessionStorage.setItem("onboarding_wizard_shown", "true")
    }
  }, [status, wizardChecked])

  function handleWizardComplete() {
    setShowWizard(false)
    window.location.reload()
  }

  function handleOpenWizard() {
    setShowWizard(true)
  }

  return (
    <>
      <OnboardingChecklist 
        className={className} 
        variant="card" 
        onOpenWizard={handleOpenWizard}
        initialStatus={status}
      />

      <SetupWizard
        open={showWizard}
        onOpenChange={setShowWizard}
        onComplete={handleWizardComplete}
      />
    </>
  )
}
