"use client"

// /app/company/agents — every agent under the company's reps: People's "All N
// agents →" overflow, restyled as the rule list Design's package asks for.
//
// The page it replaces read fields /v1/company/agents never returned
// (`name`, `brokerage`, `rep_id`, `last_active`, a `reps` list) and crashed on
// its first row (D-311); its ?rep= filter matched nothing (D-276); its row menu
// offered "Resend Invite" and "Remove from Company" with no handler (D-302).
// This reads what the API returns, filters by `rep_id`, and offers no action
// the company has no endpoint for: an agent belongs to their rep's book.

import { Suspense, useMemo, useState } from "react"
import Link from "next/link"
import { useSearchParams } from "next/navigation"
import { PageHeader } from "@/components/page-header"
import { RuleList, ListEmpty, FilterPills } from "@/components/ui/list"
import { useCompanyAgents } from "@/hooks/use-api"
import { Avatar } from "@/components/sponsor/shared"
import { AGENT_STATUS, agentSentence, type Agent, type RepStatus } from "@/lib/company-people"

type Filter = "all" | RepStatus

function AgentsList() {
  const rep = useSearchParams().get("rep")
  const { data, isLoading, error } = useCompanyAgents()
  const [filter, setFilter] = useState<Filter>("all")

  const all: Agent[] = data?.agents ?? []
  const mine = useMemo(() => (rep ? all.filter((a) => a.rep_id === rep) : all), [all, rep])
  const shown = filter === "all" ? mine : mine.filter((a) => a.status === filter)
  const repName = rep ? mine[0]?.rep_name : null

  if (error) {
    return <p className="text-[16px] text-muted-foreground">{String(error).includes("403") ? "This account isn't a title-company admin." : "Couldn't load the agents right now."}</p>
  }

  return (
    <div className="flex flex-col gap-8">
      <Link href="/app/company/reps" className="self-start text-[14px] font-semibold text-[var(--link)]">← People</Link>
      <PageHeader
        title={repName ? `${repName}'s agents` : "All agents"}
        description={isLoading ? undefined : `${mine.length} agent${mine.length === 1 ? "" : "s"}${rep ? "" : " across your reps"}. Agents belong to their rep's book; their rep invites and manages them.`}
      />
      <FilterPills<Filter>
        value={filter}
        onChange={setFilter}
        options={[
          { value: "all", label: "Everyone" },
          { value: "active", label: "Active" },
          { value: "pending", label: "Invited" },
          { value: "deactivated", label: "Switched off" },
        ]}
      />
      <RuleList>
        {shown.map((a) => (
          <div key={a.agent_id} className="grid grid-cols-[minmax(0,1.3fr)_minmax(0,0.9fr)_110px_minmax(0,1fr)] items-center gap-5 border-b border-[var(--border-subtle)] py-[13px]">
            <span className="flex min-w-0 items-center gap-3">
              <Avatar name={a.agent_name} size={34} />
              <span className="flex min-w-0 flex-col leading-[1.3]"><span className="truncate text-[15px] font-semibold text-foreground">{a.agent_name}</span><span className="truncate text-[13px] text-muted-foreground">{a.email}</span></span>
            </span>
            <span className="truncate text-[14px] text-[var(--body)]">{rep ? `${a.reports_this_month} report${a.reports_this_month === 1 ? "" : "s"} this month` : a.rep_name}</span>
            <span className={`text-[13px] font-semibold ${AGENT_STATUS[a.status].cls}`}>{AGENT_STATUS[a.status].label}</span>
            <span className="text-[14px] text-[var(--body)]">{agentSentence(a)}</span>
          </div>
        ))}
        {!isLoading && shown.length === 0 && <ListEmpty>{mine.length ? "No one matches that filter." : "No agents yet."}</ListEmpty>}
      </RuleList>
    </div>
  )
}

export default function AgentsPage() {
  // useSearchParams needs a Suspense boundary in the app router.
  return <Suspense fallback={null}><AgentsList /></Suspense>
}
