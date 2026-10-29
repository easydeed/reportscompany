// The company Activity page's decisions, kept out of the page so they can be
// tested on their own. Every field read here is one GET /v1/company/reports or
// /v1/company/schedules returns (tests/test_company_activity_reads_what_the_api_returns.py).
//
// The pages this replaces typed their rows by hand — `created_at`,
// `user_type: "rep"`, `status: "complete"`, `run_count` — against an API that
// returns none of those, so every report read "Generating" with no name, date
// or PDF, and the schedules page counted nothing (D-317).

import { reportTypeLabel, type Tone } from "@/components/sponsor/shared"

/** One row of GET /v1/company/reports. */
export type ActivityReport = {
  id: string
  report_type: string
  status: string
  generated_at: string | null
  city: string
  pdf_url: string | null
  account_name: string
  user_type: "Rep" | "Agent"
  user_name: string
  account_id: string
  rep_id: string
  rep_name: string
}

/** One row of GET /v1/company/schedules. */
export type ActivitySchedule = {
  id: string
  name: string
  report_type: string
  area: string
  cadence: "weekly" | "monthly"
  active: boolean
  next_run_at: string | null
  account_name: string
  user_type: "Rep" | "Agent"
  user_name: string
  send_hour: number | null
  send_minute: number | null
  timezone: string
  account_id: string
  rep_id: string
  rep_name: string
  weekly_dow: number | null
  monthly_dom: number | null
}

type Who = Pick<ActivityReport, "user_name" | "account_name" | "user_type" | "rep_name">

/** The person, and where they sit: "Rep", or "Ben Carter's agent". */
export function who(r: Who): { name: string; sub: string } {
  return { name: r.user_name || r.account_name, sub: r.user_type === "Rep" ? "Rep" : `${r.rep_name}'s agent` }
}

/** The API says "Unknown" when a row has no city; the page says nothing. */
function place(city: string | null | undefined): string {
  return city && city !== "Unknown" ? city : ""
}

/** "Irvine · market snapshot". */
export function reportWhat(r: Pick<ActivityReport, "city" | "report_type">): string {
  return [place(r.city), reportTypeLabel(r.report_type)].filter(Boolean).join(" · ")
}

/**
 * The report's state as a sentence. `report_generations.status` is
 * queued / processing / completed / failed (and `pending` on old rows).
 */
export function reportState(status: string): { tone: Tone; text: string } {
  if (status === "completed") return { tone: "good", text: "Made" }
  if (status === "failed") return { tone: "warn", text: "Didn't finish" }
  return { tone: "off", text: "Being made" }
}

/** A PDF link only for a finished report that has one. */
export function pdfFor(r: Pick<ActivityReport, "status" | "pdf_url">): string | null {
  return r.status === "completed" && r.pdf_url ? r.pdf_url : null
}

const DAYS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]

function ordinal(n: number): string {
  const s = n % 100 >= 11 && n % 100 <= 13 ? "th" : ({ 1: "st", 2: "nd", 3: "rd" } as Record<number, string>)[n % 10] ?? "th"
  return `${n}${s}`
}

function clock(h: number | null, m: number | null): string {
  if (h == null) return ""
  return `${h % 12 || 12}:${String(m ?? 0).padStart(2, "0")} ${h >= 12 ? "PM" : "AM"}`
}

/** "PDT" for America/Los_Angeles; the zone name itself when Intl doesn't know it. */
export function zoneLabel(tz: string, at: Date = new Date()): string {
  try {
    return new Intl.DateTimeFormat("en-US", { timeZone: tz, timeZoneName: "short" })
      .formatToParts(at).find((p) => p.type === "timeZoneName")?.value ?? tz
  } catch {
    return tz
  }
}

/**
 * "Every Monday at 8:00 AM PDT" / "The 1st of each month at 9:00 AM PDT".
 * `weekly_dow` is 0 = Sunday (services/schedule_utils.py). A day the row
 * doesn't carry is left out, not guessed.
 */
export function scheduleWhen(s: Pick<ActivitySchedule, "cadence" | "weekly_dow" | "monthly_dom" | "send_hour" | "send_minute" | "timezone">, at?: Date): string {
  const time = clock(s.send_hour, s.send_minute)
  const at_ = time ? ` at ${time} ${zoneLabel(s.timezone, at)}` : ""
  if (s.cadence === "monthly") return s.monthly_dom ? `The ${ordinal(s.monthly_dom)} of each month${at_}` : `Monthly${at_}`
  return s.weekly_dow != null && DAYS[s.weekly_dow] ? `Every ${DAYS[s.weekly_dow]}${at_}` : `Weekly${at_}`
}

/** A date ahead: "today" · "tomorrow" · "Friday" · "Nov 1". (`whenLabel` looks back.) */
export function aheadLabel(iso: string, now: Date = new Date()): string {
  const d = new Date(iso)
  const days = Math.round((new Date(d).setHours(0, 0, 0, 0) - new Date(now).setHours(0, 0, 0, 0)) / 86_400_000)
  if (days <= 0) return "today"
  if (days === 1) return "tomorrow"
  if (days < 7) return d.toLocaleDateString("en-US", { weekday: "long" })
  return d.toLocaleDateString("en-US", { month: "short", day: "numeric" })
}

/** "Next send Friday" · "Paused". */
export function scheduleNext(s: Pick<ActivitySchedule, "active" | "next_run_at">, now?: Date): { tone: Tone; text: string } {
  if (!s.active) return { tone: "warn", text: "Paused" }
  return s.next_run_at ? { tone: "good", text: `Next send ${aheadLabel(s.next_run_at, now)}` } : { tone: "off", text: "No next send set" }
}

/** "Irvine · market snapshot" for a schedule. */
export function scheduleWhat(s: Pick<ActivitySchedule, "area" | "report_type">): string {
  return reportWhat({ city: s.area, report_type: s.report_type })
}

export type WhoFilter = "everyone" | "Rep" | "Agent"

export function byWho<T extends { user_type: "Rep" | "Agent" }>(rows: T[], f: WhoFilter): T[] {
  return f === "everyone" ? rows : rows.filter((r) => r.user_type === f)
}
