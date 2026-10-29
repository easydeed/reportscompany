// The rep's pages — Reports, Schedules, one agent, Leads — kept out of the
// pages so they can be tested on their own. Every field read here is one
// /v1/affiliate/* returns (tests/test_rep_pages_read_what_the_api_returns.py).
//
// The pages this replaces typed their rows by hand against fields the API
// never returned (D-324, the rep twin of D-317): every report read
// "Generating" with no agent or date, schedules had no agent or area, and an
// agent's page had no name or status. The report and schedule sentences are
// the company Activity page's (lib/company-activity.ts): same rows, same words.

import { reportTypeLabel, whenLabel, type Tone } from "@/components/sponsor/shared"

export { pdfFor, reportState, reportWhat, scheduleNext, scheduleWhat, scheduleWhen } from "@/lib/company-activity"

/** One row of GET /v1/affiliate/all-reports. */
export type RepReport = {
  id: string
  report_type: string
  status: string
  generated_at: string | null
  city: string
  pdf_url: string | null
  user_name: string
  agent_account_id: string
  source: "You" | "Agent"
}

/** One row of GET /v1/affiliate/all-schedules. */
export type RepSchedule = {
  id: string
  name: string
  report_type: string
  area: string
  cadence: "weekly" | "monthly"
  send_hour: number | null
  send_minute: number | null
  timezone: string
  active: boolean
  next_run_at: string | null
  user_name: string
  agent_account_id: string
  source: "You" | "Agent"
  weekly_dow: number | null
  monthly_dom: number | null
}

/** One row of GET /v1/affiliate/agents/{id}/reports. */
export type AgentReport = {
  id: string
  report_type: string
  status: string
  generated_at: string | null
  city: string
  pdf_url: string | null
  is_scheduled: boolean
}

/** One row of GET /v1/affiliate/agents/{id}/schedules. */
export type AgentSchedule = {
  id: string
  name: string
  report_type: string
  area: string
  cadence: "weekly" | "monthly"
  send_hour: number | null
  send_minute: number | null
  timezone: string
  active: boolean
  next_run_at: string | null
  recipient_count: number
  weekly_dow: number | null
  monthly_dom: number | null
}

/** GET /v1/affiliate/agents/{id} → `agent`. */
export type BookAgent = {
  id: string
  name: string
  email: string
  status: "active" | "pending" | "deactivated"
  joined_at: string | null
  last_report_at: string | null
  plan_slug: string
  plan_name: string
  market_reports_used: number
  market_reports_limit: number | null
}

/** GET /v1/affiliate/agents/{id} → `leads`, and the totals of GET /v1/affiliate/leads. */
export type LeadCounts = { this_month: number; last_month: number; total: number }

/** GET /v1/affiliate/leads → `agents[]`. */
export type AgentLeadCount = { agent_account_id: string; agent_name: string; this_month: number; last_month: number; total: number }

/** GET /v1/affiliate/leads → `leads[]`. Who the homeowner is never leaves the agent. */
export type BookLead = { id: string; agent_account_id: string; agent_name: string; came_from: "property_page" | "home_value_page" | "other"; created_at: string | null }

/**
 * Where a lead came from, in words. `property_page` covers the QR code and
 * the link alike: the form sends one value for both (D-325), so the page
 * does not pretend to know which.
 */
export function cameFrom(c: BookLead["came_from"]): string {
  if (c === "property_page") return "from their property report page"
  if (c === "home_value_page") return "from their home-value page"
  return "from somewhere else"
}

const n = (k: number, one: string, many = `${one}s`) => `${k} ${k === 1 ? one : many}`

function lastMonthName(now: Date) {
  return new Date(now.getFullYear(), now.getMonth() - 1, 1).toLocaleString("en-US", { month: "long" })
}

/** "Your agents brought in 4 homeowner leads this month — 2 in September." */
export function leadsHeadline(c: Pick<LeadCounts, "this_month" | "last_month">, whose = "Your agents", now: Date = new Date()): string {
  const last = c.last_month ? ` — ${c.last_month} in ${lastMonthName(now)}` : ""
  return c.this_month
    ? `${whose} brought in ${n(c.this_month, "homeowner lead")} this month${last}.`
    : `No homeowner leads ${whose === "Your agents" ? "from your agents " : ""}yet this month${last}.`
}

/** "Priya Shah got a homeowner lead from their property report page". */
export function leadLine(l: Pick<BookLead, "agent_name" | "came_from">): string {
  return `${l.agent_name || "An agent"} got a homeowner lead ${cameFrom(l.came_from)}`
}

/** The agent's standing as one sentence, from the API's status and dates. */
export function agentSentence(a: Pick<BookAgent, "status" | "last_report_at" | "joined_at">): { tone: Tone; text: string } {
  if (a.status === "pending") return { tone: "off", text: "Invited, hasn't joined yet" }
  if (a.status === "deactivated") return { tone: "off", text: "Switched off — they can't sign in" }
  if (!a.last_report_at) return { tone: "warn", text: "Joined, hasn't made a report yet" }
  const days = (Date.now() - new Date(a.last_report_at).getTime()) / 86_400_000
  const when = whenLabel(a.last_report_at)
  return days > 30
    ? { tone: "warn", text: `Quiet — last report ${when}` }
    : { tone: "good", text: `Active — last report ${/^(Today|Yesterday)$/.test(when) ? when.toLowerCase() : when}` }
}

/** "3 of 3 on the Sponsored Free plan" — the limit only when the plan has one. */
export function reportsOfPlan(a: Pick<BookAgent, "market_reports_used" | "market_reports_limit" | "plan_name">): string {
  const lim = a.market_reports_limit
  if (!lim || lim >= 10000) return `on the ${a.plan_name} plan`
  // The plan lets a few through past the limit (usage.grace_ceiling); "4 of 3" reads like an error.
  return a.market_reports_used > lim ? `${a.market_reports_used - lim} over the ${a.plan_name} plan's ${lim}` : `of ${lim} on the ${a.plan_name} plan`
}

/** "Made a market snapshot for Irvine" · "Their schedule made an inventory report". */
export function madeLine(r: Pick<AgentReport, "report_type" | "city" | "is_scheduled">): string {
  const kind = reportTypeLabel(r.report_type)
  const city = r.city && r.city !== "Unknown" ? ` for ${r.city}` : ""
  return `${r.is_scheduled ? "Their schedule made" : "Made"} ${/^[aeiou]/i.test(kind) ? "an" : "a"} ${kind}${city}`
}

export type SourceFilter = "agents" | "mine" | "all"

/** Agents' reports, the rep's own, or both — from the API's `source`. */
export function bySource<T extends { source: "You" | "Agent" }>(rows: T[], f: SourceFilter): T[] {
  return f === "all" ? rows : rows.filter((r) => (f === "mine" ? r.source === "You" : r.source === "Agent"))
}
