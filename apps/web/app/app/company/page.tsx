"use client"

// /app/company — the company dashboard. Answers one question on open: is my
// network working. Header is the brand that flows down; three plain stat
// cells; reps as sentences; activity as sentences. No usage bars (the
// company's own market-report limit is not the number that matters), no
// quick-actions card, no metric-card icons or deltas.
//
// Adopted from Design's Sponsor v4 with these changes, each to what the data
// says: the lead line reads `metrics.leads_this_month` / `leads_last_month`
// (added to /v1/company/overview for it — a read of `leads`, nothing captured);
// activity is "made", not "sent", and a nameless row is "Someone" (reps' own
// reports are in the feed too); (the feed is generated reports, and a report
// can be downloaded without going anywhere); its heading is "Recent", not
// "This week" (the API returns the last ten, however old); and a deactivated
// rep's agents are "still in their book" — a deactivated rep holds no seat, so
// the seat reassign endpoint (`POST /v1/company/reps/{id}/reassign`) is not
// what "need a new rep" points at, and its UI is not built yet. "Reports this month" says "None last month"
// rather than the API's percentage against a zero.

import Link from "next/link"
import { Send, UserPlus } from "lucide-react"
import { useCompanyOverview, useCompanyBranding } from "@/hooks/use-api"
import { RuleList } from "@/components/ui/list"
import { Avatar, Sentence, StatCell, ActivityRow, H2, whenLabel, sinceLabel, reportTypeLabel, QUIET_DAYS, type Tone } from "@/components/sponsor/shared"

type Rep = { id: string; name: string; email: string; office: string; agent_count: number; reports_this_month: number; last_active: string | null; status: "active" | "pending" | "deactivated" }
type Overview = {
  company: { name: string; plan: string; initials: string }
  metrics: { total_reps: number; total_agents: number; reports_this_month: number; active_agents_30d: number; reports_change_pct: number; reports_last_month: number; agents_at_limit: number; leads_this_month: number; leads_last_month: number }
  /** null when the company is not on seats (nothing enforced). */
  seats: { total: number; held: number; open: number; pending: number; idle: number } | null
  reps: Rep[]
  activity: { id: string; description: string; timestamp: string | null }[]
}

/** One sentence per rep, derived from the row. A rep with no active agents is a seat cooling. */
export function repSentence(r: Rep): { tone: Tone; text: string } {
  if (r.status === "pending") return { tone: "off", text: "Invited, hasn't joined yet" }
  if (r.status === "deactivated") return { tone: "off", text: `Deactivated${r.agent_count ? ` · ${r.agent_count} agent${r.agent_count === 1 ? "" : "s"} still in their book` : ""}` }
  if (r.agent_count === 0) return { tone: "warn", text: "No agents yet" }
  const quietDays = r.last_active ? (Date.now() - new Date(r.last_active).getTime()) / 86_400_000 : Infinity
  const head = `${r.agent_count} agent${r.agent_count === 1 ? "" : "s"} · ${r.reports_this_month} report${r.reports_this_month === 1 ? "" : "s"} this month`
  if (!r.last_active) return { tone: "warn", text: `${head} · nothing sent yet` }
  if (quietDays > QUIET_DAYS) return { tone: "warn", text: `${head} · quiet for ${sinceLabel(r.last_active)}` }
  return { tone: "good", text: `${head} · active ${whenLabel(r.last_active).toLowerCase()}` }
}

/** "1 open · 2 invited, not joined · 1 idle for a month". Idle: a joined rep
 *  whose agents finished no market or property report in 30 days. */
export function seatSub(s: NonNullable<Overview["seats"]>): string {
  const parts = [
    s.open ? `${s.open} open` : "None open",
    s.pending ? `${s.pending} invited, not joined` : null,
    s.idle ? `${s.idle} idle for a month` : null,
  ].filter(Boolean)
  return parts.join(" · ")
}

export default function CompanyDashboard() {
  const { data, isLoading, error } = useCompanyOverview()
  const { data: brandingData } = useCompanyBranding()
  const brand = brandingData?.branding as { logo_url?: string | null; primary_color?: string | null; brand_display_name?: string | null } | null | undefined

  if (error) return <p className="text-[16px] text-muted-foreground">{String(error).includes("403") ? "This account isn't a title-company admin." : "Couldn't load the company right now."}</p>
  const o = data as Overview | undefined
  const m = o?.metrics
  const reps = o?.reps ?? []
  const name = brand?.brand_display_name || o?.company.name || ""
  const primary = brand?.primary_color || "var(--agent-primary)"
  const sending = m ? m.active_agents_30d : 0
  const quietAgents = m ? m.total_agents - m.active_agents_30d : 0

  // Activity rows arrive as "{name} generated {type} for {city}" — rewrite into the house voice.
  const activity = (o?.activity ?? []).map((a) => {
    const match = a.description.match(/^(.*?) generated (.*?) for (.*)$/)
    const kind = match ? reportTypeLabel(match[2].replace(/ /g, "_")) : ""
    // The feed is the company's, its reps' and its agents' reports — a nameless
    // row is not necessarily an agent's.
    const text = match ? `${match[1] || "Someone"} made ${/^[aeiou]/i.test(kind) ? "an" : "a"} ${kind}${match[3] === "unknown" ? "" : ` for ${match[3]}`}` : a.description
    return { id: a.id, text, when: whenLabel(a.timestamp) }
  })
  const lastMonthName = new Date(new Date().getFullYear(), new Date().getMonth() - 1, 1).toLocaleString("en-US", { month: "long" })
  const leadsLine = !m ? null
    : m.leads_this_month > 0
      ? `Your agents brought in ${m.leads_this_month} homeowner lead${m.leads_this_month === 1 ? "" : "s"} this month${m.leads_last_month ? ` — ${m.leads_last_month} in ${lastMonthName}` : ""}.`
      : `No homeowner leads from your agents yet this month${m.leads_last_month ? ` — ${m.leads_last_month} in ${lastMonthName}` : ""}.`

  return (
    <div className="flex flex-col gap-9">
      <div className="flex items-center gap-[18px]">
        {brand?.logo_url
          ? <img src={brand.logo_url} alt="" className="h-14 w-14 rounded-xl object-contain" style={{ background: primary }} />
          : <span className="flex size-14 items-center justify-center rounded-xl text-[18px] font-extrabold text-white" style={{ background: primary }}>{o?.company.initials ?? ""}</span>}
        <div className="flex flex-col gap-1.5">
          <h1 className="text-[34px] font-extrabold leading-[1.1] tracking-[-0.03em] text-foreground">{isLoading ? "\u00a0" : name}</h1>
          {m && <p className="text-[16px] text-muted-foreground">{m.total_reps} rep{m.total_reps === 1 ? "" : "s"} · {m.total_agents} agents · {m.reports_this_month} reports this month</p>}
        </div>
      </div>

      {m && (
        <div className="grid grid-cols-[repeat(auto-fit,minmax(220px,1fr))] gap-4">
          {/* Seats-of-N when the company is on seats; reps otherwise, as before seats existed. */}
          {o?.seats ? (
            <StatCell label="Seats" value={`${o.seats.held} of ${o.seats.total}`} sub={seatSub(o.seats)} subTone={o.seats.idle > 0 ? "warn" : "good"} />
          ) : (
            <StatCell label="Reps" value={String(m.total_reps)} sub={reps.filter((r) => r.status === "pending").length ? `${reps.filter((r) => r.status === "pending").length} invited, not joined` : "All joined"} />
          )}
          <StatCell label="Agents sending" value={`${sending} of ${m.total_agents}`} sub={quietAgents > 0 ? `${quietAgents} haven't sent anything in a month` : "Everyone sent something this month"} subTone={quietAgents > 0 ? "warn" : "good"} />
          <StatCell label="Reports this month" value={String(m.reports_this_month)} sub={m.reports_last_month === 0 ? "None last month" : m.reports_change_pct === 0 ? "Same as last month" : `${m.reports_change_pct > 0 ? "Up" : "Down"} ${Math.abs(m.reports_change_pct)}% on last month`} subTone={m.reports_last_month === 0 || m.reports_change_pct >= 0 ? "good" : "warn"} />
        </div>
      )}

      {leadsLine && (
        <p className={m && m.leads_this_month > 0
          ? "rounded-xl bg-[var(--success-muted)] px-5 py-4 text-[16px] font-medium text-[var(--success-foreground)]"
          : "rounded-xl bg-[var(--surface-cream)] px-5 py-4 text-[16px] text-muted-foreground"}>
          {leadsLine}
        </p>
      )}

      <div className="flex flex-col gap-[14px]">
        <H2 linkLabel="Manage reps & agents →" href="/app/company/reps">Your reps</H2>
        <RuleList>
          {reps.map((r) => { const s = repSentence(r); return (
            <div key={r.id} className="grid grid-cols-[minmax(0,1fr)_minmax(0,1.6fr)] items-center gap-5 border-b border-[var(--border-subtle)] py-[14px]">
              <span className="flex min-w-0 items-center gap-3">
                <Avatar name={r.name} size={34} color={primary} />
                <span className="flex min-w-0 flex-col leading-[1.3]"><span className="truncate text-[15px] font-semibold text-foreground">{r.name}</span><span className="truncate text-[13px] text-muted-foreground">{r.office || r.email}</span></span>
              </span>
              <Sentence tone={s.tone}>{s.text}</Sentence>
            </div>
          )})}
          {!isLoading && reps.length === 0 && (
            <div className="flex flex-wrap items-center gap-x-4 border-b border-[var(--border-subtle)] py-[14px] text-[14px] text-muted-foreground">No reps yet. <Link href="/app/company/reps" className="font-semibold text-[var(--link)]">Invite the first one →</Link></div>
          )}
        </RuleList>
      </div>

      <div className="flex flex-col gap-[14px]">
        <H2>Recent</H2>
        <RuleList>
          {activity.map((a) => <ActivityRow key={a.id} icon={<Send />} text={a.text} when={a.when} />)}
          {reps.filter((r) => r.status === "pending").map((r) => <ActivityRow key={`inv-${r.id}`} icon={<UserPlus />} text={`${r.name} was invited as a rep`} when="" />)}
          {!isLoading && activity.length === 0 && <p className="border-b border-[var(--border-subtle)] py-[14px] text-[14px] text-muted-foreground">Nothing yet.</p>}
        </RuleList>
      </div>
    </div>
  )
}
