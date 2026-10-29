"use client"

// /cma/[code] — public homeowner funnel. Six steps, one question per screen.
// Spec: ../../../../../README.md §Home Value Page. Design: Home Value Page.dc.html.
// Everything the homeowner sees is in the agent's name: no product logo, no
// sign-up, no estimate number (that lives in the PDF — it is the reason to
// leave a contact). The server page (page.tsx) loads the agent by `code` and
// renders <CmaFunnel agent=… api=… />.

import { useEffect, useRef, useState, type ReactNode } from "react"
import { ArrowRight, Check, Download, House, MapPin, MessageCircle, Phone } from "lucide-react"
import { cn } from "@/lib/utils"

// ── Consent copy ─────────────────────────────────────────────────────────────
// Required before launch. Provided by the brokerage (TCPA). The slot holds up
// to three lines at 14px; the checkbox is required regardless of wording.
export const CONSENT_COPY = "" // TODO(legal): e.g. "Send me my report and let {agent} follow up about my home."

// ── Types ────────────────────────────────────────────────────────────────────

export type Agent = {
  name: string; brokerage: string; dre?: string | null
  phone: string            // E.164 or 10 digits; used for tel:/sms: and display
  photoUrl?: string | null
  /** The agent's theme_color. The page has no brand-name enum to pass. */
  color: string
  /** Omitted when the landing payload has no city. */
  city?: string
}

export type Suggestion = { address: string; locality: string } // "14 Cartwheel" / "Irvine, CA"

export type Record_ = {
  address: string; city: string; state: string; zip: string; type: string // "Single family"
  beds: number | null; baths: number | null; sqft: number | null; yearBuilt: number | null
}

export type Lead = {
  record: Record_
  method: "sms" | "email"
  contact: string          // digits only for sms
  firstName?: string
  consent: true
  consentText: string      // CONSENT_COPY as shown — store it with the lead
}

export type Api = {
  suggest: (q: string) => Promise<Suggestion[]>
  lookup: (s: Suggestion | string) => Promise<Record_ | null>
  submit: (lead: Lead) => Promise<{ reportUrl?: string }>
}

type Step = "address" | "looking" | "confirm" | "contact" | "processing" | "success"

// ── Helpers ──────────────────────────────────────────────────────────────────

const initials = (n: string) => n.split(" ").filter(Boolean).map((w) => w[0]).join("").slice(0, 2).toUpperCase()
const fmtPhone = (d: string) => d.length >= 6 ? `(${d.slice(0, 3)}) ${d.slice(3, 6)}-${d.slice(6)}` : d.length >= 3 ? `(${d.slice(0, 3)}) ${d.slice(3)}` : d
const masked = (d: string) => `(${d.slice(0, 3)}) ••• ${d.slice(6)}`
const dash = (v: number | null | undefined, f: (n: number) => string = String) => (v == null ? "—" : f(v))
const firstName = (n: string) => n.split(" ")[0]
const digitsOf = (p: string) => p.replace(/\D/g, "").replace(/^1(\d{10})$/, "$1")

const LOOK = ["Matching your address", "Reading the county record", "Checking the MLS for your street"]

// ── Component ────────────────────────────────────────────────────────────────

export default function CmaFunnel({ agent, api, cover, initialAddress = "" }: {
  agent: Agent
  api: Api
  /** Renders the property cover for the current record. Receives the live
   *  requester name so "Prepared for" updates as they type. Pinned to 816×1056
   *  and transform-scaled here (same move as components/shared/report-thumb). */
  cover: (p: { record: Record_ | null; requesterName: string }) => ReactNode
  /** `?address=` on the landing URL. The page already reads it. */
  initialAddress?: string
}) {
  const hex = agent.color
  const first = firstName(agent.name)
  const tel = digitsOf(agent.phone)

  const [step, setStep] = useState<Step>("address")
  const [addr, setAddr] = useState(initialAddress)
  const [sugs, setSugs] = useState<Suggestion[]>([])
  const [picked, setPicked] = useState<Suggestion | null>(null)
  const [record, setRecord] = useState<Record_ | null>(null)
  const [fix, setFix] = useState(false)
  const [method, setMethod] = useState<"sms" | "email">("sms")
  const [contact, setContact] = useState("")
  const [name, setName] = useState("")
  const [consent, setConsent] = useState(false)
  const [prog, setProg] = useState(0)
  const [reportUrl, setReportUrl] = useState<string | undefined>()
  const [error, setError] = useState<string | null>(null)
  const addrRef = useRef<HTMLInputElement>(null)

  // typeahead — ≥2 chars, three suggestions
  useEffect(() => {
    const q = addr.trim()
    if (q.length < 2 || picked) { setSugs([]); return }
    let live = true
    const t = setTimeout(() => api.suggest(q).then((r) => live && setSugs(r.slice(0, 3))).catch(() => live && setSugs([])), 150)
    return () => { live = false; clearTimeout(t) }
  }, [addr, picked, api])

  // stage ticker for the two waiting steps; the real call runs alongside and
  // the step advances when BOTH the last stage and the response have landed.
  const tick = (n: number) => {
    setProg(0)
    return new Promise<void>((res) => {
      let i = 0
      const id = setInterval(() => { i += 1; setProg(i); if (i >= n) { clearInterval(id); res() } }, 1000)
    })
  }

  const findHome = async (s: Suggestion | string) => {
    setError(null); setStep("looking")
    const [rec] = await Promise.all([api.lookup(s).catch(() => null), tick(LOOK.length)])
    if (!rec) { setStep("address"); setError("We couldn't find that address. Try the full street address."); setTimeout(() => addrRef.current?.focus(), 0); return }
    setRecord(rec); setStep("confirm")
  }

  const restart = () => {
    setStep("address"); setAddr(""); setPicked(null); setRecord(null); setFix(false)
    setContact(""); setConsent(false); setProg(0); setError(null)
    setTimeout(() => addrRef.current?.focus(), 0)
  }

  const digits = contact.replace(/\D/g, "")
  const contactOk = method === "sms" ? digits.length === 10 : /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(contact)
  const canSubmit = contactOk && consent && !!record
  const build = ["Finding your home in county records", "Pulling nearby sales from the MLS", "Writing your report",
    method === "sms" ? `Texting the link to ${fmtPhone(digits)}` : `Emailing the link to ${contact}`]

  const submit = async () => {
    if (!canSubmit || !record) return
    setError(null); setStep("processing")
    const lead: Lead = { record, method, contact: method === "sms" ? digits : contact.trim(), firstName: name.trim() || undefined, consent: true, consentText: CONSENT_COPY }
    const [res] = await Promise.all([api.submit(lead).catch(() => null), tick(build.length)])
    if (!res) { setStep("contact"); setError("Something went wrong sending your report. Try again."); return }
    setReportUrl(res.reportUrl); setStep("success")
  }

  const dotStep = step === "address" || step === "looking" ? 0 : step === "confirm" ? 1 : 2
  const veiled = step === "address" || step === "looking"
  const fullAddr = record?.address ?? picked?.address ?? addr.trim()
  const requester = name.trim()

  return (
    <div className="flex min-h-screen flex-col bg-[#FAFAF7] text-[#0F172A] antialiased">
      {/* Header — the agent, not the product */}
      <header className="border-b border-[#ECEAE3] bg-white">
        <div className="mx-auto flex max-w-[1080px] items-center justify-between gap-4 px-5 py-[14px]">
          <div className="flex min-w-0 items-center gap-3">
            <AgentAvatar agent={agent} size={42} />
            <div className="flex min-w-0 flex-col leading-[1.25]">
              <span className="truncate text-[15px] font-bold">{agent.name}</span>
              <span className="truncate text-[13px] text-[#64748B]">{agent.brokerage}{agent.dre ? ` · DRE #${agent.dre}` : ""}</span>
            </div>
          </div>
          <a href={`tel:${tel}`} aria-label={`Call ${first}`}
            className="inline-flex h-10 shrink-0 items-center gap-2 whitespace-nowrap rounded-full border border-[#D6D3CB] bg-white px-[14px] text-[14px] font-semibold">
            <Phone size={15} /> <span className="hidden sm:inline">{fmtPhone(tel)}</span>
          </a>
        </div>
      </header>

      <main className="mx-auto grid w-full max-w-[1080px] flex-1 grid-cols-[repeat(auto-fit,minmax(min(100%,420px),1fr))] items-start gap-9 px-5 pb-14 pt-7">
        {/* Artifact */}
        <section className="flex min-w-0 flex-col items-center gap-3">
          <div className="relative w-[min(100%,400px)] overflow-hidden rounded-lg transition-[height] duration-500 ease-[cubic-bezier(0.2,0.8,0.2,1)]"
            style={{ height: veiled ? 260 : "auto" }}>
            <div className="relative aspect-[816/1056] w-[min(100%,400px)] overflow-hidden rounded-lg bg-white transition-transform duration-500 ease-[cubic-bezier(0.2,0.8,0.2,1)]"
              style={{ boxShadow: "0 30px 60px -22px rgba(15,23,42,0.35),0 0 0 1px rgba(15,23,42,0.06)", transform: step === "success" ? "rotate(-2deg)" : "none", filter: step === "address" ? "saturate(0.6)" : "none" }}>
              <CoverFrame>{cover({ record, requesterName: requester })}</CoverFrame>
              {veiled && (
                <div className="absolute inset-0 flex items-end justify-center p-7"
                  style={{ background: "linear-gradient(180deg,rgba(250,250,247,0) 30%,rgba(250,250,247,0.92) 70%)" }}>
                  <span className="text-balance text-center text-[14px] font-semibold text-[#334155]">
                    {step === "address" ? "Your report starts with your address" : "Pulling your home's record…"}
                  </span>
                </div>
              )}
            </div>
          </div>
          <span className="text-center text-[13px] text-[#64748B]">
            {step === "address" ? "A real report, like this one, for your home" : `Your report · ${fullAddr}`}
          </span>
        </section>

        {/* Controls */}
        <section className="flex w-full max-w-[460px] min-w-0 flex-col gap-6 justify-self-center">
          <div className="flex gap-[6px]" aria-hidden>
            {[0, 1, 2].map((i) => <span key={i} className="h-1 flex-1 rounded-sm transition-colors" style={{ background: i <= dotStep ? hex : "#E4E2DA" }} />)}
          </div>

          {step === "address" && (
            <div className="flex flex-col gap-5">
              <div className="flex flex-col gap-[10px]">
                <h1 className="text-balance text-[clamp(30px,5vw,40px)] font-extrabold leading-[1.05] tracking-[-0.035em]">{agent.city ? `What's your ${agent.city} home worth today?` : "What's your home worth today?"}</h1>
                <p className="text-pretty text-[17px] text-[#475569]">Based on this month's closed sales near you. Free, from {first} — no sign-up.</p>
              </div>
              <div className="flex flex-col gap-2">
                <div className="relative">
                  <House size={18} className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-[#94A3B8]" />
                  <input ref={addrRef} value={addr} onChange={(e) => { setAddr(e.target.value); setPicked(null) }}
                    onKeyDown={(e) => e.key === "Enter" && addr.trim() && findHome(picked ?? addr.trim())}
                    placeholder="Your street address" autoComplete="street-address" aria-label="Street address"
                    className="h-[58px] w-full rounded-xl border-[1.5px] border-[#D6D3CB] bg-white pl-[46px] pr-4 text-[18px] outline-none focus:border-[#0F172A]" />
                </div>
                {sugs.length > 0 && (
                  <ul className="flex flex-col overflow-hidden rounded-xl border border-[#ECEAE3] bg-white" style={{ boxShadow: "0 12px 32px -16px rgba(15,23,42,0.25)" }}>
                    {sugs.map((g) => (
                      <li key={g.address + g.locality}>
                        <button type="button" onClick={() => { setPicked(g); setAddr(`${g.address}, ${g.locality}`); findHome(g) }}
                          className="flex w-full items-center gap-3 border-b border-[#F1F1EE] px-4 py-[13px] text-left text-[15px] hover:bg-[#FAFAF7]">
                          <MapPin size={15} className="shrink-0 text-[#94A3B8]" /><span className="font-semibold">{g.address}</span><span className="text-[#64748B]">{g.locality}</span>
                        </button>
                      </li>
                    ))}
                  </ul>
                )}
                {error && <p role="alert" className="text-[14px] text-[#B91C1C]">{error}</p>}
              </div>
              <Cta hex={hex} disabled={!addr.trim()} onClick={() => findHome(picked ?? addr.trim())}>Find my home</Cta>
              <div className="flex flex-wrap gap-x-4 gap-y-[6px] text-[13px] text-[#64748B]"><span>Takes 10 seconds</span><span>·</span><span>No obligation</span><span>·</span><span>Only {first} sees your details</span></div>
            </div>
          )}

          {step === "looking" && (
            <div className="flex flex-col gap-[18px]">
              <h1 className="text-[30px] font-extrabold leading-[1.1] tracking-[-0.03em]">Finding your home…</h1>
              <Stages items={LOOK} prog={prog} />
            </div>
          )}

          {step === "confirm" && record && (
            <div className="flex flex-col gap-5">
              <div className="flex flex-col gap-2">
                <span className="text-[12px] font-bold uppercase tracking-[0.12em]" style={{ color: hex }}>Found it</span>
                <h1 className="text-[30px] font-extrabold leading-[1.1] tracking-[-0.03em]">Is this your home?</h1>
              </div>
              <div className="flex flex-col gap-[14px] rounded-[14px] border border-[#ECEAE3] bg-white px-5 py-[18px]">
                <div className="flex flex-col">
                  <span className="text-[19px] font-bold">{record.address}</span>
                  <span className="text-[14px] text-[#64748B]">{record.city}, {record.state} {record.zip} · {record.type}</span>
                </div>
                <div className="grid grid-cols-4 gap-2">
                  <Fact k="Beds" v={record.beds} lock={!fix} hex={hex} onChange={(n) => setRecord({ ...record, beds: n })} />
                  <Fact k="Baths" v={record.baths} lock={!fix} hex={hex} onChange={(n) => setRecord({ ...record, baths: n })} />
                  <Fact k="Sq ft" v={record.sqft} lock={!fix} hex={hex} fmt={(n) => n.toLocaleString()} onChange={(n) => setRecord({ ...record, sqft: n })} />
                  <Fact k="Built" v={record.yearBuilt} lock={!fix} hex={hex} onChange={(n) => setRecord({ ...record, yearBuilt: n })} />
                </div>
                <span className="text-[13px] text-[#64748B]">{fix ? "Tap a number to change it." : missingNote(record)}</span>
              </div>
              <Cta hex={hex} onClick={() => { setFix(false); setStep("contact") }}>Yes, that's it</Cta>
              <div className="flex justify-center gap-[22px] text-[14px]">
                <button type="button" onClick={() => setFix((f) => !f)} className="font-semibold text-[#334155]">{fix ? "Done fixing" : "Something's off"}</button>
                <button type="button" onClick={restart} className="font-semibold text-[#64748B]">Not my home</button>
              </div>
            </div>
          )}

          {step === "contact" && (
            <div className="flex flex-col gap-5">
              <div className="flex flex-col gap-2">
                <h1 className="text-[30px] font-extrabold leading-[1.1] tracking-[-0.03em]">Where should it go?</h1>
                <p className="text-[16px] text-[#475569]">It's a PDF of the sales near your home. We'll send the link.</p>
              </div>
              <div role="radiogroup" className="flex gap-[6px] rounded-xl bg-[#ECEAE3] p-1">
                {(["sms", "email"] as const).map((m) => (
                  <button key={m} type="button" role="radio" aria-checked={method === m} onClick={() => { setMethod(m); setContact("") }}
                    className={cn("h-[42px] flex-1 rounded-[9px] text-[15px] font-semibold", method === m ? "bg-white text-[#0F172A] shadow-[0_1px_3px_rgba(15,23,42,0.12)]" : "text-[#64748B]")}>
                    {m === "sms" ? "Text me" : "Email me"}
                  </button>
                ))}
              </div>
              <input value={contact} aria-label={method === "sms" ? "Mobile number" : "Email address"}
                onChange={(e) => setContact(method === "sms" ? fmtPhone(e.target.value.replace(/\D/g, "").slice(0, 10)) : e.target.value)}
                placeholder={method === "sms" ? "(555) 555-5555" : "you@email.com"} inputMode={method === "sms" ? "tel" : "email"} autoComplete={method === "sms" ? "tel" : "email"}
                className="h-[58px] w-full rounded-xl border-[1.5px] border-[#D6D3CB] bg-white px-4 text-center text-[20px] tabular-nums tracking-[0.01em] outline-none focus:border-[#0F172A]" />
              <input value={name} onChange={(e) => setName(e.target.value)} placeholder="Your name (optional)" autoComplete="given-name" aria-label="Your name"
                className="h-[50px] w-full rounded-xl border border-[#E4E2DA] bg-white px-4 text-[16px] outline-none focus:border-[#0F172A]" />
              <label className="flex cursor-pointer items-start gap-3 text-[14px] leading-[1.45] text-[#475569]">
                <input type="checkbox" checked={consent} onChange={(e) => setConsent(e.target.checked)} className="peer sr-only" required />
                <span aria-hidden className={cn("mt-[1px] flex size-[22px] shrink-0 items-center justify-center rounded-md border-[1.5px] peer-focus-visible:ring-2 peer-focus-visible:ring-[#0F172A]/40", consent ? "border-[#0F172A] bg-[#0F172A]" : "border-[#CBD5E1] bg-white")}>
                  {consent && <Check size={13} className="text-white" />}
                </span>
                <span className={cn(!CONSENT_COPY && "italic text-[#94A3B8]")}>{CONSENT_COPY || `[Consent wording — ${first} can contact me about my home]`}</span>
              </label>
              {error && <p role="alert" className="text-[14px] text-[#B91C1C]">{error}</p>}
              <Cta hex={hex} disabled={!canSubmit} onClick={submit}>{method === "sms" ? "Text me my report" : "Email me my report"}</Cta>
              <button type="button" onClick={() => setStep("confirm")} className="self-center text-[14px] font-semibold text-[#64748B]">← Back</button>
            </div>
          )}

          {step === "processing" && (
            <div className="flex flex-col gap-[18px]">
              <div className="flex flex-col gap-2">
                <h1 className="text-[30px] font-extrabold leading-[1.1] tracking-[-0.03em]">Building your report…</h1>
                <p className="text-[15px] text-[#64748B]">About 20 seconds. You can close this — the link still arrives.</p>
              </div>
              <Stages items={build} prog={prog} />
            </div>
          )}

          {step === "success" && (
            <div className="flex flex-col gap-[22px]">
              <div className="flex flex-col gap-[10px]">
                <span className="flex size-12 items-center justify-center rounded-full bg-[#D1FAE5]"><Check size={22} className="text-[#047857]" /></span>
                <h1 className="text-balance text-[30px] font-extrabold leading-[1.1] tracking-[-0.03em]">
                  {method === "sms" ? `On its way to ${masked(digits)}.` : "It's in your inbox."}
                </h1>
                <p className="text-pretty text-[16px] text-[#475569]">
                  {method === "sms" ? "The text has a link to your PDF. It works for 30 days." : `Sent to ${contact}. The link works for 30 days.`}
                </p>
              </div>
              {reportUrl && (
                <a href={reportUrl} target="_blank" rel="noreferrer" className="flex h-[58px] items-center justify-center gap-2 rounded-xl bg-[#0F172A] text-[17px] font-semibold text-white">
                  <Download size={16} /> Open my report now
                </a>
              )}
              <div className="flex flex-col gap-[14px] rounded-[14px] border border-[#ECEAE3] bg-white px-5 py-[18px]">
                <div className="flex items-center gap-3">
                  <AgentAvatar agent={agent} size={44} />
                  <div className="flex flex-col leading-[1.3]">
                    <span className="text-[15px] font-bold">{agent.name}</span>
                    <span className="text-[14px] text-[#64748B]">Questions about the report? I'm happy to walk through it.</span>
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-2">
                  <a href={`tel:${tel}`} className="flex h-12 items-center justify-center gap-2 rounded-[10px] text-[15px] font-semibold text-white" style={{ background: hex }}><Phone size={15} /> Call {first}</a>
                  <a href={`sms:${tel}`} className="flex h-12 items-center justify-center gap-2 rounded-[10px] border border-[#D6D3CB] text-[15px] font-semibold"><MessageCircle size={15} /> Text</a>
                </div>
              </div>
              <button type="button" onClick={restart} className="self-center text-[14px] font-semibold text-[#64748B]">Check another address</button>
            </div>
          )}
        </section>
      </main>

      <footer className="border-t border-[#ECEAE3]">
        <div className="mx-auto flex max-w-[1080px] flex-wrap items-center justify-between gap-3 px-5 py-[18px] text-[12px] text-[#94A3B8]">
          <span>From recent MLS sales. Not an appraisal.</span>
          <span>{agent.brokerage}{agent.dre ? ` · DRE #${agent.dre}` : ""}</span>
        </div>
      </footer>
    </div>
  )
}

// ── Pieces ───────────────────────────────────────────────────────────────────

function AgentAvatar({ agent, size }: { agent: Agent; size: number }) {
  return agent.photoUrl
    ? <img src={agent.photoUrl} alt="" width={size} height={size} className="shrink-0 rounded-full object-cover" style={{ width: size, height: size }} />
    : <span className="flex shrink-0 items-center justify-center rounded-full text-[14px] font-bold text-white" style={{ width: size, height: size, background: agent.color }}>{initials(agent.name)}</span>
}

function Cta({ hex, disabled, onClick, children }: { hex: string; disabled?: boolean; onClick: () => void; children: ReactNode }) {
  return (
    <button type="button" disabled={disabled} onClick={onClick}
      className="flex h-[58px] items-center justify-center gap-2 rounded-xl text-[17px] font-semibold disabled:cursor-not-allowed"
      style={{ background: disabled ? "#E4E2DA" : hex, color: disabled ? "#94A3B8" : "#fff" }}>
      {children}<ArrowRight size={16} />
    </button>
  )
}

function Stages({ items, prog }: { items: string[]; prog: number }) {
  return (
    <ol className="flex flex-col border-t-[1.5px] border-[#0F172A]" aria-live="polite">
      {items.map((t, i) => {
        const done = i < prog, active = i === prog
        return (
          <li key={t} className={cn("flex items-center gap-[14px] border-b border-[#ECEAE3] py-[13px] text-[15px]", done || active ? "text-[#0F172A]" : "text-[#94A3B8]", active ? "font-semibold" : "font-medium")}>
            <span className={cn("flex size-5 shrink-0 items-center justify-center rounded-full", done ? "bg-[#047857]" : active ? "animate-spin border-2 border-dashed border-[#0F172A]" : "border-[1.5px] border-[#CBD5E1]")}
              style={active ? { animationDuration: "1.4s" } : undefined}>
              {done && <Check size={11} className="text-white" />}
            </span>
            {t}
          </li>
        )
      })}
    </ol>
  )
}

function Fact({ k, v, lock, hex, fmt, onChange }: { k: string; v: number | null; lock: boolean; hex: string; fmt?: (n: number) => string; onChange: (n: number | null) => void }) {
  return (
    <label className="flex flex-col gap-[2px] rounded-[10px] bg-[#FAFAF7] px-2 py-[10px] text-center">
      <input value={lock ? dash(v, fmt) : v ?? ""} readOnly={lock} inputMode="numeric" aria-label={k}
        onChange={(e) => { const n = e.target.value.replace(/\D/g, ""); onChange(n ? Number(n) : null) }}
        className="w-full bg-transparent p-0 text-center text-[17px] font-bold outline-none"
        style={{ color: v == null && lock ? "#5E636B" : "#0F172A", borderBottom: lock ? "1.5px solid transparent" : `1.5px solid ${hex}` }} />
      <span className="text-[11px] text-[#64748B]">{k}</span>
    </label>
  )
}

function missingNote(r: Record_) {
  const miss = ([["beds", "Beds"], ["baths", "Baths"], ["sqft", "Sq ft"], ["yearBuilt", "Year built"]] as const).filter(([key]) => r[key] == null).map(([, l]) => l)
  if (!miss.length) return "From the county record."
  return `From the county record. ${miss.join(" and ")} ${miss.length > 1 ? "weren't" : "wasn't"} listed — that's fine.`
}

/** Pins the cover at 816×1056 and scales it to the frame width (ResizeObserver). */
function CoverFrame({ children }: { children: ReactNode }) {
  const ref = useRef<HTMLDivElement>(null)
  const [scale, setScale] = useState(400 / 816)
  useEffect(() => {
    const el = ref.current; if (!el) return
    const ro = new ResizeObserver(([e]) => setScale(e.contentRect.width / 816)); ro.observe(el)
    return () => ro.disconnect()
  }, [])
  return <div ref={ref} className="absolute inset-0"><div style={{ width: 816, height: 1056, transform: `scale(${scale})`, transformOrigin: "0 0" }}>{children}</div></div>
}
