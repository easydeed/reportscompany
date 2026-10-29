// The company Plan & Seats page's decisions, kept out of the page so they can
// be tested on their own. Every field read here is one /v1/company/seats,
// /reps or /agents returns (tests/test_company_pages_read_what_the_api_returns.py).
// Seats are REP seats: agents take none. No number on this page is typed in —
// the seat count is the company's, the agents' limits are the plans table's.

import type { Agent, Rep, SeatSummary } from "@/lib/company-people"
import { whenLabel } from "@/components/sponsor/shared"

/** GET /v1/company/seats → `agent_plan`. A limit the table doesn't give is null. */
export type AgentPlan = { plan_name: string; market_reports: number | null; schedules: number | null; property_reports: number | null }

/** GET /v1/company/seats → one `history` row, newest first. */
export type SeatPeriod = {
  rep_id: string
  rep_name: string
  started_at: string | null
  ended_at: string | null
  ended_reason: "reassigned" | "invite_cancelled" | null
  successor_rep_id: string | null
  successor_name: string | null
  agents_moved: number | null
}

/** The plan the API names as the agents' (`seats.AGENT_PLAN`). */
export const AGENT_PLAN_SLUG = "sponsored_free"

const n = (k: number, one: string, many = `${one}s`) => `${k} ${k === 1 ? one : many}`

/** "6 rep seats, 5 in use." — or, off seats, the reps counted with no cap. */
export function planHeadline(seats: SeatSummary | null | undefined, repsHoldingSeats: number): string {
  if (!seats) return `No seat count is set for your company, so there's no cap on reps. ${n(repsHoldingSeats, "rep")} right now.`
  return `${n(seats.total, "rep seat")}, ${seats.held} in use.`
}

export type SeatRow =
  | { kind: "held"; label: string; rep: Rep; tone: "good" | "warn" | "off"; text: string }
  | { kind: "open"; label: string }

/**
 * One row per seat: the reps holding one (by name), then the open seats.
 * Off seats there is no count, so no open rows and no "Seat N" numbering.
 */
export function seatRows(seats: SeatSummary | null | undefined, reps: Rep[]): SeatRow[] {
  const holders = reps.filter((r) => r.holds_seat).sort((a, b) => a.name.localeCompare(b.name))
  const rows: SeatRow[] = holders.map((rep, i) => ({
    kind: "held" as const,
    label: seats ? `Seat ${i + 1}` : "",
    rep,
    ...holderSentence(rep),
  }))
  const open = seats ? Math.max(seats.total - holders.length, 0) : 0
  for (let i = 0; i < open; i++) rows.push({ kind: "open", label: `Seat ${holders.length + i + 1}` })
  return rows
}

/** What a held seat is doing — the seat's view, not the rep's whole story. */
export function holderSentence(r: Pick<Rep, "status" | "idle" | "agent_count">): { tone: "good" | "warn" | "off"; text: string } {
  if (r.status === "pending") return { tone: "off", text: "Invited, hasn't joined · the seat is held for them" }
  if (r.idle) return { tone: "warn", text: `${n(r.agent_count, "agent")} · no reports from their agents in 30 days` }
  return { tone: "good", text: n(r.agent_count, "agent") }
}

/**
 * "3 market reports a month, 1 property report a month and 1 schedule that
 * sends on its own" — only the limits the table gives; "" when it gives none.
 */
export function agentPlanLimits(p: AgentPlan | null | undefined): string {
  if (!p) return ""
  const parts: string[] = []
  if (p.market_reports) parts.push(`${n(p.market_reports, "market report")} a month`)
  if (p.property_reports) parts.push(`${n(p.property_reports, "property report")} a month`)
  if (p.schedules) parts.push(`${n(p.schedules, "schedule")} that send${p.schedules === 1 ? "s" : ""} on ${p.schedules === 1 ? "its" : "their"} own`)
  if (parts.length < 2) return parts.join("")
  return `${parts.slice(0, -1).join(", ")} and ${parts[parts.length - 1]}`
}

/** "Of your 14 agents, 12 are on Sponsored Free and 2 have upgraded." */
export function agentPlanCounts(agents: Pick<Agent, "plan">[], p: AgentPlan | null | undefined): string {
  if (agents.length === 0) return "Your reps haven't invited any agents yet."
  const onPlan = agents.filter((a) => a.plan === AGENT_PLAN_SLUG).length
  const upgraded = agents.length - onPlan
  const name = p?.plan_name ?? "the sponsored plan"
  return `Of your ${n(agents.length, "agent")}, ${onPlan} ${onPlan === 1 ? "is" : "are"} on ${name} and ${upgraded} ${upgraded === 1 ? "has" : "have"} upgraded.`
}

/** `whenLabel`, with the year when it isn't this one: a seat history spans years. */
export function historyDate(iso: string | null, now: Date = new Date()): string {
  if (!iso) return ""
  const d = new Date(iso)
  if (d.getFullYear() === now.getFullYear()) return whenLabel(iso)
  return d.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })
}

/** One history row as a sentence. The date is the row's own, shown beside it. */
export function seatPeriodLine(h: SeatPeriod): { text: string; at: string | null } {
  if (h.ended_reason === "reassigned") {
    const to = h.successor_name ? ` to ${h.successor_name}` : ""
    const moved = h.agents_moved ? ` · ${n(h.agents_moved, "agent")} moved with it` : ""
    return { text: `${h.rep_name}'s seat went${to}${moved}`, at: h.ended_at }
  }
  if (h.ended_reason === "invite_cancelled") return { text: `${h.rep_name}'s invite was cancelled · the seat opened`, at: h.ended_at }
  return { text: `${h.rep_name} was given a seat`, at: h.started_at }
}
