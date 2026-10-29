"use client"

// /app/affiliate/schedules — the schedules in the rep's book. Design's rep
// Schedules (Sponsor v4): who, what and where, when it sends, next or paused.
// No toggles, no New schedule: they are the agents' schedules.
//
// The page it replaces showed no agent, no area and no run count — it read
// fields GET /v1/affiliate/all-schedules never returned (D-324).

import { useState } from "react"
import Link from "next/link"
import { PageHeader } from "@/components/page-header"
import { FilterPills, ListEmpty, RuleList } from "@/components/ui/list"
import { useRepSchedules } from "@/hooks/use-api"
import { Avatar, Sentence } from "@/components/sponsor/shared"
import { bySource, scheduleNext, scheduleWhat, scheduleWhen, type RepSchedule, type SourceFilter } from "@/lib/rep-book"

export default function RepSchedulesPage() {
  const [filter, setFilter] = useState<SourceFilter>("agents")
  const { data, isLoading, error } = useRepSchedules()

  if (error) return <p className="text-[16px] text-muted-foreground">{String(error).includes("403") ? "This account isn't a rep's." : "Couldn't load the schedules right now."}</p>

  const all: RepSchedule[] = data?.schedules ?? []
  const rows = bySource(all, filter)

  return (
    <div className="flex flex-col gap-8">
      <PageHeader title="Schedules" description="Reports set to go out on their own, from your agents and from you." />
      <FilterPills<SourceFilter> value={filter} onChange={setFilter} options={[
        { value: "agents", label: "My agents'" }, { value: "mine", label: "Mine" }, { value: "all", label: "Everything" },
      ]} />
      <div className="flex flex-col gap-4">
        <RuleList>
          {rows.map((s) => { const nx = scheduleNext(s); const name = s.source === "You" ? "You" : s.user_name || "An agent"; return (
            <div key={s.id} className="grid grid-cols-[minmax(0,1.1fr)_minmax(0,1fr)_minmax(0,1.1fr)_150px] items-center gap-5 border-b border-[var(--border-subtle)] py-[13px]">
              <span className="flex min-w-0 items-center gap-3">
                <Avatar name={name} size={34} />
                {s.source === "Agent"
                  ? <Link href={`/app/affiliate/agents/${s.agent_account_id}`} className="truncate text-[15px] font-semibold text-foreground hover:text-[var(--link)]">{name}</Link>
                  : <span className="truncate text-[15px] font-semibold text-foreground">{name}</span>}
              </span>
              <span className="flex min-w-0 flex-col leading-[1.3]"><span className="truncate text-[15px] text-foreground">{scheduleWhat(s)}</span><span className="truncate text-[13px] text-muted-foreground">{s.name}</span></span>
              <span className="text-[14px] text-[var(--body)]">{scheduleWhen(s)}</span>
              <Sentence tone={nx.tone}>{nx.text}</Sentence>
            </div>
          )})}
          {!isLoading && rows.length === 0 && <ListEmpty>{all.length ? "Nothing here under that filter." : "No schedules yet."}</ListEmpty>}
        </RuleList>
        <p className="text-[14px] text-muted-foreground">These are your agents&apos; own schedules — you can see them, not change them.</p>
      </div>
    </div>
  )
}
