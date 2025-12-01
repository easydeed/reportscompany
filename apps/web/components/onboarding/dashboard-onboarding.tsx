"use client"

import { useEffect, useState } from "react"
import { OnboardingChecklist } from "./onboarding-checklist"
import { SetupWizard } from "./setup-wizard"

interface DashboardOnboardingProps {
  className?: string
}

/**
 * Client component that handles onboarding UI on the dashboard.
 * Shows setup wizard for first-time users and checklist for ongoing onboarding.
 */
export function DashboardOnboarding({ className }: DashboardOnboardingProps) {
  const [showWizard, setShowWizard] = useState(false)
  const [isFirstVisit, setIsFirstVisit] = useState(false)

  useEffect(() => {
    checkFirstVisit()
  }, [])

  async function checkFirstVisit() {
    try {
      const res = await fetch("/api/proxy/v1/onboarding", { cache: "no-store" })
      if (res.ok) {
        const data = await res.json()

        // Show wizard if user hasn't completed any steps and hasn't dismissed
        const hasNoProgress = data.completed_count === 0
        const notDismissed = !data.is_dismissed
        const notComplete = !data.is_complete

        // Check localStorage to see if wizard was shown this session
        const wizardShownThisSession = sessionStorage.getItem("onboarding_wizard_shown")

        if (hasNoProgress && notDismissed && notComplete && !wizardShownThisSession) {
          setIsFirstVisit(true)
          setShowWizard(true)
          sessionStorage.setItem("onboarding_wizard_shown", "true")
        }
      }
    } catch (error) {
      console.error("Failed to check onboarding status:", error)
    }
  }

  function handleWizardComplete() {
    setShowWizard(false)
    // Refresh the page to update all components
    window.location.reload()
  }

  return (
    <>
      {/* Onboarding Checklist */}
      <OnboardingChecklist className={className} variant="card" />

      {/* Setup Wizard Modal */}
      <SetupWizard
        open={showWizard}
        onOpenChange={setShowWizard}
        onComplete={handleWizardComplete}
      />
    </>
  )
}
