"use client"

// /app/affiliate/leads — the homeowner leads the rep's agents bring in.
// Design's leads tweak (Sponsor v4, Decisions #2): a count per agent and a
// feed, read-only, no lead's name, email, phone, message or address — the
// lead belongs to the agent. Each row says where it came from: the agent's
// property report page (QR code and link alike, D-325) or home-value page.
// GET /v1/affiliate/leads reads rows the agents' own pages wrote; nothing is
// captured here.

import { Suspense } from "react"
import Link from "next/link"
import { useRouter, useSearchParams } from "next/navigation"
import { PageHeader } from "@/components/page-header"
import { ListEmpty, RuleList } from "@/components/ui/list"
import { useBookLeads } from "@/hooks/use-api"
import { ActivityRow, Avatar, H2, whenLabel } from "@/components/sponsor/shared"
import { UserPlus } from "lucide-react"
import { cameFrom, leadsHeadline, type AgentLeadCount, type BookLead } from "@/lib/rep-book"

function Leads() {
  const params = useSearchParams()
  const router = useRouter()
  const agent = params.get("agent")
  const { data: all, isLoading, error } = useBookLeads(null)
  const { data: one } = useBookLeads(agent)

  if (error) return <p className="text-[16px] text-muted-foreground">{String(error).includes("403") ? "This account isn't a rep's." : "Couldn't load the leads right now."}</p>

  const counts: AgentLeadCount[] = all?.agents ?? []
  const feed: BookLead[] = (agent ? one?.leads : all?.leads) ?? []
  const agentName = agent ? counts.find((c) => c.agent_account_id === agent)?.agent_name : null

  return (
    <div className="flex flex-col gap-9">
      <PageHeader title="Leads" description={all ? leadsHeadline(all) : undefined} />

      <div className="flex flex-col gap-[14px]">
        <H2>By agent</H2>
        <RuleList>
          <div className="grid grid-cols-[minmax(0,1.4fr)_100px_100px_80px] gap-5 border-b border-[var(--border-subtle)] py-2 text-[13px] text-muted-foreground">
            <span>Agent</span><span className="text-right">This month</span><span className="text-right">Last month</span><span className="text-right">In all</span>
          </div>
          {counts.map((c) => (
            <button key={c.agent_account_id} type="button" onClick={() => router.replace(agent === c.agent_account_id ? "/app/affiliate/leads" : `/app/affiliate/leads?agent=${c.agent_account_id}`)}
              className={`grid w-full grid-cols-[minmax(0,1.4fr)_100px_100px_80px] items-center gap-5 border-b border-[var(--border-subtle)] py-[12px] text-left ${agent === c.agent_account_id ? "bg-[var(--surface-cream)]" : ""}`}>
              <span className="flex min-w-0 items-center gap-3"><Avatar name={c.agent_name} size={30} /><span className="truncate text-[15px] font-semibold text-foreground">{c.agent_name}</span></span>
              <span className={`text-right text-[15px] tabular-nums ${c.this_month ? "font-semibold text-[var(--success-foreground)]" : "text-[var(--body)]"}`}>{c.this_month}</span>
              <span className="text-right text-[15px] tabular-nums text-[var(--body)]">{c.last_month}</span>
              <span className="text-right text-[15px] tabular-nums text-[var(--body)]">{c.total}</span>
            </button>
          ))}
          {!isLoading && counts.length === 0 && <ListEmpty>No agents in your book yet.</ListEmpty>}
        </RuleList>
      </div>

      <div className="flex flex-col gap-[14px]">
        <H2 linkLabel={agent ? "Everyone →" : undefined} href={agent ? "/app/affiliate/leads" : undefined}>{agentName ? `${agentName}'s leads` : "Recent"}</H2>
        <RuleList>
          {feed.map((l) => (
            <ActivityRow key={l.id} icon={<UserPlus />} tone="good"
              text={<><Link href={`/app/affiliate/agents/${l.agent_account_id}`} className="font-semibold hover:text-[var(--link)]">{l.agent_name || "An agent"}</Link> got a homeowner lead {cameFrom(l.came_from)}</>}
              when={whenLabel(l.created_at)} />
          ))}
          {!isLoading && feed.length === 0 && <ListEmpty>No leads yet.</ListEmpty>}
        </RuleList>
        <p className="text-[14px] text-muted-foreground">Counts and where they came from only. Who the homeowner is stays with the agent.</p>
      </div>
    </div>
  )
}

export default function RepLeadsPage() {
  // useSearchParams needs a Suspense boundary in the app router.
  return <Suspense fallback={null}><Leads /></Suspense>
}
