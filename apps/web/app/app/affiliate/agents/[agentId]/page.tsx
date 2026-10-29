"use client"

// /app/affiliate/agents/[agentId] — one agent in the rep's book. Design's rep
// Person (Sponsor v4): who they are and where they stand as one sentence,
// three plain numbers, what they've been doing, what goes out on its own,
// and the homeowner leads their pages brought in.
//
// The page it replaces read a name, email and status from
// /agents/{id}/usage, which returns plan usage and none of those, so its
// header was blank, and its rows read fields the reports and schedules
// endpoints never returned (D-324). The header now reads GET
// /v1/affiliate/agents/{id}. Leads are counts and where they came from: who
// the homeowner is stays with the agent. A finished report keeps its PDF
// link (Jerry: keep).

import { useParams } from "next/navigation"
import Link from "next/link"
import { useBookAgent, useBookAgentReports, useBookAgentSchedules, useBookLeads } from "@/hooks/use-api"
import { RuleList } from "@/components/ui/list"
import { ActivityRow, Avatar, H2, Sentence, StatCell, whenLabel } from "@/components/sponsor/shared"
import { FileText, Send, UserPlus } from "lucide-react"
import {
  agentSentence, cameFrom, madeLine, pdfFor, reportState, reportsOfPlan, scheduleNext, scheduleWhat, scheduleWhen,
  type AgentReport, type AgentSchedule, type BookAgent, type BookLead, type LeadCounts,
} from "@/lib/rep-book"

export default function BookAgentPage() {
  const { agentId } = useParams<{ agentId: string }>()
  const { data, isLoading, error } = useBookAgent(agentId)
  const { data: reportsData } = useBookAgentReports(agentId)
  const { data: schedulesData } = useBookAgentSchedules(agentId)
  const { data: leadsData } = useBookLeads(agentId)

  if (error) {
    return (
      <div className="flex flex-col gap-4">
        <Link href="/app/affiliate" className="self-start text-[14px] font-semibold text-[var(--link)]">← My agents</Link>
        <p className="text-[16px] text-muted-foreground">{String(error).includes("403") ? "This agent isn't in your book." : "Couldn't load this agent right now."}</p>
      </div>
    )
  }

  const a: BookAgent | undefined = data?.agent
  const leads: LeadCounts | undefined = data?.leads
  const reports: AgentReport[] = reportsData?.reports ?? []
  const schedules: AgentSchedule[] = schedulesData?.schedules ?? []
  const leadRows: BookLead[] = leadsData?.leads ?? []
  const s = a ? agentSentence(a) : null
  const first = a?.name.split(" ")[0] || "this agent"

  return (
    <div className="flex flex-col gap-9">
      <Link href="/app/affiliate" className="self-start text-[14px] font-semibold text-[var(--link)]">← My agents</Link>

      <div className="flex items-center gap-4">
        <Avatar name={a?.name || "?"} size={56} />
        <div className="flex min-w-0 flex-col gap-1">
          <h1 className="truncate text-[30px] font-extrabold leading-[1.1] tracking-[-0.03em] text-foreground">{isLoading ? " " : a?.name}</h1>
          {a?.email && <a href={`mailto:${a.email}`} className="truncate text-[15px] text-[var(--link)]">{a.email}</a>}
        </div>
      </div>

      {s && <div className="rounded-xl bg-[var(--surface-cream)] px-5 py-4"><Sentence tone={s.tone} size={17}>{s.text}</Sentence></div>}

      {a && a.status !== "pending" && (
        <div className="grid grid-cols-[repeat(auto-fit,minmax(200px,1fr))] gap-4">
          <StatCell label="Reports this month" value={String(a.market_reports_used)} sub={reportsOfPlan(a)} />
          <StatCell label="Last report" value={a.last_report_at ? whenLabel(a.last_report_at) : "None yet"} />
          <StatCell label="Homeowner leads this month" value={String(leads?.this_month ?? 0)}
            sub={leads ? `${leads.last_month} last month · ${leads.total} in all` : undefined} subTone={leads && leads.this_month > 0 ? "good" : "muted"} />
        </div>
      )}

      <div className="flex flex-col gap-[14px]">
        <H2>What {first} has been doing</H2>
        <RuleList>
          {reports.map((r) => { const st = reportState(r.status); const pdf = pdfFor(r); return (
            <ActivityRow key={r.id} icon={r.is_scheduled ? <Send /> : <FileText />}
              text={<span className="flex flex-wrap items-center gap-x-3">{madeLine(r)}{st.text !== "Made" && <Sentence tone={st.tone}>{st.text}</Sentence>}{pdf && <a href={pdf} target="_blank" rel="noopener noreferrer" className="text-[14px] font-semibold text-[var(--link)]">PDF</a>}</span>}
              when={whenLabel(r.generated_at)} />
          )})}
          {a?.joined_at && a.status !== "pending" && <ActivityRow icon={<UserPlus />} text="Joined" when={whenLabel(a.joined_at)} />}
          {reportsData && reports.length === 0 && <p className="border-b border-[var(--border-subtle)] py-[13px] text-[14px] text-muted-foreground">No reports yet.</p>}
        </RuleList>
      </div>

      {schedules.length > 0 && (
        <div className="flex flex-col gap-[14px]">
          <H2>Going out on its own</H2>
          <RuleList>
            {schedules.map((sc) => { const nx = scheduleNext(sc); return (
              <div key={sc.id} className="grid grid-cols-[minmax(0,1fr)_minmax(0,1.1fr)_150px] items-center gap-5 border-b border-[var(--border-subtle)] py-[13px]">
                <span className="flex min-w-0 flex-col leading-[1.3]"><span className="truncate text-[15px] text-foreground">{scheduleWhat(sc)}</span><span className="truncate text-[13px] text-muted-foreground">To {sc.recipient_count} {sc.recipient_count === 1 ? "recipient" : "recipients"}</span></span>
                <span className="text-[14px] text-[var(--body)]">{scheduleWhen(sc)}</span>
                <Sentence tone={nx.tone}>{nx.text}</Sentence>
              </div>
            )})}
          </RuleList>
        </div>
      )}

      <div className="flex flex-col gap-[14px]">
        <H2>Homeowner leads</H2>
        <RuleList>
          {leadRows.map((l) => <ActivityRow key={l.id} icon={<UserPlus />} tone="good" text={`A homeowner lead ${cameFrom(l.came_from)}`} when={whenLabel(l.created_at)} />)}
          {leadsData && leadRows.length === 0 && <p className="border-b border-[var(--border-subtle)] py-[13px] text-[14px] text-muted-foreground">No leads yet.</p>}
        </RuleList>
        <p className="text-[14px] text-muted-foreground">You see that reports went out and leads came in. Who the homeowners are stays with {first}.</p>
      </div>
    </div>
  )
}
