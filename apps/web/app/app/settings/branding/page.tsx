"use client"

import { useEffect, useState } from "react"
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
  Lightbulb,
  Sparkles,
  Eye,
} from "lucide-react"
import { useToast } from "@/components/ui/use-toast"
import { ImageUpload } from "@/components/ui/image-upload"
import { cn } from "@/lib/utils"
import { REPORT_TYPE_OPTIONS, ReportType } from "@/lib/sample-report-data"

type BrandingData = {
  primary_color: string
  accent_color: string
  pdf_header_logo_url: string | null
  pdf_footer_logo_url: string | null
  email_header_logo_url: string | null
  email_footer_logo_url: string | null
}

export default function BrandingPage() {
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const { toast } = useToast()

  const [branding, setBranding] = useState<BrandingData>({
    primary_color: "#818CF8",
    accent_color: "#F59E0B",
    pdf_header_logo_url: null,
    pdf_footer_logo_url: null,
    email_header_logo_url: null,
    email_footer_logo_url: null,
  })

  // Test branding state
  const [reportType, setReportType] = useState<ReportType>("market_snapshot")
  const [isDownloadingPdf, setIsDownloadingPdf] = useState(false)
  const [isDownloadingJpg, setIsDownloadingJpg] = useState(false)
  const [downloadSuccess, setDownloadSuccess] = useState<string | null>(null)
  const [testEmail, setTestEmail] = useState("")
  const [isSending, setIsSending] = useState(false)
  const [sendSuccess, setSendSuccess] = useState(false)

  // User profile for preview
  const [userName, setUserName] = useState("")
  const [companyName, setCompanyName] = useState("")

  useEffect(() => {
    loadData()
  }, [])

  async function loadData() {
    setLoading(true)
    try {
      const [accountRes, profileRes] = await Promise.all([
        fetch("/api/proxy/v1/account", { cache: "no-store", credentials: "include" }),
        fetch("/api/proxy/v1/users/me", { cache: "no-store", credentials: "include" }),
      ])

      if (accountRes.ok) {
        const data = await accountRes.json()
        setBranding({
          primary_color: data.primary_color || "#818CF8",
          accent_color: data.secondary_color || "#F59E0B",
          pdf_header_logo_url: data.logo_url || null,
          pdf_footer_logo_url: data.footer_logo_url || null,
          email_header_logo_url: data.email_logo_url || null,
          email_footer_logo_url: data.email_footer_logo_url || null,
        })
      }

      if (profileRes.ok) {
        const profile = await profileRes.json()
        const fullName = [profile.first_name, profile.last_name].filter(Boolean).join(" ")
        setUserName(fullName || profile.email?.split("@")[0] || "User")
        setCompanyName(profile.company_name || "")
        setTestEmail(profile.email || "")
      }
    } catch (error) {
      console.error("Failed to load branding:", error)
      toast({
        title: "Error",
        description: "Failed to load branding settings",
        variant: "destructive",
      })
    } finally {
      setLoading(false)
    }
  }

  async function save() {
    setSaving(true)
    try {
      const res = await fetch("/api/proxy/v1/account/branding", {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          primary_color: branding.primary_color,
          secondary_color: branding.accent_color,
          logo_url: branding.pdf_header_logo_url,
          footer_logo_url: branding.pdf_footer_logo_url,
          email_logo_url: branding.email_header_logo_url,
          email_footer_logo_url: branding.email_footer_logo_url,
        }),
      })

      if (!res.ok) throw new Error("Failed to save branding")

      toast({
        title: "Branding Saved",
        description: "Your branding has been updated successfully.",
      })
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to save branding",
        variant: "destructive",
      })
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

      if (!response.ok) {
        const data = await response.json().catch(() => ({}))
        throw new Error(data.error || data.detail || "Failed to generate PDF")
      }

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
      toast({
        title: "Error",
        description: err instanceof Error ? err.message : "Download failed",
        variant: "destructive",
      })
    } finally {
      setIsDownloadingPdf(false)
    }
  }

  async function handleDownloadJpg() {
    setIsDownloadingJpg(true)
    setDownloadSuccess(null)
    try {
      const response = await fetch("/api/proxy/v1/branding/sample-jpg", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ report_type: reportType }),
      })

      if (!response.ok) {
        const data = await response.json().catch(() => ({}))
        throw new Error(data.error || data.detail || "Failed to generate image")
      }

      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement("a")
      link.href = url
      link.download = `sample-${reportType.replace(/_/g, "-")}-social.jpg`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)

      setDownloadSuccess("jpg")
      setTimeout(() => setDownloadSuccess(null), 3000)
    } catch (err) {
      toast({
        title: "Error",
        description: err instanceof Error ? err.message : "Download failed",
        variant: "destructive",
      })
    } finally {
      setIsDownloadingJpg(false)
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

      if (!response.ok) {
        const data = await response.json().catch(() => ({}))
        throw new Error(data.error || data.detail || "Failed to send email")
      }

      setSendSuccess(true)
      setTimeout(() => setSendSuccess(false), 5000)
    } catch (err) {
      toast({
        title: "Error",
        description: err instanceof Error ? err.message : "Send failed",
        variant: "destructive",
      })
    } finally {
      setIsSending(false)
    }
  }

  const primaryColor = branding.primary_color
  const accentColor = branding.accent_color

  if (loading) {
    return (
      <div className="flex items-center justify-center py-24">
        <div className="text-center">
          <Loader2 className="w-8 h-8 animate-spin text-indigo-600 mx-auto mb-4" />
          <p className="text-muted-foreground text-sm">Loading branding settings...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-5xl">
      {/* Page Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-semibold tracking-tight text-foreground">Branding</h1>
          <p className="text-[13px] text-muted-foreground mt-0.5">
            Customize how your reports and emails look.
          </p>
        </div>
        <Button onClick={save} disabled={saving} size="sm">
          {saving ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin mr-1.5" />
              Saving...
            </>
          ) : (
            <>
              <Save className="w-4 h-4 mr-1.5" />
              Save Changes
            </>
          )}
        </Button>
      </div>

      {/* Two-column layout */}
      <div className="grid lg:grid-cols-[1fr_340px] gap-6">
        {/* Left: Configuration */}
        <div className="space-y-4">
          {/* Brand Colors Card */}
          <div className="bg-card border border-border rounded-xl shadow-[var(--shadow-card)] overflow-hidden">
            <div className="px-5 py-3 border-b border-border bg-muted/30 flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-indigo-50 flex items-center justify-center">
                <Palette className="w-4 h-4 text-indigo-600" />
              </div>
              <div>
                <h3 className="text-[13px] font-semibold text-foreground">Brand Colors</h3>
                <p className="text-[11px] text-muted-foreground">Used throughout reports and emails</p>
              </div>
            </div>
            <div className="p-5 space-y-5">
              <div className="grid sm:grid-cols-2 gap-5">
                <div className="space-y-2">
                  <Label className="text-xs font-medium text-muted-foreground">Primary Color</Label>
                  <p className="text-[11px] text-muted-foreground -mt-1">Headers, ribbons, backgrounds</p>
                  <div className="flex gap-2">
                    <div
                      className="w-12 h-9 rounded-lg border-2 border-border cursor-pointer relative shadow-sm flex-shrink-0 transition-shadow hover:shadow-md"
                      style={{ backgroundColor: primaryColor }}
                    >
                      <input
                        type="color"
                        value={primaryColor}
                        onChange={(e) => setBranding({ ...branding, primary_color: e.target.value })}
                        className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                      />
                    </div>
                    <Input
                      value={primaryColor}
                      onChange={(e) => setBranding({ ...branding, primary_color: e.target.value })}
                      className="font-mono text-sm uppercase h-9"
                      maxLength={7}
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label className="text-xs font-medium text-muted-foreground">Accent Color</Label>
                  <p className="text-[11px] text-muted-foreground -mt-1">Buttons, highlights, CTAs</p>
                  <div className="flex gap-2">
                    <div
                      className="w-12 h-9 rounded-lg border-2 border-border cursor-pointer relative shadow-sm flex-shrink-0 transition-shadow hover:shadow-md"
                      style={{ backgroundColor: accentColor }}
                    >
                      <input
                        type="color"
                        value={accentColor}
                        onChange={(e) => setBranding({ ...branding, accent_color: e.target.value })}
                        className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                      />
                    </div>
                    <Input
                      value={accentColor}
                      onChange={(e) => setBranding({ ...branding, accent_color: e.target.value })}
                      className="font-mono text-sm uppercase h-9"
                      maxLength={7}
                    />
                  </div>
                </div>
              </div>

              {/* Gradient preview */}
              <div
                className="h-2 rounded-full"
                style={{ background: `linear-gradient(90deg, ${primaryColor} 0%, ${accentColor} 100%)` }}
              />
            </div>
          </div>

          {/* PDF Logos Card */}
          <div className="bg-card border border-border rounded-xl shadow-[var(--shadow-card)] overflow-hidden">
            <div className="px-5 py-3 border-b border-border bg-muted/30 flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-red-50 flex items-center justify-center">
                <FileText className="w-4 h-4 text-red-600" />
              </div>
              <div>
                <h3 className="text-[13px] font-semibold text-foreground">PDF Logos</h3>
                <p className="text-[11px] text-muted-foreground">Logos for downloadable PDF reports</p>
              </div>
            </div>
            <div className="p-5">
              <div className="grid sm:grid-cols-2 gap-5">
                <div className="space-y-2">
                  <Label className="text-xs font-medium text-muted-foreground">Header Logo</Label>
                  <p className="text-[11px] text-muted-foreground -mt-1">Light/white version for gradient</p>
                  <ImageUpload
                    label=""
                    value={branding.pdf_header_logo_url}
                    onChange={(url) => setBranding({ ...branding, pdf_header_logo_url: url })}
                    assetType="logo"
                    aspectRatio="wide"
                    helpText="PNG/SVG, transparent bg"
                  />
                </div>
                <div className="space-y-2">
                  <Label className="text-xs font-medium text-muted-foreground">Footer Logo</Label>
                  <p className="text-[11px] text-muted-foreground -mt-1">Standard/dark version</p>
                  <ImageUpload
                    label=""
                    value={branding.pdf_footer_logo_url}
                    onChange={(url) => setBranding({ ...branding, pdf_footer_logo_url: url })}
                    assetType="logo"
                    aspectRatio="wide"
                    helpText="PNG/SVG, transparent bg"
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Email Logos Card */}
          <div className="bg-card border border-border rounded-xl shadow-[var(--shadow-card)] overflow-hidden">
            <div className="px-5 py-3 border-b border-border bg-muted/30 flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-indigo-50 flex items-center justify-center">
                <Mail className="w-4 h-4 text-indigo-600" />
              </div>
              <div>
                <h3 className="text-[13px] font-semibold text-foreground">Email Logos</h3>
                <p className="text-[11px] text-muted-foreground">Logos for email reports</p>
              </div>
            </div>
            <div className="p-5 space-y-4">
              <div className="grid sm:grid-cols-2 gap-5">
                <div className="space-y-2">
                  <Label className="text-xs font-medium text-muted-foreground">Header Logo</Label>
                  <ImageUpload
                    label=""
                    value={branding.email_header_logo_url}
                    onChange={(url) => setBranding({ ...branding, email_header_logo_url: url })}
                    assetType="logo"
                    aspectRatio="wide"
                    helpText=""
                  />
                </div>
                <div className="space-y-2">
                  <Label className="text-xs font-medium text-muted-foreground">Footer Logo</Label>
                  <ImageUpload
                    label=""
                    value={branding.email_footer_logo_url}
                    onChange={(url) => setBranding({ ...branding, email_footer_logo_url: url })}
                    assetType="logo"
                    aspectRatio="wide"
                    helpText=""
                  />
                </div>
              </div>

              <div className="p-3 rounded-lg bg-amber-50 border border-amber-200">
                <p className="text-[11px] text-amber-800 flex items-start gap-2">
                  <Lightbulb className="w-4 h-4 flex-shrink-0 mt-0.5" />
                  Email logos may need to differ from PDF logos due to email client rendering.
                </p>
              </div>
            </div>
          </div>

          {/* Test Branding Card */}
          <div className="bg-card border border-border rounded-xl shadow-[var(--shadow-card)] overflow-hidden">
            <div className="px-5 py-3 border-b border-border bg-muted/30 flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-emerald-50 flex items-center justify-center">
                <Eye className="w-4 h-4 text-emerald-600" />
              </div>
              <div>
                <h3 className="text-[13px] font-semibold text-foreground">Test Your Branding</h3>
                <p className="text-[11px] text-muted-foreground">Download samples or send test email</p>
              </div>
            </div>
            <div className="p-5 space-y-4">
              <div className="space-y-1.5">
                <Label className="text-xs font-medium text-muted-foreground">Report Type</Label>
                <Select value={reportType} onValueChange={(v) => setReportType(v as ReportType)}>
                  <SelectTrigger className="h-9">
                    <SelectValue placeholder="Select report type" />
                  </SelectTrigger>
                  <SelectContent>
                    {REPORT_TYPE_OPTIONS.map((type) => (
                      <SelectItem key={type.value} value={type.value}>
                        {type.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="flex gap-2">
                <Button
                  onClick={handleDownloadPdf}
                  disabled={isDownloadingPdf}
                  variant="outline"
                  size="sm"
                  className={cn("flex-1", downloadSuccess === "pdf" && "border-emerald-500 text-emerald-600")}
                >
                  {isDownloadingPdf ? (
                    <Loader2 className="w-4 h-4 animate-spin mr-1.5" />
                  ) : downloadSuccess === "pdf" ? (
                    <Check className="w-4 h-4 mr-1.5" />
                  ) : (
                    <Download className="w-4 h-4 mr-1.5" />
                  )}
                  {downloadSuccess === "pdf" ? "Downloaded!" : "Sample PDF"}
                </Button>

                <Button
                  onClick={handleDownloadJpg}
                  disabled={isDownloadingJpg}
                  variant="outline"
                  size="sm"
                  className={cn("flex-1", downloadSuccess === "jpg" && "border-emerald-500 text-emerald-600")}
                >
                  {isDownloadingJpg ? (
                    <Loader2 className="w-4 h-4 animate-spin mr-1.5" />
                  ) : downloadSuccess === "jpg" ? (
                    <Check className="w-4 h-4 mr-1.5" />
                  ) : (
                    <Sparkles className="w-4 h-4 mr-1.5" />
                  )}
                  {downloadSuccess === "jpg" ? "Downloaded!" : "Social Image"}
                </Button>
              </div>

              <div className="relative">
                <div className="absolute inset-0 flex items-center">
                  <div className="w-full border-t border-border" />
                </div>
                <div className="relative flex justify-center text-[10px] uppercase tracking-wider">
                  <span className="bg-card px-2 text-muted-foreground">or</span>
                </div>
              </div>

              <div className="space-y-1.5">
                <Label className="text-xs font-medium text-muted-foreground">Send Test Email</Label>
                <div className="flex gap-2">
                  <Input
                    type="email"
                    value={testEmail}
                    onChange={(e) => setTestEmail(e.target.value)}
                    placeholder="your@email.com"
                    className="flex-1 h-9"
                  />
                  <Button
                    onClick={handleSendTestEmail}
                    disabled={isSending}
                    size="sm"
                    className={cn(sendSuccess && "bg-emerald-600 hover:bg-emerald-700")}
                  >
                    {isSending ? (
                      <Loader2 className="w-4 h-4 animate-spin" />
                    ) : sendSuccess ? (
                      <Check className="w-4 h-4" />
                    ) : (
                      <Send className="w-4 h-4" />
                    )}
                  </Button>
                </div>
                {sendSuccess && (
                  <p className="text-[11px] text-emerald-600 flex items-center gap-1">
                    <Check className="w-3 h-3" />
                    Test email sent! Check your inbox.
                  </p>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Right: Live Preview (Sticky) */}
        <div className="lg:sticky lg:top-20 h-fit space-y-4">
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
            Live Preview
          </div>

          {/* PDF Preview */}
          <div className="bg-card border border-border rounded-xl shadow-[var(--shadow-card)] overflow-hidden">
            <div className="px-3 py-2 border-b border-border bg-muted/30 flex items-center gap-2">
              <FileText className="w-3.5 h-3.5 text-red-500" />
              <span className="text-[11px] font-medium text-muted-foreground">PDF Report</span>
            </div>
            <div className="bg-white">
              {/* Header */}
              <div
                className="p-3"
                style={{ background: `linear-gradient(135deg, ${primaryColor} 0%, ${accentColor} 100%)` }}
              >
                <div className="flex items-center gap-2">
                  {branding.pdf_header_logo_url ? (
                    <img
                      src={branding.pdf_header_logo_url}
                      className="h-6 w-auto max-w-[60px] object-contain brightness-0 invert"
                      alt=""
                    />
                  ) : (
                    <div className="h-6 w-6 rounded bg-white/20 flex items-center justify-center text-white font-bold text-xs">
                      {companyName?.[0] || "B"}
                    </div>
                  )}
                  <div className="text-white">
                    <div className="font-semibold text-xs">Market Update</div>
                    <div className="text-[10px] text-white/70">January 2026</div>
                  </div>
                </div>
              </div>
              {/* Content placeholder */}
              <div className="p-3 space-y-1.5">
                <div className="h-1.5 bg-slate-100 rounded w-full" />
                <div className="h-1.5 bg-slate-100 rounded w-3/4" />
                <div className="h-1.5 bg-slate-100 rounded w-5/6" />
              </div>
              {/* Footer */}
              <div className="p-2 bg-slate-50 border-t flex items-center justify-between">
                <div className="text-[10px] text-slate-600 truncate">{userName}</div>
                {branding.pdf_footer_logo_url ? (
                  <img
                    src={branding.pdf_footer_logo_url}
                    className="h-4 w-auto max-w-[40px] object-contain"
                    alt=""
                  />
                ) : (
                  <div className="text-[9px] font-semibold" style={{ color: primaryColor }}>
                    {companyName || "Your Brand"}
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Email Preview */}
          <div className="bg-card border border-border rounded-xl shadow-[var(--shadow-card)] overflow-hidden">
            <div className="px-3 py-2 border-b border-border bg-muted/30 flex items-center gap-2">
              <Mail className="w-3.5 h-3.5 text-indigo-500" />
              <span className="text-[11px] font-medium text-muted-foreground">Email</span>
            </div>
            <div className="bg-white">
              {/* Header */}
              <div
                className="p-2"
                style={{ background: `linear-gradient(135deg, ${primaryColor} 0%, ${accentColor} 100%)` }}
              >
                <div className="flex items-center gap-2">
                  {branding.email_header_logo_url || branding.pdf_header_logo_url ? (
                    <img
                      src={branding.email_header_logo_url || branding.pdf_header_logo_url || ""}
                      className="h-5 w-auto max-w-[50px] object-contain"
                      alt=""
                    />
                  ) : (
                    <div className="h-5 w-5 rounded bg-white/20 flex items-center justify-center text-white font-bold text-[10px]">
                      {companyName?.[0] || "B"}
                    </div>
                  )}
                  <div className="text-white text-[10px] font-semibold">
                    {companyName || "Your Brand"}
                  </div>
                </div>
              </div>
              {/* Content */}
              <div className="p-2 space-y-1.5">
                <div className="text-[10px] text-slate-600">Your report is ready!</div>
                <div className="h-1 bg-slate-100 rounded w-full" />
                <div className="h-1 bg-slate-100 rounded w-2/3" />
              </div>
              {/* Footer */}
              <div className="p-2 bg-white border-t flex items-center justify-between">
                <div className="text-[9px] text-slate-600 truncate">{userName}</div>
                {branding.email_footer_logo_url || branding.pdf_footer_logo_url ? (
                  <img
                    src={branding.email_footer_logo_url || branding.pdf_footer_logo_url || ""}
                    className="h-4 w-auto max-w-[40px] object-contain"
                    alt=""
                  />
                ) : (
                  <div className="text-[9px] font-semibold" style={{ color: primaryColor }}>
                    {companyName || "Your Brand"}
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Tip */}
          <div className="p-3 rounded-lg bg-amber-50 border border-amber-200">
            <p className="text-[11px] text-amber-800 flex items-start gap-2">
              <Lightbulb className="w-4 h-4 flex-shrink-0 mt-0.5" />
              Header logos should be light/white for the gradient background.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
