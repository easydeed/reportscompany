"use client"

// /app/affiliate/schedules — read-only. What the network has going out on
// its own and when. No "New schedule": reps don't author schedules in the
// current product (that's the net-new feature flagged for Jerry).

import { useEffect, useState } from "react"
import Link from "next/link"
import { PageHeader } from "@/components/page-header"
import { RuleList, ListEmpty } from "@/components/ui/list"
import { Avatar, reportTypeLabel, whenLabel } from "@/components/sponsor/shared"

type Row = { id: string; name: string; report_type: string; area: string; cadence: string; active: boolean; next_run_at: string | null; user_name: string; agent_account_id: string; source: "You" | "Agent" }
const COLS = "minmax(0,1fr) minmax(0,1.4fr) 130px"
const CADENCE: Record<string, string> = { daily: "Daily", weekly: "Weekly", monthly: "Monthly", biweekly: "Every other week" }

export default function NetworkSchedulesPage() {
  const [rows, setRows] = useState<Row[] | null>(null)
  useEffect(() => {
    fetch("/api/proxy/v1/affiliate/all-schedules", { credentials: "include" })
      .then((r) => (r.ok ? r.json() : { schedules: [] })).then((d) => setRows((d.schedules ?? []).filter((s: Row) => s.source === "Agent")))
  }, [])

  const running = (rows ?? []).filter((s) => s.active).length
  const agents = new Set((rows ?? []).map((s) => s.agent_account_id)).size
  const description = rows === null ? undefined : rows.length === 0 ? "Nothing going out on its own yet." : `What your agents have going out on their own. ${running} running across ${agents} agent${agents === 1 ? "" : "s"}.`

  return (
    <div className="flex flex-col gap-8">
      <PageHeader title="Schedules" description={description} />
      <RuleList>
        {(rows ?? []).map((s) => (
          <div key={s.id} className="grid items-center gap-[18px] border-b border-[var(--border-subtle)] py-[14px] transition-colors hover:bg-[var(--surface-cream)]" style={{ gridTemplateColumns: COLS }}>
            <span className="flex min-w-0 items-center gap-[10px]">
              <Avatar name={s.user_name || "?"} size={30} />
              <Link href={`/app/affiliate/agents/${s.agent_account_id}`} className="text-[15px] font-semibold text-foreground hover:text-[var(--link)]">{s.user_name || "An agent"}</Link>
            </span>
            <span className="flex min-w-0 flex-col leading-[1.3]">
              <span className="text-[15px] text-foreground">{s.area === "Unknown" ? "" : `${s.area} · `}{reportTypeLabel(s.report_type)}</span>
              <span className="text-[13px] text-muted-foreground">{CADENCE[s.cadence] ?? s.cadence}</span>
            </span>
            <span className={`whitespace-nowrap text-right text-[14px] ${s.active ? "text-[var(--body)]" : "text-[var(--warning-foreground)]"}`}>{s.active ? `Next ${whenLabel(s.next_run_at) || "—"}` : "Paused"}</span>
          </div>
        ))}
        {rows && rows.length === 0 && <ListEmpty>Your agents haven't set anything to repeat.</ListEmpty>}
      </RuleList>
      <p className="text-[14px] text-muted-foreground">These are the agents' schedules — you can see them, not change them.</p>
    </div>
  )
}
