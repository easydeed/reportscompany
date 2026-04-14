"use client"

import { useEffect, useState } from "react"
import { useAccount, useMe } from "@/hooks/use-api"
import { useQueryClient } from "@tanstack/react-query"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  Palette,
  FileText,
  Mail,
  Save,
  Loader2,
  Download,
  Send,
  Check,
  Sparkles,
  Eye,
  Upload,
  User,
  Type,
  Building,
  Info,
} from "lucide-react"
import { useToast } from "@/components/ui/use-toast"
import { ImageUpload } from "@/components/ui/image-upload"
import { cn } from "@/lib/utils"
import { REPORT_TYPE_OPTIONS, type ReportType } from "@/lib/sample-report-data"
import {
  SharedEmailPreview,
  type PreviewReportType,
} from "@/components/shared/email-preview"

// ─── Theme definitions (mirror property-wizard/types.ts) ───

const THEMES = [
  { id: 1, name: "Classic", style: "Timeless & Professional", font: "Merriweather + System Sans", gradient: "linear-gradient(135deg, #1B365D 0%, #2D5F8A 100%)", previewImage: "/previews/1.jpg" },
  { id: 2, name: "Modern", style: "Clean & Contemporary", font: "DM Sans", gradient: "linear-gradient(135deg, #1A1F36 0%, #FF6B5B 100%)", previewImage: "/previews/2.jpg" },
  { id: 3, name: "Elegant", style: "Sophisticated & Refined", font: "Playfair Display", gradient: "linear-gradient(135deg, #1a1a1a 0%, #C9A962 100%)", previewImage: "/previews/3.jpg" },
  { id: 4, name: "Teal", style: "Vibrant & Modern", font: "Montserrat", gradient: "linear-gradient(135deg, #18235c 0%, #34d1c3 100%)", previewImage: "/previews/4.jpg" },
  { id: 5, name: "Bold", style: "Impactful & Striking", font: "Clash Display + DM Sans", gradient: "linear-gradient(135deg, #15216E 0%, #D69649 100%)", previewImage: "/previews/5.jpg" },
]

const COLOR_PRESETS = [
  { name: "Indigo", primary: "#4F46E5", accent: "#F59E0B" },
  { name: "Ocean", primary: "#0EA5E9", accent: "#10B981" },
  { name: "Crimson", primary: "#DC2626", accent: "#1D4ED8" },
  { name: "Forest", primary: "#059669", accent: "#D97706" },
  { name: "Midnight", primary: "#1E293B", accent: "#818CF8" },
  { name: "Royal", primary: "#7C3AED", accent: "#EC4899" },
]

const PREVIEW_REPORT_TYPES: { value: PreviewReportType; label: string }[] = [
  { value: "market_snapshot", label: "Market Update" },
  { value: "new_listings_gallery", label: "New Listings" },
  { value: "closed", label: "Closed Sales" },
  { value: "inventory", label: "Inventory" },
  { value: "featured_listings", label: "Featured" },
]

type BrandingData = {
  display_name: string
  tagline: string
  primary_color: string
  accent_color: string
  default_theme_id: number
  header_logo_url: string | null
  footer_logo_url: string | null
  agent_name: string
  agent_title: string
  agent_phone: string
  agent_email: string
  agent_photo_url: string | null
}

export default function BrandingPage() {
  const { data: accountData, isLoading: accountLoading } = useAccount()
  const { data: meData, isLoading: meLoading } = useMe()
  const queryClient = useQueryClient()
  const isLoading = accountLoading || meLoading

  const [formInitialized, setFormInitialized] = useState(false)
  const [saving, setSaving] = useState(false)
  const { toast } = useToast()

  const [branding, setBranding] = useState<BrandingData>({
    display_name: "",
    tagline: "",
    primary_color: "#818CF8",
    accent_color: "#F59E0B",
    default_theme_id: 4,
    header_logo_url: null,
    footer_logo_url: null,
    agent_name: "",
    agent_title: "",
    agent_phone: "",
    agent_email: "",
    agent_photo_url: null,
  })

  // Preview state
  const [previewMode, setPreviewMode] = useState<"email" | "property">("email")
  const [previewReportType, setPreviewReportType] = useState<PreviewReportType>("market_snapshot")

  // Test branding
  const [reportType, setReportType] = useState<ReportType>("market_snapshot")
  const [isDownloadingPdf, setIsDownloadingPdf] = useState(false)
  const [downloadSuccess, setDownloadSuccess] = useState<string | null>(null)
  const [testEmail, setTestEmail] = useState("")
  const [isSending, setIsSending] = useState(false)
  const [sendSuccess, setSendSuccess] = useState(false)

  useEffect(() => {
    if (accountData && meData && !formInitialized) {
      const acc = accountData as Record<string, any>
      const profile = meData as Record<string, any>
      const fullName = [profile.first_name, profile.last_name].filter(Boolean).join(" ")
      setBranding({
        display_name: acc.display_name || acc.name || "",
        tagline: "",
        primary_color: acc.primary_color || "#818CF8",
        accent_color: acc.secondary_color || "#F59E0B",
        default_theme_id: acc.default_theme_id || 4,
        header_logo_url: acc.logo_url || acc.email_logo_url || null,
        footer_logo_url: acc.footer_logo_url || acc.email_footer_logo_url || null,
        agent_name: fullName || "",
        agent_title: profile.job_title || "",
        agent_phone: profile.phone || "",
        agent_email: profile.email || "",
        agent_photo_url: profile.avatar_url || null,
      })
      setTestEmail(profile.email || "")
      setFormInitialized(true)
    }
  }, [accountData, meData, formInitialized])

  async function save() {
    setSaving(true)
    try {
      const [brandingRes, profileRes] = await Promise.all([
        fetch("/api/proxy/v1/account/branding", {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            display_name: branding.display_name || undefined,
            tagline: branding.tagline || undefined,
            primary_color: branding.primary_color,
            secondary_color: branding.accent_color,
            default_theme_id: branding.default_theme_id,
            logo_url: branding.header_logo_url,
            footer_logo_url: branding.footer_logo_url,
            email_logo_url: branding.header_logo_url,
            email_footer_logo_url: branding.footer_logo_url,
          }),
        }),
        fetch("/api/proxy/v1/users/me", {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            ...(branding.agent_name ? {
              first_name: branding.agent_name.split(" ")[0],
              last_name: branding.agent_name.split(" ").slice(1).join(" ") || undefined,
            } : {}),
            ...(branding.agent_title ? { job_title: branding.agent_title } : {}),
            ...(branding.agent_phone ? { phone: branding.agent_phone } : {}),
            ...(branding.agent_photo_url !== null ? { avatar_url: branding.agent_photo_url } : {}),
          }),
        }),
      ])
      if (!brandingRes.ok) throw new Error("Failed to save branding")
      if (!profileRes.ok) console.warn("Failed to save agent profile — branding saved OK")
      queryClient.invalidateQueries({ queryKey: ["account"] })
      queryClient.invalidateQueries({ queryKey: ["me"] })
      queryClient.invalidateQueries({ queryKey: ["branding"] })
      toast({ title: "Branding Saved", description: "Your branding has been updated successfully." })
    } catch {
      toast({ title: "Error", description: "Failed to save branding", variant: "destructive" })
    } finally {
      setSaving(false)
    }
  }

  async function handleDownloadPdf() {
    setIsDownloadingPdf(true)
    setDownloadSuccess(null)
    try {
      const response = await fetch("/api/proxy/v1/branding/sample-pdf", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ report_type: reportType }),
      })
      if (!response.ok) throw new Error("Failed to generate PDF")
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement("a")
      link.href = url
      link.download = `sample-${reportType.replace(/_/g, "-")}.pdf`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
      setDownloadSuccess("pdf")
      setTimeout(() => setDownloadSuccess(null), 3000)
    } catch (err) {
      toast({ title: "Error", description: err instanceof Error ? err.message : "Download failed", variant: "destructive" })
    } finally {
      setIsDownloadingPdf(false)
    }
  }

  async function handleSendTestEmail() {
    if (!testEmail || !testEmail.includes("@")) {
      toast({ title: "Error", description: "Please enter a valid email", variant: "destructive" })
      return
    }
    setIsSending(true)
    setSendSuccess(false)
    try {
      const response = await fetch("/api/proxy/v1/branding/test-email", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: testEmail, report_type: reportType }),
      })
      if (!response.ok) throw new Error("Failed to send email")
      setSendSuccess(true)
      setTimeout(() => setSendSuccess(false), 5000)
    } catch (err) {
      toast({ title: "Error", description: err instanceof Error ? err.message : "Send failed", variant: "destructive" })
    } finally {
      setIsSending(false)
    }
  }

  const update = (patch: Partial<BrandingData>) => setBranding((prev) => ({ ...prev, ...patch }))
  const selectedTheme = THEMES.find((t) => t.id === branding.default_theme_id) || THEMES[3]

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-24">
        <div className="text-center">
          <Loader2 className="w-8 h-8 animate-spin text-indigo-600 mx-auto mb-4" />
          <p className="text-muted-foreground text-sm">Loading branding settings...</p>
        </div>
      </div>
    )
  }

  // Company reps inherit branding — show read-only view
  const acc = accountData as Record<string, any> | undefined
  const isCompanyRep = acc?.account_type === "INDUSTRY_AFFILIATE" && !!acc?.parent_account_id
  if (isCompanyRep) {
    const companyName = acc?.parent_company_name || "your company"
    return (
      <div className="max-w-2xl mx-auto space-y-6">
        <div>
          <h1 className="text-xl font-semibold tracking-tight text-foreground">Branding</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Your branding is managed by your company
          </p>
        </div>

        <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 dark:bg-blue-950/30 dark:border-blue-800">
          <div className="flex items-start gap-3">
            <Building className="w-5 h-5 text-blue-600 dark:text-blue-400 mt-0.5 shrink-0" />
            <p className="text-sm text-blue-800 dark:text-blue-300">
              Your branding is inherited from <strong>{companyName}</strong>.
              Logos, colors, and display name are set at the company level and cascade
              to all reports generated by you and your agents. Contact your company admin
              to make changes.
            </p>
          </div>
        </div>

        <div className="rounded-xl border bg-card p-6 space-y-5">
          <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">Current Branding</h2>

          {acc?.logo_url && (
            <div>
              <label className="text-xs font-medium text-muted-foreground uppercase">Company Logo</label>
              <img src={acc.logo_url} alt="Company logo" className="mt-2 max-h-12 object-contain" />
            </div>
          )}

          <div className="flex gap-6">
            {acc?.primary_color && (
              <div>
                <label className="text-xs font-medium text-muted-foreground uppercase">Primary Color</label>
                <div className="mt-1.5 flex items-center gap-2">
                  <div className="w-8 h-8 rounded-lg border" style={{ backgroundColor: acc.primary_color }} />
                  <span className="text-sm text-muted-foreground font-mono">{acc.primary_color}</span>
                </div>
              </div>
            )}
            {acc?.secondary_color && (
              <div>
                <label className="text-xs font-medium text-muted-foreground uppercase">Accent Color</label>
                <div className="mt-1.5 flex items-center gap-2">
                  <div className="w-8 h-8 rounded-lg border" style={{ backgroundColor: acc.secondary_color }} />
                  <span className="text-sm text-muted-foreground font-mono">{acc.secondary_color}</span>
                </div>
              </div>
            )}
          </div>

          {(acc?.display_name || acc?.name) && (
            <div>
              <label className="text-xs font-medium text-muted-foreground uppercase">Display Name</label>
              <p className="mt-1 text-sm font-medium">{acc.display_name || acc.name}</p>
            </div>
          )}
        </div>

        <div className="flex items-start gap-2 text-xs text-muted-foreground">
          <Info className="w-3.5 h-3.5 mt-0.5 shrink-0" />
          <p>
            You can still customize your profile photo, name, and contact info from{" "}
            <a href="/app/settings/profile" className="text-indigo-600 underline dark:text-indigo-400">
              Settings → Profile
            </a>. These appear alongside your company branding on agent reports.
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-[1400px] mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-semibold tracking-tight text-foreground">Branding</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Control how your reports and emails look across every touchpoint
          </p>
        </div>
        <Button size="sm" onClick={save} disabled={saving}>
          {saving ? (
            <><Loader2 className="w-4 h-4 animate-spin mr-2" />Saving...</>
          ) : (
            <><Save className="w-4 h-4 mr-2" />Save Changes</>
          )}
        </Button>
      </div>

      {/* Two-column layout: Controls left, Preview right */}
      <div className="grid lg:grid-cols-[1fr_420px] gap-6">
        {/* ─── Left: Controls ─── */}
        <div className="space-y-5">

          {/* Brand Identity */}
          <Section icon={<Sparkles className="w-4 h-4 text-indigo-600" />} iconBg="bg-indigo-50" title="Brand Identity" subtitle="Your display name and tagline">
            <div className="grid sm:grid-cols-2 gap-4">
              <div className="space-y-1.5">
                <Label className="text-xs font-medium">Display Name</Label>
                <Input
                  value={branding.display_name}
                  onChange={(e) => update({ display_name: e.target.value })}
                  placeholder="Acme Realty"
                  className="h-10"
                />
              </div>
              <div className="space-y-1.5">
                <Label className="text-xs font-medium">Tagline <span className="text-muted-foreground">(optional)</span></Label>
                <Input
                  value={branding.tagline}
                  onChange={(e) => update({ tagline: e.target.value })}
                  placeholder="Your Home Expert"
                  className="h-10"
                />
              </div>
            </div>
          </Section>

          {/* Colors */}
          <Section icon={<Palette className="w-4 h-4 text-violet-600" />} iconBg="bg-violet-50" title="Brand Colors" subtitle="Primary and accent colors for all reports and emails">
            <div className="grid sm:grid-cols-2 gap-5">
              <ColorPicker
                label="Primary Color"
                help="Headers, gradients, text accents"
                value={branding.primary_color}
                onChange={(v) => update({ primary_color: v })}
              />
              <ColorPicker
                label="Accent Color"
                help="Buttons, highlights, CTAs"
                value={branding.accent_color}
                onChange={(v) => update({ accent_color: v })}
              />
            </div>

            {/* Gradient preview */}
            <div className="mt-4">
              <Label className="text-xs text-muted-foreground mb-1.5 block">Gradient Preview</Label>
              <div
                className="h-12 rounded-lg shadow-inner"
                style={{ background: `linear-gradient(135deg, ${branding.primary_color} 0%, ${branding.accent_color} 100%)` }}
              />
            </div>

            {/* Presets */}
            <div className="mt-4">
              <Label className="text-xs text-muted-foreground mb-2 block">Quick Presets</Label>
              <div className="grid grid-cols-3 sm:grid-cols-6 gap-2">
                {COLOR_PRESETS.map((preset) => {
                  const active = branding.primary_color === preset.primary && branding.accent_color === preset.accent
                  return (
                    <button
                      key={preset.name}
                      onClick={() => update({ primary_color: preset.primary, accent_color: preset.accent })}
                      className={cn(
                        "group relative rounded-lg border-2 p-2.5 transition-all hover:scale-[1.03]",
                        active ? "border-indigo-500 bg-indigo-50/50 shadow-md" : "border-border hover:border-indigo-200"
                      )}
                    >
                      <div className="flex gap-1.5 mb-1.5">
                        <div className="w-5 h-5 rounded" style={{ backgroundColor: preset.primary }} />
                        <div className="w-5 h-5 rounded" style={{ backgroundColor: preset.accent }} />
                      </div>
                      <p className="text-[10px] font-medium text-foreground">{preset.name}</p>
                      {active && <Check className="absolute top-1 right-1 w-3.5 h-3.5 text-indigo-600" />}
                    </button>
                  )
                })}
              </div>
            </div>
          </Section>

          {/* Default Property Theme */}
          <Section icon={<Type className="w-4 h-4 text-teal-600" />} iconBg="bg-teal-50" title="Default Property Theme" subtitle="New property reports will start with this theme">
            <div className="grid grid-cols-5 gap-2">
              {THEMES.map((theme) => {
                const active = branding.default_theme_id === theme.id
                return (
                  <button
                    key={theme.id}
                    onClick={() => update({ default_theme_id: theme.id })}
                    className={cn(
                      "group relative rounded-lg border-2 overflow-hidden transition-all hover:scale-[1.02]",
                      active ? "border-indigo-500 shadow-lg ring-2 ring-indigo-200" : "border-border hover:border-indigo-200"
                    )}
                  >
                    <div className="aspect-[3/4] overflow-hidden">
                      {theme.previewImage ? (
                        <img src={theme.previewImage} alt={theme.name} className="w-full h-full object-cover object-top" />
                      ) : (
                        <div className="w-full h-full" style={{ background: theme.gradient }} />
                      )}
                    </div>
                    <div className="p-1.5 bg-white">
                      <p className="text-[10px] font-semibold text-center">{theme.name}</p>
                    </div>
                    {active && (
                      <div className="absolute top-1 right-1 w-5 h-5 rounded-full bg-indigo-500 flex items-center justify-center">
                        <Check className="w-3 h-3 text-white" />
                      </div>
                    )}
                  </button>
                )
              })}
            </div>
            <div className="mt-3 flex items-center gap-2 text-xs text-muted-foreground">
              <Type className="w-3.5 h-3.5" />
              <span>
                <strong>{selectedTheme.name}</strong> — {selectedTheme.font}
              </span>
            </div>
          </Section>

          {/* Logos */}
          <Section icon={<FileText className="w-4 h-4 text-rose-600" />} iconBg="bg-rose-50" title="Logos" subtitle="Used in PDF reports and emails">
            <div className="grid sm:grid-cols-2 gap-5">
              <div className="space-y-2">
                <Label className="text-xs font-medium">Header Logo <span className="text-muted-foreground">(light version)</span></Label>
                <p className="text-[11px] text-muted-foreground -mt-1">For gradient backgrounds. PNG/SVG with transparent bg.</p>
                <div className="flex items-center gap-3">
                  <div
                    className="w-20 h-14 rounded-lg flex items-center justify-center p-1.5"
                    style={{ background: `linear-gradient(135deg, ${branding.primary_color} 0%, ${branding.accent_color} 100%)` }}
                  >
                    {branding.header_logo_url ? (
                      <img src={branding.header_logo_url} className="max-h-full max-w-full object-contain" alt="Header logo" />
                    ) : (
                      <Upload className="w-5 h-5 text-white/40" />
                    )}
                  </div>
                  <div className="flex-1">
                    <ImageUpload
                      label=""
                      value={branding.header_logo_url}
                      onChange={(url) => update({ header_logo_url: url })}
                      assetType="logo"
                      aspectRatio="wide"
                      helpText=""
                    />
                  </div>
                </div>
              </div>
              <div className="space-y-2">
                <Label className="text-xs font-medium">Footer Logo <span className="text-muted-foreground">(dark version)</span></Label>
                <p className="text-[11px] text-muted-foreground -mt-1">For light backgrounds. PNG/SVG with transparent bg.</p>
                <div className="flex items-center gap-3">
                  <div className="w-20 h-14 rounded-lg bg-stone-50 border border-border flex items-center justify-center p-1.5">
                    {branding.footer_logo_url ? (
                      <img src={branding.footer_logo_url} className="max-h-full max-w-full object-contain" alt="Footer logo" />
                    ) : (
                      <Upload className="w-5 h-5 text-muted-foreground/30" />
                    )}
                  </div>
                  <div className="flex-1">
                    <ImageUpload
                      label=""
                      value={branding.footer_logo_url}
                      onChange={(url) => update({ footer_logo_url: url })}
                      assetType="logo"
                      aspectRatio="wide"
                      helpText=""
                    />
                  </div>
                </div>
              </div>
            </div>
          </Section>

          {/* Agent Info */}
          <Section icon={<User className="w-4 h-4 text-amber-600" />} iconBg="bg-amber-50" title="Agent Info" subtitle="Appears in email footers and report cover pages">
            <div className="grid sm:grid-cols-2 gap-4">
              <div className="space-y-1.5">
                <Label className="text-xs font-medium">Full Name</Label>
                <Input value={branding.agent_name} onChange={(e) => update({ agent_name: e.target.value })} placeholder="Sarah Chen" className="h-10" />
              </div>
              <div className="space-y-1.5">
                <Label className="text-xs font-medium">Title</Label>
                <Input value={branding.agent_title} onChange={(e) => update({ agent_title: e.target.value })} placeholder="Senior Realtor" className="h-10" />
              </div>
              <div className="space-y-1.5">
                <Label className="text-xs font-medium">Phone</Label>
                <Input value={branding.agent_phone} onChange={(e) => update({ agent_phone: e.target.value })} placeholder="(310) 555-1234" className="h-10" />
              </div>
              <div className="space-y-1.5">
                <Label className="text-xs font-medium">Email</Label>
                <Input value={branding.agent_email} onChange={(e) => update({ agent_email: e.target.value })} placeholder="sarah@acmerealty.com" className="h-10" />
              </div>
            </div>
            <div className="mt-3 space-y-1.5">
              <Label className="text-xs font-medium">Agent Photo</Label>
              <ImageUpload
                label=""
                value={branding.agent_photo_url}
                onChange={(url) => update({ agent_photo_url: url })}
                assetType="headshot"
                aspectRatio="square"
                helpText="Square photo, at least 200×200px"
              />
            </div>
          </Section>
        </div>

        {/* ─── Right: Live Preview + Actions ─── */}
        <div className="lg:sticky lg:top-6 lg:self-start space-y-4">
          {/* Preview Card */}
          <div className="bg-card border border-border rounded-xl shadow-[var(--shadow-card)] overflow-hidden">
            <div className="flex items-center justify-between px-4 py-3 border-b border-border bg-muted/30">
              <div className="flex items-center gap-2">
                <div className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Live Preview</h3>
              </div>
              <div className="flex gap-1 bg-muted rounded-md p-0.5">
                <button
                  onClick={() => setPreviewMode("email")}
                  className={cn("px-2.5 py-1 rounded text-[10px] font-medium transition-colors", previewMode === "email" ? "bg-white shadow-sm text-foreground" : "text-muted-foreground hover:text-foreground")}
                >
                  <Mail className="w-3 h-3 inline mr-1" />Email
                </button>
                <button
                  onClick={() => setPreviewMode("property")}
                  className={cn("px-2.5 py-1 rounded text-[10px] font-medium transition-colors", previewMode === "property" ? "bg-white shadow-sm text-foreground" : "text-muted-foreground hover:text-foreground")}
                >
                  <FileText className="w-3 h-3 inline mr-1" />PDF
                </button>
              </div>
            </div>

            {/* Report type switcher for email preview */}
            {previewMode === "email" && (
              <div className="flex gap-1 px-4 py-2 border-b border-border bg-muted/10 overflow-x-auto">
                {PREVIEW_REPORT_TYPES.map((rt) => (
                  <button
                    key={rt.value}
                    onClick={() => setPreviewReportType(rt.value)}
                    className={cn(
                      "whitespace-nowrap px-2 py-1 rounded text-[10px] font-medium transition-colors",
                      previewReportType === rt.value ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:bg-muted"
                    )}
                  >
                    {rt.label}
                  </button>
                ))}
              </div>
            )}

            <div className="p-4 bg-stone-100/50">
              {previewMode === "email" ? (
                <SharedEmailPreview
                  primaryColor={branding.primary_color}
                  accentColor={branding.accent_color}
                  headerLogoUrl={branding.header_logo_url}
                  displayName={branding.display_name}
                  agentName={branding.agent_name || "Agent Name"}
                  agentTitle={branding.agent_title || null}
                  agentPhone={branding.agent_phone || null}
                  agentEmail={branding.agent_email || null}
                  agentPhotoUrl={branding.agent_photo_url}
                  reportType={previewReportType}
                  areaName="Los Angeles, CA"
                  lookbackDays={30}
                  scale={0.95}
                />
              ) : (
                <PropertyPreviewMini
                  theme={selectedTheme}
                  headerLogoUrl={branding.header_logo_url}
                  footerLogoUrl={branding.footer_logo_url}
                  agentName={branding.agent_name}
                  companyName={branding.display_name}
                  primaryColor={branding.primary_color}
                  accentColor={branding.accent_color}
                />
              )}
            </div>
          </div>

          {/* Actions Card */}
          <div className="bg-card border border-border rounded-xl shadow-[var(--shadow-card)] overflow-hidden">
            <div className="px-4 py-3 border-b border-border bg-muted/30 flex items-center gap-2">
              <Eye className="w-4 h-4 text-emerald-600" />
              <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Test Your Branding</h3>
            </div>
            <div className="p-4 space-y-4">
              <div className="space-y-1.5">
                <Label className="text-xs font-medium text-muted-foreground">Report Type</Label>
                <Select value={reportType} onValueChange={(v) => setReportType(v as ReportType)}>
                  <SelectTrigger className="h-9 text-xs"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    {REPORT_TYPE_OPTIONS.map((t) => (
                      <SelectItem key={t.value} value={t.value}>{t.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <Button
                onClick={handleDownloadPdf}
                disabled={isDownloadingPdf}
                variant="outline"
                className="w-full h-9 text-xs"
              >
                {isDownloadingPdf ? <Loader2 className="w-3.5 h-3.5 animate-spin mr-2" /> : downloadSuccess === "pdf" ? <Check className="w-3.5 h-3.5 mr-2" /> : <Download className="w-3.5 h-3.5 mr-2" />}
                {downloadSuccess === "pdf" ? "Downloaded!" : "Download Sample PDF"}
              </Button>

              <div className="relative py-1">
                <div className="absolute inset-0 flex items-center"><div className="w-full border-t border-border" /></div>
                <div className="relative flex justify-center"><span className="bg-card px-2 text-[10px] text-muted-foreground">or</span></div>
              </div>

              <div className="flex gap-2">
                <Input
                  type="email"
                  value={testEmail}
                  onChange={(e) => setTestEmail(e.target.value)}
                  placeholder="your@email.com"
                  className="flex-1 h-9 text-xs"
                />
                <Button onClick={handleSendTestEmail} disabled={isSending} className={cn("h-9 w-9 p-0", sendSuccess && "bg-emerald-600 hover:bg-emerald-700")}>
                  {isSending ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : sendSuccess ? <Check className="w-3.5 h-3.5" /> : <Send className="w-3.5 h-3.5" />}
                </Button>
              </div>
              {sendSuccess && (
                <p className="text-[11px] text-emerald-600 flex items-center gap-1"><Check className="w-3 h-3" />Test email sent!</p>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

// ─── Helper components ───

function Section({
  icon,
  iconBg,
  title,
  subtitle,
  children,
}: {
  icon: React.ReactNode
  iconBg: string
  title: string
  subtitle: string
  children: React.ReactNode
}) {
  return (
    <div className="bg-card border border-border rounded-xl shadow-[var(--shadow-card)] overflow-hidden">
      <div className="px-5 py-3.5 border-b border-border bg-muted/30 flex items-center gap-3">
        <div className={cn("w-8 h-8 rounded-lg flex items-center justify-center", iconBg)}>
          {icon}
        </div>
        <div>
          <h3 className="text-sm font-semibold text-foreground">{title}</h3>
          <p className="text-xs text-muted-foreground">{subtitle}</p>
        </div>
      </div>
      <div className="p-5">{children}</div>
    </div>
  )
}

function ColorPicker({
  label,
  help,
  value,
  onChange,
}: {
  label: string
  help: string
  value: string
  onChange: (v: string) => void
}) {
  return (
    <div className="space-y-2">
      <Label className="text-xs font-medium">{label}</Label>
      <p className="text-[11px] text-muted-foreground -mt-1">{help}</p>
      <div className="flex gap-2.5">
        <div
          className="w-14 h-10 rounded-lg border-2 border-border cursor-pointer relative shadow-inner flex-shrink-0 transition-all hover:scale-105"
          style={{ backgroundColor: value }}
        >
          <input
            type="color"
            value={value}
            onChange={(e) => onChange(e.target.value)}
            className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
          />
        </div>
        <Input
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className="font-mono text-xs uppercase h-10 flex-1"
          maxLength={7}
        />
      </div>
    </div>
  )
}

function PropertyPreviewMini({
  theme,
  headerLogoUrl,
  footerLogoUrl,
  agentName,
  companyName,
  primaryColor,
  accentColor,
}: {
  theme: (typeof THEMES)[number]
  headerLogoUrl: string | null
  footerLogoUrl: string | null
  agentName: string
  companyName: string
  primaryColor: string
  accentColor: string
}) {
  return (
    <div className="bg-white rounded-xl shadow-lg overflow-hidden border border-stone-200 max-w-sm mx-auto">
      {/* Cover page mini */}
      <div className="aspect-[3/4] relative overflow-hidden">
        {theme.previewImage ? (
          <img src={theme.previewImage} alt={theme.name} className="w-full h-full object-cover object-top" />
        ) : (
          <div className="w-full h-full" style={{ background: theme.gradient }}>
            <div className="absolute inset-0 flex flex-col items-center justify-center text-white p-4">
              {headerLogoUrl && (
                <img src={headerLogoUrl} alt="" className="h-8 w-auto mb-3 object-contain" />
              )}
              <div className="text-lg font-bold text-center">Property Report</div>
              <div className="text-xs opacity-70 mt-1">123 Main Street</div>
            </div>
          </div>
        )}
      </div>
      {/* Footer bar */}
      <div className="px-4 py-3 bg-stone-50 border-t border-stone-100 flex items-center justify-between">
        <div className="text-xs text-stone-600">{agentName || "Agent Name"}</div>
        {footerLogoUrl ? (
          <img src={footerLogoUrl} alt="" className="h-5 w-auto max-w-[70px] object-contain" />
        ) : (
          <div className="text-[10px] font-semibold" style={{ color: primaryColor }}>
            {companyName || "Your Brand"}
          </div>
        )}
      </div>
    </div>
  )
}
