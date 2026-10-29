"use client"

// /app/company/branding — Branding. Design's company Branding (Sponsor v4): a
// rule list of what the company sets, a live report page beside it, and what
// each rep adds.
//
// Adopted with these changes, each to what the code does:
//   * two logos, not one: the reports and emails use a logo on the brand
//     colour (`logo_url`) and one on white (`footer_logo_url`, which falls back
//     to the first) — dropping the second would leave an old logo in every
//     footer after a Replace;
//   * the second colour stays: the market report reads `accent_color`;
//   * Design's "your colour is never changed to fix contrast" is not what the
//     report does — `MarketReportBuilder._masthead_band` darkens a colour
//     until white text on it reads (D-112) — so the page says that instead;
//   * Replace, never Remove: the PATCH keeps a field sent as null, so a
//     removal could not be saved. The old page's Remove and theme picker
//     both did nothing (D-320);
//   * the admin's own name, title and photo moved to Settings: they are the
//     admin's profile, not the company's brand;
//   * only the company's admin edits (D-280); everyone else on the account
//     sees the same page without the controls.

import { useEffect, useMemo, useRef, useState } from "react"
import { useQueryClient } from "@tanstack/react-query"
import { PageHeader } from "@/components/page-header"
import { RuleList } from "@/components/ui/list"
import { useToast } from "@/components/ui/use-toast"
import { useCompanyBranding, useCompanyOverview, useCompanyReps, queryKeys } from "@/hooks/use-api"
import { Avatar, H2, RowButton } from "@/components/sponsor/shared"
import { ReportThumb } from "@/components/shared/report-thumb"
import type { Rep } from "@/lib/company-people"
import { HEX, SAVE_NOTE, brandFromApi, brandPatch, type Brand, type CompanyBranding } from "@/lib/company-brand"

const field = "h-10 rounded-[9px] border-[1.5px] border-[var(--border-strong)] bg-white px-3 text-[15px] text-foreground outline-none focus:border-[var(--link)] focus:ring-[3px] focus:ring-[var(--link)]/20"

function Row({ label, sub, children, action }: { label: string; sub?: string; children: React.ReactNode; action?: React.ReactNode }) {
  return (
    <div className="grid grid-cols-[160px_minmax(0,1fr)_auto] items-center gap-5 border-b border-[var(--border-subtle)] py-[14px]">
      <span className="flex flex-col leading-[1.3]"><span className="text-[15px] font-semibold text-foreground">{label}</span>{sub && <span className="text-[13px] text-muted-foreground">{sub}</span>}</span>
      <span className="flex min-w-0 items-center gap-3">{children}</span>
      <span>{action}</span>
    </div>
  )
}

/** Replace a logo: upload the file, hand back its URL. */
function ReplaceLogo({ onDone, label = "Replace" }: { onDone: (url: string) => void; label?: string }) {
  const input = useRef<HTMLInputElement>(null)
  const [busy, setBusy] = useState(false)
  const { toast } = useToast()
  async function upload(file: File) {
    setBusy(true)
    try {
      const form = new FormData()
      form.append("file", file)
      const res = await fetch("/api/proxy/v1/upload/branding/logo", { method: "POST", body: form, credentials: "include" })
      const data = await res.json().catch(() => ({}))
      if (!res.ok) throw new Error(data.detail || "Upload failed")
      onDone(data.url)
    } catch (e) {
      toast({ title: "That logo didn't upload", description: e instanceof Error ? e.message : "Try again.", variant: "destructive" })
    } finally {
      setBusy(false)
    }
  }
  return (
    <>
      <input ref={input} type="file" accept="image/png,image/jpeg,image/webp,image/svg+xml" className="hidden"
        onChange={(e) => { const f = e.target.files?.[0]; if (f) upload(f); e.target.value = "" }} />
      <RowButton onClick={() => input.current?.click()}>{busy ? "Uploading…" : label}</RowButton>
    </>
  )
}

function LogoChip({ src, on }: { src: string | null; on: string }) {
  return (
    <span className="flex h-12 w-28 items-center justify-center rounded-[9px] border border-[var(--border)] p-1.5" style={{ background: on }}>
      {src ? <img src={src} alt="" className="max-h-full max-w-full object-contain" /> : <span className="text-[12px] text-muted-foreground">None yet</span>}
    </span>
  )
}

export default function CompanyBrandingPage() {
  const qc = useQueryClient()
  const { toast } = useToast()
  const { data, isLoading, error } = useCompanyBranding()
  const { data: overview } = useCompanyOverview()
  const { data: repsData } = useCompanyReps()
  const canManage: boolean = data?.can_manage === true
  const accountName: string = overview?.company?.name ?? ""
  const saved = useMemo(() => brandFromApi(data?.branding as CompanyBranding | null, accountName), [data, accountName])
  const [brand, setBrand] = useState<Brand>(saved)
  const [saving, setSaving] = useState(false)
  const [pdfBusy, setPdfBusy] = useState(false)
  useEffect(() => setBrand(saved), [saved])

  const patch = brandPatch(saved, brand)
  const dirty = Object.keys(patch).length > 0
  const reps: Rep[] = repsData?.reps ?? []
  const exampleRep = reps.find((r) => r.status === "active") ?? reps[0]
  const set = (p: Partial<Brand>) => setBrand((b) => ({ ...b, ...p }))
  const primaryShown = HEX.test(brand.primary) ? brand.primary : undefined
  const accentShown = HEX.test(brand.accent) ? brand.accent : undefined

  if (error) return <p className="text-[16px] text-muted-foreground">{String(error).includes("403") ? "This account isn't on a title company." : "Couldn't load your brand right now."}</p>

  async function save() {
    setSaving(true)
    try {
      const res = await fetch("/api/proxy/v1/company/branding", {
        method: "PATCH", credentials: "include", headers: { "Content-Type": "application/json" }, body: JSON.stringify(patch),
      })
      const body = await res.json().catch(() => ({}))
      if (!res.ok) throw new Error(typeof body.detail === "string" ? body.detail : "That didn't save.")
      await qc.invalidateQueries({ queryKey: queryKeys.company.branding })
      toast({ title: "Brand saved", description: "Your reps' next reports and emails carry it." })
    } catch (e) {
      toast({ title: "Not saved", description: e instanceof Error ? e.message : "That didn't save.", variant: "destructive" })
    } finally {
      setSaving(false)
    }
  }

  async function samplePdf() {
    setPdfBusy(true)
    try {
      const res = await fetch("/api/proxy/v1/branding/sample-pdf", {
        method: "POST", credentials: "include", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ report_type: "market_snapshot" }),
      })
      if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail || "The sample PDF didn't generate.")
      const url = URL.createObjectURL(await res.blob())
      const a = document.createElement("a")
      a.href = url; a.download = "sample-market-snapshot.pdf"; a.click()
      URL.revokeObjectURL(url)
    } catch (e) {
      toast({ title: "No sample PDF", description: e instanceof Error ? e.message : "Try again.", variant: "destructive" })
    } finally {
      setPdfBusy(false)
    }
  }

  const colourRow = (key: "primary" | "accent", label: string, sub: string) => (
    <Row label={label} sub={sub} action={null}>
      {/* The swatch is the picker: an unset colour shows empty, not black. */}
      <label className={`relative size-10 shrink-0 rounded-[9px] border border-[var(--border)] ${canManage ? "cursor-pointer" : ""}`} style={{ background: HEX.test(brand[key]) ? brand[key] : "repeating-linear-gradient(45deg, #fff 0 6px, #f1f0ec 6px 12px)" }}>
        {canManage && <input type="color" aria-label={`${label} picker`} value={HEX.test(brand[key]) ? brand[key] : "#ffffff"} onChange={(e) => set({ [key]: e.target.value } as Partial<Brand>)} className="absolute inset-0 size-full cursor-pointer opacity-0" />}
      </label>
      {canManage ? (
        <>
          <input aria-label={label} value={brand[key]} onChange={(e) => set({ [key]: e.target.value.trim() } as Partial<Brand>)} placeholder="#rrggbb" className={`${field} w-32 font-mono`} />
          {brand[key] && !HEX.test(brand[key]) && <span className="text-[13px] text-[var(--warning-foreground)]">Six hex digits after #</span>}
          {!brand[key] && <span className="text-[13px] text-muted-foreground">Not set</span>}
        </>
      ) : (
        <span className="font-mono text-[15px] text-[var(--body)]">{brand[key] || "Not set"}</span>
      )}
    </Row>
  )

  return (
    <div className="flex flex-col gap-9">
      <PageHeader
        title="Branding"
        description="Your brand is on every report and email your reps send. Your agents' reports carry their own."
      />

      <div className="grid grid-cols-1 gap-10 lg:grid-cols-[minmax(0,1fr)_300px]">
        <div className="flex flex-col gap-9">
          <div className="flex flex-col gap-4">
            <RuleList>
              <Row label="Name" sub="On reports and in emails">
                {canManage
                  ? <input aria-label="Name" value={brand.name} onChange={(e) => set({ name: e.target.value })} className={`${field} w-full max-w-[360px]`} />
                  : <span className="text-[15px] text-foreground">{brand.name}</span>}
              </Row>
              <Row label="Logo" sub="On your colour" action={canManage && <ReplaceLogo onDone={(url) => set({ logo: url })} label={brand.logo ? "Replace" : "Add"} />}>
                <LogoChip src={brand.logo} on={primaryShown ?? "var(--muted)"} />
              </Row>
              <Row label="Logo on white" sub={brand.logoOnWhite ? "Footers and light pages" : "Uses your logo until you add one"} action={canManage && <ReplaceLogo onDone={(url) => set({ logoOnWhite: url })} label={brand.logoOnWhite ? "Replace" : "Add"} />}>
                <LogoChip src={brand.logoOnWhite ?? brand.logo} on="#ffffff" />
              </Row>
              {colourRow("primary", "Colour", "Headers and buttons")}
              {colourRow("accent", "Second colour", "Highlights on the report")}
            </RuleList>
            {canManage ? (
              <div className="flex flex-wrap items-center gap-4">
                <button type="button" onClick={save} disabled={!dirty || saving} className="h-[46px] rounded-[10px] bg-primary px-[20px] text-[15px] font-semibold text-primary-foreground transition-colors hover:bg-[var(--primary-hover)] disabled:opacity-50">
                  {saving ? "Saving…" : "Save changes"}
                </button>
                {dirty && <button type="button" onClick={() => setBrand(saved)} className="text-[14px] font-semibold text-[var(--link)]">Undo changes</button>}
                <span className="text-[14px] text-muted-foreground">{SAVE_NOTE}</span>
              </div>
            ) : (
              !isLoading && <p className="text-[14px] text-muted-foreground">Only your company&apos;s admin can change the brand.</p>
            )}
          </div>

          <div className="flex flex-col gap-[14px]">
            <H2>What each rep adds</H2>
            <div className="flex max-w-[520px] items-center gap-4 rounded-xl border border-[var(--border)] px-5 py-4">
              <Avatar name={exampleRep?.name ?? "Rep"} size={44} color={primaryShown} />
              <span className="flex min-w-0 flex-col gap-1 leading-[1.3]">
                <span className="text-[15px] font-semibold text-foreground">{exampleRep ? exampleRep.name : "Your rep"} · Title rep</span>
                <span className="text-[13px] text-muted-foreground">Their photo and two contact lines</span>
              </span>
            </div>
            <p className="max-w-[640px] text-[15px] leading-[1.55] text-[var(--body)]">
              Each rep adds only their photo and contact line; they set those themselves. Your colours are used as you set
              them — where white text sits on one, at the top of a report, the report darkens it just enough to read.
            </p>
          </div>
        </div>

        <div className="flex flex-col gap-3 lg:sticky lg:top-6 lg:self-start">
          <span className="text-[13px] text-muted-foreground">Live · your colours on a report&apos;s first page</span>
          <ReportThumb reportType="market_snapshot" width={300} primaryColor={primaryShown} accentColor={accentShown} shadow="thumb" />
          <button type="button" onClick={samplePdf} disabled={pdfBusy} className="self-start text-[14px] font-semibold text-[var(--link)] hover:text-[var(--link-hover)] disabled:opacity-60">
            {pdfBusy ? "Making the PDF…" : "Download a sample PDF"}
          </button>
          {dirty && <span className="text-[13px] text-muted-foreground">The sample PDF uses your saved brand.</span>}
        </div>
      </div>
    </div>
  )
}
