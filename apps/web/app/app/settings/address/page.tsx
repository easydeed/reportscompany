"use client"

// /app/settings/address — the postal address at the foot of the emails this
// account sends (D-079). Per account; an empty save clears it, and the emails
// then carry TrendyReports' address, which the page says with the address.

import { useEffect, useState } from "react"
import { PageHeader } from "@/components/page-header"
import { useToast } from "@/components/ui/use-toast"
import { addressPut, inUseNote, type PostalAddress } from "@/lib/postal-address"

const field = "h-10 w-full max-w-[520px] rounded-[9px] border-[1.5px] border-[var(--border-strong)] bg-white px-3 text-[15px] text-foreground outline-none focus:border-[var(--link)] focus:ring-[3px] focus:ring-[var(--link)]/20"
const ink = "h-10 rounded-[9px] bg-primary px-4 text-[14px] font-semibold text-primary-foreground transition-colors hover:bg-[var(--primary-hover)] disabled:opacity-50"

export default function AddressSettingsPage() {
  const { toast } = useToast()
  const [data, setData] = useState<PostalAddress | null>(null)
  const [failed, setFailed] = useState(false)
  const [typed, setTyped] = useState("")
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    fetch("/api/proxy/v1/account/postal-address", { credentials: "include", cache: "no-store" })
      .then(async (r) => { if (!r.ok) throw new Error(String(r.status)); return r.json() })
      .then((d: PostalAddress) => { setData(d); setTyped(d.postal_address ?? "") })
      .catch(() => setFailed(true))
  }, [])

  const body = data ? addressPut(data.postal_address, typed) : null

  async function save() {
    if (!body) return
    setSaving(true)
    try {
      const res = await fetch("/api/proxy/v1/account/postal-address", {
        method: "PUT", credentials: "include",
        headers: { "Content-Type": "application/json" }, body: JSON.stringify(body),
      })
      const d = await res.json().catch(() => ({}))
      if (!res.ok) throw new Error(typeof d.detail === "string" ? d.detail : "That didn't save.")
      setData(d as PostalAddress)
      setTyped((d as PostalAddress).postal_address ?? "")
      toast({ title: body.postal_address ? "Address saved" : "Address cleared" })
    } catch (e) {
      toast({ title: "Not saved", description: e instanceof Error ? e.message : "That didn't save.", variant: "destructive" })
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="flex flex-col gap-8">
      <PageHeader title="Mailing address" description="The postal address printed at the foot of every email you send." />
      {failed && <p className="text-[16px] text-muted-foreground">Couldn&apos;t load your address right now.</p>}
      {data && (
        <div className="flex flex-col gap-3">
          {data.can_edit ? (
            <>
              <label htmlFor="postal-address" className="text-[15px] font-semibold text-foreground">Address</label>
              <input id="postal-address" value={typed} onChange={(e) => setTyped(e.target.value)}
                     placeholder="Street, city, state ZIP" className={field} />
              <p className="text-[14px] text-muted-foreground">
                Leave it empty to use TrendyReports&apos; address: {data.platform_address}
              </p>
              <div><button type="button" className={ink} disabled={!body || saving} onClick={save}>{saving ? "Saving…" : "Save"}</button></div>
            </>
          ) : null}
          <p className="text-[15px] text-[var(--body)]" data-testid="in-use">{inUseNote(data)}</p>
          {!data.can_edit && data.source !== "company" && (
            <p className="text-[14px] text-muted-foreground">Only the account&apos;s owner can change it.</p>
          )}
        </div>
      )}
    </div>
  )
}
