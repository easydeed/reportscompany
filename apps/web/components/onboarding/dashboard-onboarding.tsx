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
  const [onboardingData, setOnboardingData] = useState<any>(null)

  useEffect(() => {
    checkFirstVisit()
  }, [])

  async function checkFirstVisit() {
    try {
      const res = await fetch("/api/proxy/v1/onboarding", { 
        cache: "no-store",
        credentials: "include" 
      })
      if (res.ok) {
        const data = await res.json()
        setOnboardingData(data)

        // Show wizard if:
        // - User hasn't dismissed onboarding
        // - Onboarding is not complete
        // - Progress is low (less than half completed)
        // - Wizard hasn't been shown this session
        const notDismissed = !data.is_dismissed
        const notComplete = !data.is_complete
        const lowProgress = data.progress_percent < 50
        const wizardShownThisSession = sessionStorage.getItem("onboarding_wizard_shown")

        if (notDismissed && notComplete && lowProgress && !wizardShownThisSession) {
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

  // Allow opening wizard from checklist
  function handleOpenWizard() {
    setShowWizard(true)
  }

  return (
    <>
      {/* Onboarding Checklist */}
      <OnboardingChecklist 
        className={className} 
        variant="card" 
        onOpenWizard={handleOpenWizard}
      />

      {/* Setup Wizard Modal */}
      <SetupWizard
        open={showWizard}
        onOpenChange={setShowWizard}
        onComplete={handleWizardComplete}
      />
    </>
  )
}
