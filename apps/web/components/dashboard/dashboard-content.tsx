"use client"

// Dashboard — App v3. A sentence, the latest report as an object, then
// Next send / Call these first / Recent in the second column. First-run
// state arrives from onboarding as ?from=onboarding&city=&autopilot=.

import Link from "next/link"
import { useSearchParams } from "next/navigation"
import { Check, Download, Share2, Upload, Link2, ImagePlus, ArrowRight, Plus } from "lucide-react"
import { Skeleton } from "@/components/ui/skeleton"
import { StatusBadge } from "@/components/status-badge"
import { SectionLabel, RuleList, ListEmpty } from "@/components/ui/list"
import { ReportThumb } from "@/components/shared/report-thumb"
import { useUsage, usePlanUsage, useSchedules, useAllLeads, useBranding, useMe } from "@/hooks/use-api"
import type { PreviewReportType } from "@/components/shared/email-preview/sample-data"

const KIND_TITLE: Record<string, string> = {
  market_snapshot: "Market Snapshot", closed: "Closed Sales", new_listings: "New Listings", new_listings_gallery: "New Listings",
  inventory: "Active Inventory", price_bands: "Price Bands", featured_listings: "Featured Listings", open_houses: "Open Houses",
}

function rel(ts?: string) {
  if (!ts) return ""
  const d = (Date.now() - new Date(ts).getTime()) / 60000
  if (d < 1) return "Just now"
  if (d < 60) return `${Math.floor(d)}m ago`
  if (d < 1440) return `${Math.floor(d / 60)}h ago`
  if (d < 10080) return `${Math.floor(d / 1440)}d ago`
  return new Date(ts).toLocaleDateString(undefined, { month: "short", day: "numeric" })
}
const fmtDate = (ts: string, time = false) => new Date(ts).toLocaleString(undefined, { month: "short", day: "numeric", ...(time ? { hour: "numeric", minute: "2-digit" } : {}) })
const greeting = () => { const h = new Date().getHours(); return h < 12 ? "Good morning" : h < 17 ? "Good afternoon" : "Good evening" }

export function DashboardContent() {
  const params = useSearchParams()
  const firstRun = params.get("from") === "onboarding"
  const firstCity = params.get("city") || undefined
  const autopilot = params.get("autopilot") !== "0"

  const { data: usage, isLoading: l1 } = useUsage()
  const { data: planUsage, isLoading: l2 } = usePlanUsage()
  const { data: schedulesData } = useSchedules()
  const { data: leadsData } = useAllLeads()
  const { data: brandingData } = useBranding()
  const { data: meData } = useMe()
  const loading = l1 || l2

  const me: any = meData ?? {}
  const branding: any = brandingData ?? {}
  const primary = branding.primary_color ?? "#4F46E5"
  const accent = branding.accent_color ?? "#D97706"

  const reports: any[] = usage?.recent_reports ?? []
  const emails: any[] = usage?.recent_emails ?? []
  const latest = reports[0] ?? null
  const latestKind = KIND_TITLE[latest?.type] ?? (latest?.type ?? "").replace(/_/g, " ")

  const schedules: any[] = Array.isArray(schedulesData) ? schedulesData : (schedulesData as any)?.schedules ?? []
  const next = schedules.filter((s) => s?.active && s?.next_run_at && new Date(s.next_run_at) > new Date()).sort((a, b) => a.next_run_at.localeCompare(b.next_run_at))[0] ?? null
  const nextRecipients = Array.isArray(next?.recipients) ? next.recipients.length : null

  const leads: any[] = Array.isArray(leadsData) ? leadsData : (leadsData as any)?.leads ?? []
  const callFirst = leads.filter((l) => (l?.status ?? "new") === "new").sort((a, b) => (b.created_at ?? "").localeCompare(a.created_at ?? "")).slice(0, 4)

  // Every number in the sentence is derived; any missing part drops its clause.
  const limit = planUsage?.plan?.market_reports_limit
  const used = planUsage?.usage?.market_reports_used
  const planName = planUsage?.plan?.plan_name
  const remaining = typeof limit === "number" && typeof used === "number" && limit < 999 ? Math.max(limit - used, 0) : null
  const firstName = me.first_name as string | undefined

  let title: string, lead: React.ReactNode
  if (firstRun) {
    title = `Your ${firstCity ?? ""} Snapshot is in your inbox.`.replace("  ", " ")
    lead = autopilot
      ? <>Autopilot is on. The next one goes to <strong className="font-semibold text-foreground">{next ? `${next.name} on ${fmtDate(next.next_run_at)}` : "your sphere next month"}</strong> — import your contacts before then.</>
      : <>Autopilot is off. Turn it on from <strong className="font-semibold text-foreground">Schedules</strong> whenever you're ready.</>
  } else {
    title = firstName ? `${greeting()}, ${firstName}.` : "Overview"
    const parts: React.ReactNode[] = []
    if (next) parts.push(<span key="n">Your <strong className="font-semibold text-foreground">{next.name}</strong> goes out {fmtDate(next.next_run_at)}{nextRecipients ? ` to ${nextRecipients} contacts` : ""}.</span>)
    else if (!loading) parts.push(<span key="n">Nothing is scheduled. <Link href="/app/schedules/new" prefetch={false} className="font-semibold">Set one up</Link> and your sphere hears from you monthly.</span>)
    if (remaining !== null && planName) parts.push(<span key="r"> {remaining} report{remaining === 1 ? "" : "s"} left this month on {planName}.</span>)
    lead = parts
  }

  const previewProps = { primaryColor: primary, accentColor: accent, lookbackDays: 30 }

  const activity = [
    ...reports.map((r) => ({ id: `r-${r.id}`, title: `${KIND_TITLE[r.type] ?? r.type} · ${r.city ?? "—"}`, sub: r.status === "completed" ? "PDF ready" : r.status, ts: r.created_at })),
    ...emails.map((e) => ({ id: `e-${e.id}`, title: e.subject || "Email sent", sub: e.to ?? "", ts: e.created_at })),
  ].sort((a, b) => (b.ts ?? "").localeCompare(a.ts ?? "")).slice(0, 4)

  return (
    <div className="flex flex-col gap-9">
      <div className="flex flex-col gap-2">
        {firstRun && (
          <span className="mb-1.5 inline-flex items-center gap-2 self-start rounded-full bg-[var(--success-muted)] px-3 py-1.5 text-[13px] font-semibold text-[var(--success-foreground)]">
            <Check className="size-3.5 text-[var(--success-strong)]" />You're set up
          </span>
        )}
        {loading && !firstRun ? <Skeleton className="h-9 w-72" /> : (
          <h1 className="text-[34px] font-extrabold leading-[1.1] tracking-[-0.03em] [text-wrap:balance]">{title}</h1>
        )}
        <p className="text-[17px] text-[var(--secondary-foreground)] [text-wrap:pretty]">{lead}</p>
      </div>

      <div className="grid items-start gap-10" style={{ gridTemplateColumns: "repeat(auto-fit, minmax(min(100%, 400px), 1fr))" }}>
        {/* Latest report */}
        <div className="flex flex-col gap-[18px]">
          <SectionLabel href="/app/reports" linkLabel="All reports →">Latest report</SectionLabel>
          {loading ? <Skeleton className="h-[520px] w-full rounded-xl" /> : latest ? (
            <>
              <div className="relative h-[520px]">
                <div className="absolute left-1/2 top-[14px] -translate-x-1/2">
                  <ReportThumb width={360} tilt={-2} {...previewProps} reportType={(latest.type ?? "market_snapshot") as PreviewReportType} areaName={latest.city ?? ""} />
                </div>
              </div>
              <div className="flex flex-wrap items-center justify-between gap-4">
                <div className="flex flex-col">
                  <span className="text-[16px] font-bold">{latestKind} · {latest.city}</span>
                  <span className="text-[14px] text-muted-foreground">{firstRun ? "Sent to you just now · live MLS data" : `${fmtDate(latest.created_at)} · ${rel(latest.created_at)}`}</span>
                </div>
                <div className="flex gap-2">
                  {latest.pdf_url && <a href={latest.pdf_url} target="_blank" rel="noopener noreferrer" className="inline-flex h-[38px] items-center gap-[7px] rounded-lg border border-[var(--border-strong)] px-[14px] text-[14px] font-semibold text-foreground hover:bg-[var(--surface-cream)] hover:text-foreground"><Download className="size-[15px]" />PDF</a>}
                  <a href={`/social/${latest.id}`} target="_blank" rel="noopener noreferrer" className="inline-flex h-[38px] items-center gap-[7px] rounded-lg border border-[var(--border-strong)] px-[14px] text-[14px] font-semibold text-foreground hover:bg-[var(--surface-cream)] hover:text-foreground"><Share2 className="size-[15px]" />Share</a>
                </div>
              </div>
            </>
          ) : (
            <RuleList>
              <ListEmpty>
                Nothing sent yet.
                <Link href="/app/reports/new" prefetch={false} className="inline-flex h-[38px] items-center gap-2 rounded-lg bg-primary px-4 text-[14px] font-semibold text-primary-foreground hover:text-primary-foreground"><Plus className="size-4" />Your first report</Link>
              </ListEmpty>
            </RuleList>
          )}
        </div>

        <div className="flex flex-col gap-9">
          {/* Next send */}
          <div className="flex flex-col gap-[14px]">
            <SectionLabel>Next send</SectionLabel>
            <div className="flex items-center gap-[14px] rounded-[14px] border border-[var(--border-subtle)] bg-[var(--surface-cream)] px-5 py-[18px]">
              <span className="size-3 shrink-0 rounded-full" style={{ background: next ? "var(--success)" : "var(--placeholder)", boxShadow: `0 0 0 5px ${next ? "var(--success-muted)" : "var(--neutral-muted)"}` }} />
              <div className="flex min-w-0 flex-col gap-0.5">
                <span className="truncate text-[16px] font-bold">{next ? `${next.name} → ${nextRecipients !== null ? `${nextRecipients} contacts` : "your sphere"}` : "Nothing scheduled"}</span>
                <span className="text-[14px] text-muted-foreground">{next ? fmtDate(next.next_run_at, true) : "Your sphere won't hear from you automatically"}</span>
              </div>
              <Link href={next ? `/app/schedules/${next.id}` : "/app/schedules/new"} prefetch={false} className="ml-auto whitespace-nowrap text-[14px] font-semibold text-[var(--link)] hover:text-[var(--link-hover)]">{next ? "Edit" : "Turn on"}</Link>
            </div>
          </div>

          {/* First steps (first run only) */}
          {firstRun && (
            <div className="flex flex-col gap-[14px]">
              <SectionLabel>Before the first send</SectionLabel>
              <RuleList>
                {[
                  { icon: Upload, t: "Import your contacts", sub: "CSV from your CRM. Groups come along.", href: "/app/people" },
                  { icon: Link2, t: "Set up your home-value page", sub: "One link for your signature and signs", href: "/app/lead-page" },
                  { icon: ImagePlus, t: "Add your logo", sub: "Your name is on the reports until you do", href: "/app/settings/branding" },
                ].map((f) => (
                  <Link key={f.href} href={f.href} prefetch={false} className="grid grid-cols-[auto_minmax(0,1fr)_auto] items-center gap-[14px] border-b border-[var(--border-subtle)] py-[13px] text-foreground hover:text-[var(--link)]">
                    <span className="flex size-9 items-center justify-center rounded-[9px] border border-[var(--border-subtle)] bg-[var(--surface-cream)]"><f.icon className="size-4 text-foreground" /></span>
                    <span className="flex flex-col"><span className="text-[15px] font-semibold">{f.t}</span><span className="text-[13px] text-muted-foreground">{f.sub}</span></span>
                    <ArrowRight className="size-4 text-[var(--placeholder)]" />
                  </Link>
                ))}
              </RuleList>
            </div>
          )}

          {/* Call these first */}
          <div className="flex flex-col gap-[14px]">
            <SectionLabel href="/app/people" linkLabel="All contacts →">{firstRun ? "Who opened" : "Call these first"}</SectionLabel>
            <RuleList>
              {callFirst.length === 0 ? (
                <ListEmpty>{firstRun ? "No contacts yet. Who opens shows up here the morning after each send." : "No one to call yet. Opens and new leads show up here."}</ListEmpty>
              ) : callFirst.map((l) => {
                const name: string = l.name || l.email || "Unnamed lead"
                const ini = name.split(" ").map((w: string) => w[0]).join("").slice(0, 2).toUpperCase()
                return (
                  <div key={l.id} className="grid grid-cols-[40px_minmax(0,1fr)_auto] items-center gap-[14px] border-b border-[var(--border-subtle)] py-3">
                    <span className="flex size-10 items-center justify-center rounded-full text-[13px] font-bold text-white" style={{ background: primary }}>{ini}</span>
                    <div className="flex min-w-0 flex-col"><span className="truncate text-[15px] font-semibold">{name}</span><span className="truncate text-[13px] text-muted-foreground">{l.phone || l.email || "—"}</span></div>
                    <StatusBadge status={l.status ?? "lead"} accent={accent} />
                  </div>
                )
              })}
            </RuleList>
          </div>

          {/* Recent */}
          <div className="flex flex-col gap-[14px]">
            <SectionLabel>Recent</SectionLabel>
            <RuleList>
              {activity.length === 0 ? <ListEmpty>Nothing yet.</ListEmpty> : activity.map((a) => (
                <div key={a.id} className="grid grid-cols-[minmax(0,1fr)_auto] items-center gap-[14px] border-b border-[var(--border-subtle)] py-[11px]">
                  <div className="flex min-w-0 flex-col"><span className="truncate text-[15px] font-semibold">{a.title}</span><span className="truncate text-[13px] text-muted-foreground">{a.sub}</span></div>
                  <span className="whitespace-nowrap text-[13px] text-muted-foreground">{rel(a.ts)}</span>
                </div>
              ))}
            </RuleList>
          </div>
        </div>
      </div>
    </div>
  )
}
