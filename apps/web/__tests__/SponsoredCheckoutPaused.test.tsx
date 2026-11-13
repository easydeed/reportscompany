/**
 * Sponsored pilot gate (November 12): a sponsored agent is offered no Upgrade
 * and no checkout while billing is unfinished (LR-011 to LR-014). The API
 * refuses POST /v1/billing/checkout for them and says so in
 * `account.checkout_available`; these hold the app to the same answer.
 */
import React from "react"
import { render, screen, fireEvent } from "@testing-library/react"

const planUsage: { current: unknown } = { current: undefined }

jest.mock("@/hooks/use-api", () => ({
  usePlanUsage: () => ({ data: planUsage.current, isLoading: false }),
}))
jest.mock("next/navigation", () => ({
  useRouter: () => ({ push: jest.fn(), replace: jest.fn() }),
  useSearchParams: () => new URLSearchParams(),
}))
jest.mock("@/components/ui/use-toast", () => ({ useToast: () => ({ toast: jest.fn() }) }))

import { checkoutOffered } from "@/lib/checkout"
import { LimitReached } from "@/components/unified-wizard/limit-reached"
import BillingPage from "@/app/app/settings/billing/page"

const limits = {
  market_reports: { used: 3, limit: 3, status: "at_limit", can_proceed: true },
  schedules: { used: 0, limit: 1, status: "ok", can_proceed: true },
  property_reports: { used: 0, limit: 1, status: "ok", can_proceed: true },
}

function usage(account: Record<string, unknown>) {
  return {
    account: { id: "a", name: "Agent", account_type: "REGULAR", plan_slug: "sponsored_free", ...account },
    plan: { plan_slug: "sponsored_free", plan_name: "Sponsored Free", market_reports_limit: 3, schedules_limit: 1, property_reports_limit: 1 },
    usage: { market_reports_used: 3, schedules_active: 0, property_reports_used: 0 },
    limits,
    stripe_billing: null,
  }
}

describe("checkoutOffered", () => {
  it("is false only when the API says so", () => {
    expect(checkoutOffered({ account: { checkout_available: false } })).toBe(false)
    expect(checkoutOffered({ account: { checkout_available: true } })).toBe(true)
  })

  it("an answer without the field (an older API mid-deploy) keeps today's behaviour", () => {
    expect(checkoutOffered({ account: {} })).toBe(true)
    expect(checkoutOffered(undefined)).toBe(true)
  })
})

describe("the wizard's limit-reached panel", () => {
  it("offers no Upgrade to a sponsored account", () => {
    render(<LimitReached error={null} offerUpgrade={false} onBack={() => {}} onUpgrade={() => {}} />)
    expect(screen.queryByRole("button", { name: /upgrade/i })).toBeNull()
    expect(screen.queryByText(/upgrade/i)).toBeNull()
    expect(screen.getByText("You can make more when your limit resets next month.")).toBeTruthy()
    expect(screen.getByRole("button", { name: "Go Back" })).toBeTruthy()
  })

  it("still offers Upgrade to everyone else", () => {
    const onUpgrade = jest.fn()
    render(<LimitReached error={null} offerUpgrade onBack={() => {}} onUpgrade={onUpgrade} />)
    fireEvent.click(screen.getByRole("button", { name: /Upgrade Plan/ }))
    expect(onUpgrade).toHaveBeenCalledTimes(1)
  })
})

describe("the billing page", () => {
  it("shows a sponsored account no plan buttons and says why", () => {
    planUsage.current = usage({ sponsor_account_id: "s", checkout_available: false })
    render(<BillingPage />)
    expect(screen.queryByRole("button", { name: /upgrade|change plan/i })).toBeNull()
    expect(screen.queryByText("Available Plans")).toBeNull()
    expect(screen.getByTestId("sponsored-no-checkout").textContent).toContain(
      "Upgrades aren’t available on sponsored accounts right now.")
  })

  it("still shows a regular agent the plans and Upgrade", () => {
    planUsage.current = usage({ plan_slug: "free", checkout_available: true })
    render(<BillingPage />)
    expect(screen.getByText("Available Plans")).toBeTruthy()
    expect(screen.getAllByRole("button", { name: /upgrade/i }).length).toBeGreaterThan(0)
    expect(screen.queryByTestId("sponsored-no-checkout")).toBeNull()
  })
})
