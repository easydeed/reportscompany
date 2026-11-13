/**
 * Plan & Seats tells title-company admins "Agents who want more upgrade and pay
 * for it themselves." only while that is true. During the sponsored pilot the
 * API refuses checkout for agents (config/billing.py, SPONSORED_SELF_CHECKOUT)
 * and GET /v1/company/seats says `agents_self_upgrade: false`; the page drops
 * the sentence, and it comes back when the flag flips (Jerry, November 13).
 */
import React from "react"
import { render, screen } from "@testing-library/react"

const seats: { current: Record<string, unknown> } = { current: {} }

jest.mock("@/hooks/use-api", () => ({
  useCompanySeats: () => ({ data: seats.current, isLoading: false, error: null }),
  useCompanyReps: () => ({ data: { reps: [] } }),
  useCompanyAgents: () => ({ data: { agents: [] } }),
  useCompanyBranding: () => ({ data: { branding: {} } }),
}))
jest.mock("next/link", () => ({ __esModule: true, default: ({ children, href }: { children: React.ReactNode; href: string }) => <a href={href}>{children}</a> }))

import PlanAndSeatsPage from "@/app/app/company/plan/page"

const SENTENCE = "Agents who want more upgrade and pay for it themselves."
const base = {
  seats: null,
  history: [],
  agent_plan: { plan_name: "Sponsored Free", market_reports: 3, schedules: 1, property_reports: 1 },
  can_manage: true,
}

function agentsParagraph(): string {
  return screen.getByText(/Agents don.t take a seat/).textContent ?? ""
}

it("drops the sentence while the sponsored pilot gate is on", () => {
  seats.current = { ...base, agents_self_upgrade: false }
  render(<PlanAndSeatsPage />)
  expect(agentsParagraph()).not.toContain(SENTENCE)
  expect(agentsParagraph()).toContain("on the Sponsored Free plan")
})

it("says it again when the API says agents can pay", () => {
  seats.current = { ...base, agents_self_upgrade: true }
  render(<PlanAndSeatsPage />)
  expect(agentsParagraph()).toContain(SENTENCE)
})
