"use client"

// /app/affiliate/reports — a feed of what the network sent. One line per
// report: who, what, where, when. Not a report browser: no PDF column, no
// status badges, no metric tiles, no search. Filters are who-sent-it.

import { useEffect, useState } from "react"
import Link from "next/link"
import { PageHeader } from "@/components/page-header"
import { FilterPills, RuleList, ListEmpty } from "@/components/ui/list"
import { Avatar, reportTypeLabel, whenLabel } from "@/components/sponsor/shared"

type Row = { id: string; report_type: string; status: string; generated_at: string | null; city: string; user_name: string; agent_account_id: string; source: "You" | "Agent" }
type Who = "agents" | "mine" | "all"
const COLS = "minmax(0,1.1fr) minmax(0,1.3fr) 110px"

export default function NetworkReportsPage() {
  const [rows, setRows] = useState<Row[] | null>(null)
  const [who, setWho] = useState<Who>("agents")

  useEffect(() => {
    fetch("/api/proxy/v1/affiliate/all-reports?limit=100", { credentials: "include" })
      .then((r) => (r.ok ? r.json() : { reports: [] })).then((d) => setRows(d.reports ?? []))
  }, [])

  const sent = (rows ?? []).filter((r) => r.status === "completed" || r.status === "complete" || r.status === "processing")
  const shown = sent.filter((r) => who === "all" || (who === "mine" ? r.source === "You" : r.source === "Agent"))
  const monthStart = new Date(); monthStart.setDate(1); monthStart.setHours(0, 0, 0, 0)
  const byAgentsThisMonth = sent.filter((r) => r.source === "Agent" && r.generated_at && new Date(r.generated_at) >= monthStart).length
  const mineThisMonth = sent.filter((r) => r.source === "You" && r.generated_at && new Date(r.generated_at) >= monthStart).length

  const description = rows === null ? undefined
    : who === "mine" ? `${mineThisMonth} this month, run by you.`
    : `${byAgentsThisMonth} sent by your agents this month.`

  return (
    <div className="flex flex-col gap-8">
      <PageHeader title="Reports" description={description} />
      <FilterPills<Who> value={who} onChange={setWho} options={[{ value: "agents", label: "My agents'" }, { value: "mine", label: "Mine" }, { value: "all", label: "Everything" }]} />
      <RuleList>
        {shown.map((r) => {
          const name = r.source === "You" ? "You" : r.user_name || "An agent"
          const Name = r.source === "Agent"
            ? <Link href={`/app/affiliate/agents/${r.agent_account_id}`} className="truncate text-[15px] font-semibold text-foreground hover:text-[var(--link)]">{name}</Link>
            : <span className="truncate text-[15px] font-semibold text-foreground">{name}</span>
          return (
            <div key={r.id} className="grid items-center gap-[18px] border-b border-[var(--border-subtle)] py-[13px] transition-colors hover:bg-[var(--surface-cream)]" style={{ gridTemplateColumns: COLS }}>
              <span className="flex min-w-0 items-center gap-[10px]"><Avatar name={r.user_name || name} size={30} />{Name}</span>
              <span className="truncate text-[15px] text-foreground">{r.city === "Unknown" ? "" : `${r.city} · `}{reportTypeLabel(r.report_type)}</span>
              <span className="whitespace-nowrap text-[14px] text-muted-foreground">{whenLabel(r.generated_at)}</span>
            </div>
          )
        })}
        {rows && shown.length === 0 && <ListEmpty>{who === "mine" ? "You haven't run a report yet." : "Your agents haven't sent anything yet."}</ListEmpty>}
      </RuleList>
      <p className="text-[14px] text-muted-foreground">You see that a report went out. The report itself belongs to the agent.</p>
    </div>
  )
}
