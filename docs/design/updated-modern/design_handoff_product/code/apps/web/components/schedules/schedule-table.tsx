"use client"

import { useState } from "react"
import Link from "next/link"
import { Switch } from "@/components/ui/switch"
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu"
import { Ellipsis, Eye, Pencil, Trash2 } from "lucide-react"
import { RuleList, ListHeader, ListRow, Cell, Text, IconButton, ListEmpty } from "@/components/ui/list"
import { type Schedule, reportTypeLabels, dowToWeekday, formatTime12h } from "./types"

export interface ScheduleTableProps {
  schedules: Schedule[]
  onToggleActive?: (id: string, active: boolean) => void
  onView?: (id: string) => void
  onEdit?: (id: string) => void
  onDelete?: (id: string) => void
}

const COLS = "minmax(0,1.6fr) minmax(0,1fr) minmax(0,1.2fr) minmax(0,1.2fr) auto 34px"
const ORD = (n: number) => `${n}${["th", "st", "nd", "rd"][(n % 100 > 10 && n % 100 < 14) ? 0 : n % 10 < 4 ? n % 10 : 0]}`

export function ScheduleTable({ schedules, onToggleActive, onView, onEdit, onDelete }: ScheduleTableProps) {
  const [toggling, setToggling] = useState<string | null>(null)
  const toggle = async (s: Schedule) => { setToggling(s.id); await onToggleActive?.(s.id, !s.active); setToggling(null) }

  const area = (s: Schedule) => s.city || `${s.zip_codes?.length ?? 0} ZIPs`
  const cadence = (s: Schedule) => {
    const t = formatTime12h(s.send_hour, s.send_minute)
    if (s.cadence === "weekly" && s.weekly_dow != null) { const d = dowToWeekday(s.weekly_dow); return `Weekly · ${d[0].toUpperCase()}${d.slice(1, 3)}, ${t}` }
    if (s.cadence === "monthly" && s.monthly_dom) return `Monthly · ${ORD(s.monthly_dom)}, ${t}`
    return "—"
  }
  const nextRun = (s: Schedule) => {
    if (!s.active) return "Paused"
    if (!s.next_run_at) return "—"
    const d = new Date(s.next_run_at), days = Math.floor((d.getTime() - Date.now()) / 86400000)
    if (days === 0) return "Today"
    if (days === 1) return "Tomorrow"
    return d.toLocaleDateString(undefined, { month: "short", day: "numeric" })
  }

  return (
    <div className="flex flex-col gap-8">
      <RuleList>
        <ListHeader columns={COLS} cells={["Schedule", "Area", "Cadence", "Next send", "On", ""]} />
        {schedules.length === 0 ? (
          <ListEmpty>Nothing scheduled. <Link href="/app/schedules/new" prefetch={false} className="font-semibold">Set one up →</Link></ListEmpty>
        ) : schedules.map((s) => (
          <ListRow key={s.id} columns={COLS} className="py-[14px]" style={{ opacity: s.active ? 1 : 0.7 }}>
            <Cell title={<button onClick={() => onView?.(s.id)} className="text-left hover:text-[var(--link)]">{s.name}</button>} sub={`${reportTypeLabels[s.report_type]} · ${s.recipients?.length ?? 0} contacts`} />
            <Text>{area(s)}</Text>
            <Text>{cadence(s)}</Text>
            <Text strong={s.active} muted={!s.active}>{nextRun(s)}</Text>
            <Switch checked={s.active} disabled={toggling === s.id} onCheckedChange={() => toggle(s)} aria-label={`Turn ${s.name} ${s.active ? "off" : "on"}`} />
            <DropdownMenu>
              <DropdownMenuTrigger asChild><span><IconButton label="More"><Ellipsis /></IconButton></span></DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem onClick={() => onView?.(s.id)} className="gap-2"><Eye className="size-4" />View</DropdownMenuItem>
                <DropdownMenuItem onClick={() => onEdit?.(s.id)} className="gap-2"><Pencil className="size-4" />Edit</DropdownMenuItem>
                <DropdownMenuItem onClick={() => onDelete?.(s.id)} className="gap-2 text-[var(--destructive)] focus:text-[var(--destructive)]"><Trash2 className="size-4" />Delete</DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </ListRow>
        ))}
      </RuleList>
      <p className="max-w-[560px] text-[14px] text-muted-foreground [text-wrap:pretty]">Each send uses one report from your monthly allowance. Weekly cadence needs Growth.</p>
    </div>
  )
}
