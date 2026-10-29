// The company People page's decisions, kept out of the page so they can be
// tested on their own: which actions a rep row offers, what a row says, and the
// seat line. Every field read here is one /v1/company/reps, /agents or /seats
// returns (tests/test_company_people_reads_what_the_api_returns.py).

import { sinceLabel, whenLabel, QUIET_DAYS, type Tone } from "@/components/sponsor/shared"

export type RepStatus = "active" | "pending" | "deactivated"

/** `whenLabel` mid-sentence: "today", "yesterday", "Tuesday", "Oct 14". */
function when(iso: string): string {
  const w = whenLabel(iso)
  return w === "Today" || w === "Yesterday" ? w.toLowerCase() : w
}

/** One row of GET /v1/company/reps. */
export type Rep = {
  id: string
  name: string
  email: string
  office: string
  status: RepStatus
  agent_count: number
  reports_this_month: number
  last_active: string | null
  idle: boolean
  holds_seat: boolean
}

/** One row of GET /v1/company/agents. */
export type Agent = {
  agent_id: string
  agent_name: string
  email: string
  rep_id: string
  rep_name: string
  status: RepStatus
  plan: string
  reports_this_month: number
  last_activity: string | null
}

/** GET /v1/company/seats → `seats`: null when the company is not on seats. */
export type SeatSummary = { total: number; held: number; open: number; pending: number; idle: number }

export type RepAction = "resend" | "cancel" | "replace"

/**
 * What a rep row can do, from what the server allows:
 *  - resend: the invite has not been accepted (POST /resend-rep-invite);
 *  - cancel: not joined, holds a seat, and has no agents — the server refuses
 *    a pending rep with agents (`seats.cancel_rep_invite`);
 *  - replace: holds a seat (POST /reps/{id}/reassign) — a joined rep's seat
 *    moves this way, and so does a pending rep's that already has agents.
 * A rep with no seat (switched off, or reassigned away) has no seat action.
 */
export function repActions(r: Rep): RepAction[] {
  const out: RepAction[] = []
  if (r.status === "pending") out.push("resend")
  if (r.holds_seat && r.status === "pending" && r.agent_count === 0) out.push("cancel")
  else if (r.holds_seat && r.status !== "deactivated") out.push("replace")
  return out
}

/** One sentence per rep, derived from the row. */
export function repSentence(r: Pick<Rep, "status" | "agent_count" | "reports_this_month" | "last_active">): { tone: Tone; text: string } {
  if (r.status === "pending") return { tone: "off", text: "Invited, hasn't joined yet" }
  if (r.status === "deactivated") return { tone: "off", text: `Switched off${r.agent_count ? ` · ${r.agent_count} agent${r.agent_count === 1 ? "" : "s"} still in their book` : ""}` }
  if (r.agent_count === 0) return { tone: "warn", text: "No agents yet" }
  const quietDays = r.last_active ? (Date.now() - new Date(r.last_active).getTime()) / 86_400_000 : Infinity
  const head = `${r.agent_count} agent${r.agent_count === 1 ? "" : "s"} · ${r.reports_this_month} report${r.reports_this_month === 1 ? "" : "s"} this month`
  if (!r.last_active) return { tone: "warn", text: `${head} · nothing made yet` }
  if (quietDays > QUIET_DAYS) return { tone: "warn", text: `${head} · quiet for ${sinceLabel(r.last_active)}` }
  return { tone: "good", text: `${head} · active ${when(r.last_active)}` }
}

/** "1 open · 2 invited, not joined · 1 idle for a month". */
export function seatSub(s: SeatSummary): string {
  return [
    s.open ? `${s.open} open` : "None open",
    s.pending ? `${s.pending} invited, not joined` : null,
    s.idle ? `${s.idle} idle for a month` : null,
  ].filter(Boolean).join(" · ")
}

/** The line under the People header: seats when on seats, else nothing. */
export function seatLine(s: SeatSummary | null | undefined): string | null {
  if (!s) return null
  return `${s.held} of ${s.total} rep seat${s.total === 1 ? "" : "s"} in use · ${seatSub(s)}`
}

/** Agents grouped by their rep's id (D-276: never by name — two reps can share one). */
export function agentsByRep(agents: Agent[]): Record<string, Agent[]> {
  const m: Record<string, Agent[]> = {}
  for (const a of agents) (m[a.rep_id] ||= []).push(a)
  return m
}

/** What an agent row says about the agent. "Made", not "sent": the feed is
 *  generated reports, and a report can be downloaded without going anywhere. */
export function agentSentence(a: Pick<Agent, "status" | "last_activity">): string {
  if (a.status === "pending") return "Hasn't joined yet"
  if (a.status === "deactivated") return "Switched off"
  return a.last_activity ? `Last report ${when(a.last_activity)}` : "No reports yet"
}

export const AGENT_STATUS: Record<RepStatus, { label: string; cls: string }> = {
  active: { label: "Active", cls: "text-[var(--success-foreground)]" },
  pending: { label: "Invited", cls: "text-muted-foreground" },
  deactivated: { label: "Switched off", cls: "text-[var(--warning-foreground)]" },
}

/**
 * The name fields the invite and reassign endpoints require, from the one
 * name the admin typed. Nothing is guessed from an email address: the invite
 * greets the person by this name.
 */
export function splitName(full: string): { name: string; first_name: string; last_name: string } | null {
  const name = full.trim().replace(/\s+/g, " ")
  if (!name) return null
  const [first_name, ...rest] = name.split(" ")
  return { name, first_name, last_name: rest.join(" ") }
}
