"use client"

// /app/company/settings — Settings for a title company. Design's company
// Settings (Sponsor v4): the company's details, who is on the account, your
// own details, sign out.
//
// Adopted with these changes, each to what the API has:
//   * People on the account is a list, not a manager: there is no endpoint to
//     add or remove someone, so the page says so instead of drawing Design's
//     "Add an admin" and "Remove" (the D-302 / D-320 mistake: a control that
//     does nothing);
//   * no "Email me" toggles: there are no company notification settings to
//     save them to;
//   * Address is shown, never edited here — TODO(B5): the company postal
//     address is gated on a business decision. Until it is set, the emails
//     carry TrendyReports' address, and the page says that;
//   * Website saves through PATCH /v1/company/branding (reps' emails show it);
//     the PATCH keeps a field sent empty, so it can be replaced, not cleared;
//   * your name, title, phone and photo moved here from Branding: they are
//     your profile (PATCH /v1/users/me), not the company's brand.

import { useEffect, useRef, useState } from "react"
import Link from "next/link"
import { useQueryClient } from "@tanstack/react-query"
import { PageHeader } from "@/components/page-header"
import { RuleList } from "@/components/ui/list"
import { useToast } from "@/components/ui/use-toast"
import { useCompanySettings, useMe, queryKeys } from "@/hooks/use-api"
import { Avatar, H2, RowButton } from "@/components/sponsor/shared"
import { personRole, profilePatch, websitePatch, type CompanySettings, type Profile } from "@/lib/company-settings"

const field = "h-10 rounded-[9px] border-[1.5px] border-[var(--border-strong)] bg-white px-3 text-[15px] text-foreground outline-none focus:border-[var(--link)] focus:ring-[3px] focus:ring-[var(--link)]/20"
const ink = "h-10 rounded-[9px] bg-primary px-4 text-[14px] font-semibold text-primary-foreground transition-colors hover:bg-[var(--primary-hover)] disabled:opacity-50"

function Row({ label, sub, children, action }: { label: string; sub?: string; children: React.ReactNode; action?: React.ReactNode }) {
  return (
    <div className="grid grid-cols-[160px_minmax(0,1fr)_auto] items-center gap-5 border-b border-[var(--border-subtle)] py-[14px]">
      <span className="flex flex-col leading-[1.3]"><span className="text-[15px] font-semibold text-foreground">{label}</span>{sub && <span className="text-[13px] text-muted-foreground">{sub}</span>}</span>
      <span className="flex min-w-0 flex-wrap items-center gap-3 text-[15px] text-[var(--body)]">{children}</span>
      <span>{action}</span>
    </div>
  )
}

async function send(path: string, method: "PATCH", body: unknown) {
  const res = await fetch(`/api/proxy${path}`, { method, credentials: "include", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) })
  const data = await res.json().catch(() => ({}))
  if (!res.ok) throw new Error(typeof data.detail === "string" ? data.detail : "That didn't save.")
  return data
}

export default function CompanySettingsPage() {
  const qc = useQueryClient()
  const { toast } = useToast()
  const { data, isLoading, error } = useCompanySettings()
  const { data: me } = useMe()
  const s = data as CompanySettings | undefined
  const canManage = s?.can_manage === true

  const [website, setWebsite] = useState("")
  const savedProfile: Profile = {
    first_name: me?.first_name ?? "", last_name: me?.last_name ?? "", job_title: me?.job_title ?? "",
    phone: me?.phone ?? "", avatar_url: me?.avatar_url ?? null,
  }
  const [profile, setProfile] = useState<Profile>(savedProfile)
  const [busy, setBusy] = useState<string | null>(null)
  const photo = useRef<HTMLInputElement>(null)
  useEffect(() => setWebsite(s?.company.website_url ?? ""), [s?.company.website_url])
  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => setProfile(savedProfile), [me])

  if (error) return <p className="text-[16px] text-muted-foreground">{String(error).includes("403") ? "This account isn't on a title company." : "Couldn't load your settings right now."}</p>

  const site = websitePatch(s?.company.website_url ?? null, website)
  const prof = profilePatch(savedProfile, profile)

  async function run(key: string, fn: () => Promise<unknown>, done: string, invalidate: readonly unknown[]) {
    setBusy(key)
    try {
      await fn()
      await qc.invalidateQueries({ queryKey: invalidate })
      toast({ title: done })
    } catch (e) {
      toast({ title: "Not saved", description: e instanceof Error ? e.message : "That didn't save.", variant: "destructive" })
    } finally {
      setBusy(null)
    }
  }

  async function uploadPhoto(file: File) {
    const form = new FormData()
    form.append("file", file)
    setBusy("photo")
    try {
      const res = await fetch("/api/proxy/v1/upload/branding/headshot", { method: "POST", body: form, credentials: "include" })
      const d = await res.json().catch(() => ({}))
      if (!res.ok) throw new Error(d.detail || "Upload failed")
      setProfile((p) => ({ ...p, avatar_url: d.url }))
    } catch (e) {
      toast({ title: "That photo didn't upload", description: e instanceof Error ? e.message : "Try again.", variant: "destructive" })
    } finally {
      setBusy(null)
    }
  }

  async function signOut() {
    try { await fetch("/api/proxy/v1/auth/logout", { method: "POST", credentials: "include" }) } catch {}
    window.location.href = "/login"
  }

  const people = s?.people ?? []
  const fullName = [profile.first_name, profile.last_name].filter(Boolean).join(" ") || me?.email || ""

  return (
    <div className="flex flex-col gap-10">
      <PageHeader title="Settings" description={s ? `${s.company.name ?? ""} · ${people.length} ${people.length === 1 ? "person" : "people"} on this account` : undefined} />

      <div className="flex flex-col gap-[14px]">
        <H2>Company</H2>
        <RuleList>
          <Row label="Name" sub="Your account" action={<Link href="/app/company/branding" className="text-[14px] font-semibold text-[var(--link)]">Name on reports →</Link>}>
            {s?.company.name ?? ""}
          </Row>
          <Row label="Website" sub="On your reps' emails" action={canManage && site && (
            <button type="button" className={ink} disabled={busy === "site"} onClick={() => run("site", () => send("/v1/company/branding", "PATCH", site), "Website saved", queryKeys.company.settings)}>
              {busy === "site" ? "Saving…" : "Save"}
            </button>
          )}>
            {canManage
              ? <input aria-label="Website" value={website} onChange={(e) => setWebsite(e.target.value)} placeholder="https://" className={`${field} w-full max-w-[360px]`} />
              : (s?.company.website_url || "Not set")}
          </Row>
          {/* TODO(B5): the company's postal address is gated on a business decision. Shown, never set here. */}
          <Row label="Address" sub="On your reps' emails">
            {s?.company.postal_address
              ? s.company.postal_address
              : !isLoading && <span className="text-muted-foreground">Not set. Until it is, your reps&apos; emails carry TrendyReports&apos; postal address.</span>}
          </Row>
        </RuleList>
      </div>

      <div className="flex flex-col gap-[14px]">
        <H2>People on this account</H2>
        <RuleList>
          {people.map((p) => { const r = personRole(p.role); return (
            <div key={p.id} className="grid grid-cols-[minmax(0,1fr)_minmax(0,1fr)] items-center gap-5 border-b border-[var(--border-subtle)] py-[13px]">
              <span className="flex min-w-0 items-center gap-3">
                <Avatar name={p.name || p.email} size={34} />
                <span className="flex min-w-0 flex-col leading-[1.3]"><span className="truncate text-[15px] font-semibold text-foreground">{p.name || p.email}{p.id === s?.you ? " (you)" : ""}</span>{p.name && <span className="truncate text-[13px] text-muted-foreground">{p.email}</span>}</span>
              </span>
              <span className="text-[15px] text-[var(--body)]"><span className="font-semibold text-foreground">{r.label}</span> · {r.can}</span>
            </div>
          )})}
        </RuleList>
        <p className="text-[14px] text-muted-foreground">Adding or removing people on the company account isn&apos;t available in the app yet.</p>
      </div>

      <div className="flex flex-col gap-[14px]">
        <H2>You</H2>
        <RuleList>
          <Row label="Photo" action={<><input ref={photo} type="file" accept="image/png,image/jpeg,image/webp" className="hidden" onChange={(e) => { const f = e.target.files?.[0]; if (f) uploadPhoto(f); e.target.value = "" }} /><RowButton onClick={() => photo.current?.click()}>{busy === "photo" ? "Uploading…" : profile.avatar_url ? "Replace" : "Add"}</RowButton></>}>
            {profile.avatar_url ? <img src={profile.avatar_url} alt="" className="size-11 rounded-full object-cover" /> : <Avatar name={fullName} size={44} />}
          </Row>
          <Row label="Name">
            <input aria-label="First name" value={profile.first_name} onChange={(e) => setProfile({ ...profile, first_name: e.target.value })} placeholder="First" className={`${field} w-40`} />
            <input aria-label="Last name" value={profile.last_name} onChange={(e) => setProfile({ ...profile, last_name: e.target.value })} placeholder="Last" className={`${field} w-48`} />
          </Row>
          <Row label="Title">
            <input aria-label="Title" value={profile.job_title} onChange={(e) => setProfile({ ...profile, job_title: e.target.value })} className={`${field} w-full max-w-[360px]`} />
          </Row>
          <Row label="Phone">
            <input aria-label="Phone" value={profile.phone} onChange={(e) => setProfile({ ...profile, phone: e.target.value })} className={`${field} w-48`} />
          </Row>
          <Row label="Email" sub="And your password" action={<Link href="/app/settings/security" className="text-[14px] font-semibold text-[var(--link)]">Change →</Link>}>
            {me?.email ?? ""}
          </Row>
        </RuleList>
        <div className="flex items-center gap-4">
          <button type="button" className={ink} disabled={!prof || busy === "profile"} onClick={() => prof && run("profile", () => send("/v1/users/me", "PATCH", prof), "Your details are saved", queryKeys.me)}>
            {busy === "profile" ? "Saving…" : "Save your details"}
          </button>
        </div>
      </div>

      <div className="border-t border-[var(--border-subtle)] pt-6">
        <RowButton onClick={signOut}>Sign out</RowButton>
      </div>
    </div>
  )
}
