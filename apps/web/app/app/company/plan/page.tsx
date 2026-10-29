"use client"

// /app/company/plan — Plan & Seats. Design's company "Plan" (Sponsor v4):
// one row per rep seat, then what agents get, then how billing works.
//
// Adopted with these changes, each to what the API does:
//   * the count, the holders and the history read GET /v1/company/seats;
//     Design's page was "blocked on Decisions #1" — the seat count now exists;
//   * the agents' limits are the plans table's (`agent_plan`), not Design's
//     "10 reports a month"; agents take no seat;
//   * no "Add seats" button and no card row: the seat count is set by
//     TrendyReports and billed outside the app (services/seats.py), so the
//     page says that and gives the address to write to;
//   * "Invite a rep" on an open seat is the admin's only (D-280) and goes to
//     People, where the invite form is.
// The link used to go to the agent billing page, which listed the Free plan's
// features under the company's plan name (D-315).

import Link from "next/link"
import { PageHeader } from "@/components/page-header"
import { RuleList, ListEmpty } from "@/components/ui/list"
import { useCompanyAgents, useCompanyBranding, useCompanyReps, useCompanySeats } from "@/hooks/use-api"
import { Avatar, H2, Sentence } from "@/components/sponsor/shared"
import type { Agent, Rep, SeatSummary } from "@/lib/company-people"
import {
  agentPlanCounts, agentPlanLimits, historyDate, planHeadline, seatPeriodLine, seatRows,
  type AgentPlan, type SeatPeriod,
} from "@/lib/company-plan"

/** Where a company asks for a different seat count (used across the app). */
const SUPPORT = "support@trendyreports.io"

export default function PlanAndSeatsPage() {
  const { data: seatsData, isLoading, error } = useCompanySeats()
  const { data: repsData } = useCompanyReps()
  const { data: agentsData } = useCompanyAgents()
  const { data: brandingData } = useCompanyBranding()
  const primary: string = brandingData?.branding?.primary_color || "var(--agent-primary)"

  if (error) {
    return <p className="text-[16px] text-muted-foreground">{String(error).includes("403") ? "This account isn't on a title company." : "Couldn't load your seats right now."}</p>
  }

  const seats: SeatSummary | null = seatsData?.seats ?? null
  const history: SeatPeriod[] = seatsData?.history ?? []
  const plan: AgentPlan | null = seatsData?.agent_plan ?? null
  const canManage: boolean = seatsData?.can_manage === true
  const reps: Rep[] = repsData?.reps ?? []
  const agents: Agent[] = agentsData?.agents ?? []
  const rows = seatRows(seats, reps)
  const limits = agentPlanLimits(plan)
  const ready = !isLoading && repsData

  return (
    <div className="flex flex-col gap-10">
      <PageHeader
        title="Plan & Seats"
        description={ready ? `${planHeadline(seats, rows.length)}${seats ? " You pay for rep seats; agents take none." : ""}` : undefined}
      />

      <div className="flex flex-col gap-[14px]">
        <H2>Rep seats</H2>
        <RuleList>
          {rows.map((row) => row.kind === "held" ? (
            <div key={row.rep.id} className="grid grid-cols-[72px_minmax(0,1fr)_minmax(0,1.3fr)] items-center gap-5 border-b border-[var(--border-subtle)] py-[13px]">
              <span className="text-[14px] text-muted-foreground">{row.label}</span>
              <span className="flex min-w-0 items-center gap-3">
                <Avatar name={row.rep.name} size={34} color={primary} />
                <span className="flex min-w-0 flex-col leading-[1.3]"><span className="truncate text-[15px] font-semibold text-foreground">{row.rep.name}</span><span className="truncate text-[13px] text-muted-foreground">{row.rep.office || row.rep.email}</span></span>
              </span>
              <Sentence tone={row.tone}>{row.text}</Sentence>
            </div>
          ) : (
            <div key={row.label} className="grid grid-cols-[72px_minmax(0,1fr)_minmax(0,1.3fr)] items-center gap-5 border-b border-[var(--border-subtle)] py-[13px]">
              <span className="text-[14px] text-muted-foreground">{row.label}</span>
              <span className="text-[15px] font-semibold text-muted-foreground">Open</span>
              {canManage
                ? <Link href="/app/company/reps" className="text-[14px] font-semibold text-[var(--link)] hover:text-[var(--link-hover)]">Invite a rep →</Link>
                : <span />}
            </div>
          ))}
          {ready && rows.length === 0 && <ListEmpty>No reps hold a seat yet.</ListEmpty>}
        </RuleList>
      </div>

      <div className="flex flex-col gap-[14px]">
        <H2>Agents</H2>
        <p className="max-w-[640px] text-[16px] leading-[1.55] text-[var(--body)]">
          Agents don&apos;t take a seat. Each agent your reps invite gets their own account
          {plan ? <> on the {plan.plan_name} plan{limits ? <>: {limits}</> : null}</> : null}.
          {" "}Agents who want more upgrade and pay for it themselves.
          {agentsData ? <> {agentPlanCounts(agents, plan)}</> : null}
        </p>
      </div>

      <div className="flex flex-col gap-[14px]">
        <H2>Billing</H2>
        <p className="max-w-[640px] text-[16px] leading-[1.55] text-[var(--body)]">
          {seats ? "Your seat count is set" : "Your plan is set"} by TrendyReports and billed outside the app — there&apos;s no card to manage here.
          {" "}{seats ? "To add or remove seats" : "For questions about your plan"}, email <a href={`mailto:${SUPPORT}?subject=${encodeURIComponent(seats ? "Rep seats" : "Our plan")}`} className="font-semibold text-[var(--link)]">{SUPPORT}</a>.
        </p>
      </div>

      {history.length > 0 && (
        <div className="flex flex-col gap-[14px]">
          <H2>Seat history</H2>
          <RuleList>
            {history.map((h, i) => { const l = seatPeriodLine(h); return (
              <div key={`${h.rep_id}-${i}`} className="grid grid-cols-[minmax(0,1fr)_110px] items-center gap-[18px] border-b border-[var(--border-subtle)] py-[13px]">
                <span className="text-[15px] text-foreground">{l.text}</span>
                <span className="whitespace-nowrap text-right text-[14px] text-muted-foreground">{historyDate(l.at)}</span>
              </div>
            )})}
          </RuleList>
        </div>
      )}
    </div>
  )
}
