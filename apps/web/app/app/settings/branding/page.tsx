"use client"

import { useEffect, useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible"
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
  TestTube2,
  ChevronDown,
  ChevronUp,
  Save,
  Loader2,
  Download,
  Send,
  Check,
  AlertCircle,
  Lightbulb,
  Sparkles,
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

type AccordionState = {
  colors: boolean
  pdfLogos: boolean
  emailLogos: boolean
  testing: boolean
}

export default function BrandingPage() {
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const { toast } = useToast()

  const [branding, setBranding] = useState<BrandingData>({
    primary_color: "#8B5CF6",
    accent_color: "#F59E0B",
    pdf_header_logo_url: null,
    pdf_footer_logo_url: null,
    email_header_logo_url: null,
    email_footer_logo_url: null,
  })

  const [accordion, setAccordion] = useState<AccordionState>({
    colors: true,
    pdfLogos: false,
    emailLogos: false,
    testing: false,
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
          primary_color: data.primary_color || "#8B5CF6",
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
          <Loader2 className="w-8 h-8 animate-spin text-violet-600 mx-auto mb-4" />
          <p className="text-muted-foreground">Loading branding settings...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Section Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold">Branding</h2>
          <p className="text-sm text-muted-foreground mt-1">
            Customize how your reports and emails look.
          </p>
        </div>
        <Button onClick={save} disabled={saving}>
          {saving ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin mr-2" />
              Saving...
            </>
          ) : (
            <>
              <Save className="w-4 h-4 mr-2" />
              Save Changes
            </>
          )}
        </Button>
      </div>

      {/* Two-column layout: Config + Preview */}
      <div className="grid grid-cols-[1fr_380px] gap-8">
        {/* Left: Configuration Accordions */}
        <div className="space-y-3">
          {/* Brand Colors Accordion */}
          <Collapsible
            open={accordion.colors}
            onOpenChange={(open) => setAccordion({ ...accordion, colors: open })}
          >
            <div className="bg-card border rounded-xl overflow-hidden">
              <CollapsibleTrigger className="w-full p-4 flex items-center justify-between hover:bg-muted/50 transition-colors">
                <div className="flex items-center gap-3">
                  <div className="p-1.5 rounded-lg bg-violet-100 dark:bg-violet-900/30">
                    <Palette className="w-4 h-4 text-violet-600" />
                  </div>
                  <div className="text-left">
                    <p className="font-medium">Brand Colors</p>
                    {!accordion.colors && (
                      <div className="flex items-center gap-2 mt-1">
                        <div
                          className="w-4 h-4 rounded border"
                          style={{ backgroundColor: primaryColor }}
                        />
                        <span className="text-xs text-muted-foreground">{primaryColor}</span>
                        <span className="text-muted-foreground">·</span>
                        <div
                          className="w-4 h-4 rounded border"
                          style={{ backgroundColor: accentColor }}
                        />
                        <span className="text-xs text-muted-foreground">{accentColor}</span>
                      </div>
                    )}
                  </div>
                </div>
                {accordion.colors ? (
                  <ChevronUp className="w-5 h-5 text-muted-foreground" />
                ) : (
                  <ChevronDown className="w-5 h-5 text-muted-foreground" />
                )}
              </CollapsibleTrigger>
              <CollapsibleContent>
                <div className="p-4 pt-0 space-y-5 border-t">
                  <p className="text-sm text-muted-foreground">
                    These colors are used throughout your reports and emails.
                  </p>

                  <div>
                    <Label>Primary Color</Label>
                    <p className="text-xs text-muted-foreground mb-2">
                      Used for headers, ribbons, and backgrounds
                    </p>
                    <div className="flex gap-2">
                      <div
                        className="w-14 h-10 rounded-lg border-2 cursor-pointer relative shadow-sm flex-shrink-0"
                        style={{ backgroundColor: primaryColor }}
                      >
                        <input
                          type="color"
                          value={primaryColor}
                          onChange={(e) =>
                            setBranding({ ...branding, primary_color: e.target.value })
                          }
                          className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                        />
                      </div>
                      <Input
                        value={primaryColor}
                        onChange={(e) =>
                          setBranding({ ...branding, primary_color: e.target.value })
                        }
                        className="font-mono text-sm uppercase"
                        maxLength={7}
                      />
                    </div>
                  </div>

                  {/* Gradient preview */}
                  <div
                    className="h-3 rounded-full"
                    style={{
                      background: `linear-gradient(90deg, ${primaryColor} 0%, ${accentColor} 100%)`,
                    }}
                  />

                  <div>
                    <Label>Accent Color</Label>
                    <p className="text-xs text-muted-foreground mb-2">
                      Used for buttons, highlights, and call-to-actions
                    </p>
                    <div className="flex gap-2">
                      <div
                        className="w-14 h-10 rounded-lg border-2 cursor-pointer relative shadow-sm flex-shrink-0"
                        style={{ backgroundColor: accentColor }}
                      >
                        <input
                          type="color"
                          value={accentColor}
                          onChange={(e) =>
                            setBranding({ ...branding, accent_color: e.target.value })
                          }
                          className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                        />
                      </div>
                      <Input
                        value={accentColor}
                        onChange={(e) =>
                          setBranding({ ...branding, accent_color: e.target.value })
                        }
                        className="font-mono text-sm uppercase"
                        maxLength={7}
                      />
                    </div>
                  </div>
                </div>
              </CollapsibleContent>
            </div>
          </Collapsible>

          {/* PDF Logos Accordion */}
          <Collapsible
            open={accordion.pdfLogos}
            onOpenChange={(open) => setAccordion({ ...accordion, pdfLogos: open })}
          >
            <div className="bg-card border rounded-xl overflow-hidden">
              <CollapsibleTrigger className="w-full p-4 flex items-center justify-between hover:bg-muted/50 transition-colors">
                <div className="flex items-center gap-3">
                  <div className="p-1.5 rounded-lg bg-red-100 dark:bg-red-900/30">
                    <FileText className="w-4 h-4 text-red-600" />
                  </div>
                  <div className="text-left">
                    <p className="font-medium">PDF Logos</p>
                    {!accordion.pdfLogos && (
                      <p className="text-xs text-muted-foreground mt-1">
                        Header {branding.pdf_header_logo_url ? "✓" : "○"} · Footer{" "}
                        {branding.pdf_footer_logo_url ? "✓" : "○"}
                      </p>
                    )}
                  </div>
                </div>
                {accordion.pdfLogos ? (
                  <ChevronUp className="w-5 h-5 text-muted-foreground" />
                ) : (
                  <ChevronDown className="w-5 h-5 text-muted-foreground" />
                )}
              </CollapsibleTrigger>
              <CollapsibleContent>
                <div className="p-4 pt-0 space-y-5 border-t">
                  <p className="text-sm text-muted-foreground">
                    Logos used in downloadable PDF reports.
                  </p>

                  <div>
                    <Label>Header Logo</Label>
                    <p className="text-xs text-muted-foreground mb-2">
                      Appears on the gradient header. Use a light/white version.
                    </p>
                    <ImageUpload
                      label=""
                      value={branding.pdf_header_logo_url}
                      onChange={(url) =>
                        setBranding({ ...branding, pdf_header_logo_url: url })
                      }
                      assetType="logo"
                      aspectRatio="wide"
                      helpText="PNG or SVG, transparent background recommended"
                    />
                  </div>

                  <div>
                    <Label>Footer Logo</Label>
                    <p className="text-xs text-muted-foreground mb-2">
                      Appears in the footer. Use your standard/dark version.
                    </p>
                    <ImageUpload
                      label=""
                      value={branding.pdf_footer_logo_url}
                      onChange={(url) =>
                        setBranding({ ...branding, pdf_footer_logo_url: url })
                      }
                      assetType="logo"
                      aspectRatio="wide"
                      helpText="PNG or SVG, transparent background recommended"
                    />
                  </div>
                </div>
              </CollapsibleContent>
            </div>
          </Collapsible>

          {/* Email Logos Accordion */}
          <Collapsible
            open={accordion.emailLogos}
            onOpenChange={(open) => setAccordion({ ...accordion, emailLogos: open })}
          >
            <div className="bg-card border rounded-xl overflow-hidden">
              <CollapsibleTrigger className="w-full p-4 flex items-center justify-between hover:bg-muted/50 transition-colors">
                <div className="flex items-center gap-3">
                  <div className="p-1.5 rounded-lg bg-purple-100 dark:bg-purple-900/30">
                    <Mail className="w-4 h-4 text-purple-600" />
                  </div>
                  <div className="text-left">
                    <p className="font-medium">Email Logos</p>
                    {!accordion.emailLogos && (
                      <p className="text-xs text-muted-foreground mt-1">
                        Header {branding.email_header_logo_url ? "✓" : "○"} · Footer{" "}
                        {branding.email_footer_logo_url ? "✓" : "○"}
                      </p>
                    )}
                  </div>
                </div>
                {accordion.emailLogos ? (
                  <ChevronUp className="w-5 h-5 text-muted-foreground" />
                ) : (
                  <ChevronDown className="w-5 h-5 text-muted-foreground" />
                )}
              </CollapsibleTrigger>
              <CollapsibleContent>
                <div className="p-4 pt-0 space-y-5 border-t">
                  <p className="text-sm text-muted-foreground">Logos used in email reports.</p>

                  <div>
                    <Label>Header Logo</Label>
                    <p className="text-xs text-muted-foreground mb-2">
                      Appears on the email header.
                    </p>
                    <ImageUpload
                      label=""
                      value={branding.email_header_logo_url}
                      onChange={(url) =>
                        setBranding({ ...branding, email_header_logo_url: url })
                      }
                      assetType="logo"
                      aspectRatio="wide"
                      helpText=""
                    />
                  </div>

                  <div>
                    <Label>Footer Logo</Label>
                    <p className="text-xs text-muted-foreground mb-2">
                      Appears in the email footer.
                    </p>
                    <ImageUpload
                      label=""
                      value={branding.email_footer_logo_url}
                      onChange={(url) =>
                        setBranding({ ...branding, email_footer_logo_url: url })
                      }
                      assetType="logo"
                      aspectRatio="wide"
                      helpText=""
                    />
                  </div>

                  <div className="p-3 rounded-lg bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800">
                    <p className="text-xs text-amber-800 dark:text-amber-200 flex items-start gap-2">
                      <Lightbulb className="w-4 h-4 flex-shrink-0 mt-0.5" />
                      Email logos may need to be different from PDF logos due to email client
                      rendering differences.
                    </p>
                  </div>
                </div>
              </CollapsibleContent>
            </div>
          </Collapsible>

          {/* Test Your Branding Accordion */}
          <Collapsible
            open={accordion.testing}
            onOpenChange={(open) => setAccordion({ ...accordion, testing: open })}
          >
            <div className="bg-card border rounded-xl overflow-hidden">
              <CollapsibleTrigger className="w-full p-4 flex items-center justify-between hover:bg-muted/50 transition-colors">
                <div className="flex items-center gap-3">
                  <div className="p-1.5 rounded-lg bg-green-100 dark:bg-green-900/30">
                    <TestTube2 className="w-4 h-4 text-green-600" />
                  </div>
                  <div className="text-left">
                    <p className="font-medium">Test Your Branding</p>
                    {!accordion.testing && (
                      <p className="text-xs text-muted-foreground mt-1">
                        Download samples or send test email
                      </p>
                    )}
                  </div>
                </div>
                {accordion.testing ? (
                  <ChevronUp className="w-5 h-5 text-muted-foreground" />
                ) : (
                  <ChevronDown className="w-5 h-5 text-muted-foreground" />
                )}
              </CollapsibleTrigger>
              <CollapsibleContent>
                <div className="p-4 pt-0 space-y-5 border-t">
                  <p className="text-sm text-muted-foreground">
                    Preview how your branding looks on actual reports.
                  </p>

                  <div>
                    <Label>Report Type</Label>
                    <Select
                      value={reportType}
                      onValueChange={(v) => setReportType(v as ReportType)}
                    >
                      <SelectTrigger className="mt-1.5">
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

                  <div className="space-y-2">
                    <Button
                      onClick={handleDownloadPdf}
                      disabled={isDownloadingPdf}
                      variant="outline"
                      className={cn(
                        "w-full justify-start h-11",
                        downloadSuccess === "pdf" && "border-green-500 text-green-600"
                      )}
                    >
                      {isDownloadingPdf ? (
                        <Loader2 className="w-4 h-4 animate-spin mr-2" />
                      ) : downloadSuccess === "pdf" ? (
                        <Check className="w-4 h-4 mr-2" />
                      ) : (
                        <FileText className="w-4 h-4 mr-2" />
                      )}
                      {isDownloadingPdf
                        ? "Generating..."
                        : downloadSuccess === "pdf"
                        ? "Downloaded!"
                        : "Download Sample PDF"}
                    </Button>

                    <Button
                      onClick={handleDownloadJpg}
                      disabled={isDownloadingJpg}
                      variant="outline"
                      className={cn(
                        "w-full justify-start h-11",
                        downloadSuccess === "jpg" && "border-green-500 text-green-600"
                      )}
                    >
                      {isDownloadingJpg ? (
                        <Loader2 className="w-4 h-4 animate-spin mr-2" />
                      ) : downloadSuccess === "jpg" ? (
                        <Check className="w-4 h-4 mr-2" />
                      ) : (
                        <Sparkles className="w-4 h-4 mr-2" />
                      )}
                      {isDownloadingJpg
                        ? "Generating..."
                        : downloadSuccess === "jpg"
                        ? "Downloaded!"
                        : "Download Social Image (Story)"}
                    </Button>
                  </div>

                  <div className="relative">
                    <div className="absolute inset-0 flex items-center">
                      <div className="w-full border-t" />
                    </div>
                    <div className="relative flex justify-center text-xs uppercase">
                      <span className="bg-card px-2 text-muted-foreground">or</span>
                    </div>
                  </div>

                  <div>
                    <Label>Send Test Email</Label>
                    <div className="flex gap-2 mt-1.5">
                      <Input
                        type="email"
                        value={testEmail}
                        onChange={(e) => setTestEmail(e.target.value)}
                        placeholder="your@email.com"
                        className="flex-1"
                      />
                      <Button
                        onClick={handleSendTestEmail}
                        disabled={isSending}
                        className={cn(sendSuccess && "bg-green-600 hover:bg-green-700")}
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
                      <p className="text-xs text-green-600 mt-1.5 flex items-center gap-1">
                        <Check className="w-3 h-3" />
                        Test email sent! Check your inbox.
                      </p>
                    )}
                  </div>
                </div>
              </CollapsibleContent>
            </div>
          </Collapsible>
        </div>

        {/* Right: Live Preview (Sticky) */}
        <div className="sticky top-24 h-fit space-y-4">
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
            Preview
            <span className="text-xs ml-auto">Updates live</span>
          </div>

          {/* PDF Preview */}
          <div>
            <div className="flex items-center gap-2 mb-2 text-xs text-muted-foreground">
              <FileText className="w-3.5 h-3.5 text-red-500" />
              PDF Report
            </div>
            <div className="rounded-xl border shadow-lg overflow-hidden bg-white dark:bg-zinc-900">
              {/* Header */}
              <div
                className="p-4"
                style={{
                  background: `linear-gradient(135deg, ${primaryColor} 0%, ${accentColor} 100%)`,
                }}
              >
                <div className="flex items-center gap-3">
                  {branding.pdf_header_logo_url ? (
                    <img
                      src={branding.pdf_header_logo_url}
                      className="h-8 w-auto max-w-[80px] object-contain brightness-0 invert"
                      alt=""
                    />
                  ) : (
                    <div className="h-8 w-8 rounded bg-white/20 flex items-center justify-center text-white font-bold">
                      {companyName?.[0] || "B"}
                    </div>
                  )}
                  <div className="text-white">
                    <div className="font-semibold text-sm">Market Update</div>
                    <div className="text-xs text-white/70">January 2026</div>
                  </div>
                </div>
              </div>
              {/* Content placeholder */}
              <div className="p-4 space-y-2">
                <div className="h-2 bg-slate-100 rounded w-full" />
                <div className="h-2 bg-slate-100 rounded w-3/4" />
                <div className="h-2 bg-slate-100 rounded w-5/6" />
              </div>
              {/* Footer */}
              <div className="p-3 bg-slate-50 border-t flex items-center justify-between">
                <div className="text-xs text-slate-600 truncate">{userName}</div>
                {branding.pdf_footer_logo_url ? (
                  <img
                    src={branding.pdf_footer_logo_url}
                    className="h-6 w-auto max-w-[60px] object-contain"
                    alt=""
                  />
                ) : (
                  <div className="text-xs font-semibold" style={{ color: primaryColor }}>
                    {companyName || "Your Brand"}
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Email Preview */}
          <div>
            <div className="flex items-center gap-2 mb-2 text-xs text-muted-foreground">
              <Mail className="w-3.5 h-3.5 text-purple-500" />
              Email
            </div>
            <div className="rounded-xl border shadow-lg overflow-hidden bg-white dark:bg-zinc-900">
              {/* Header */}
              <div
                className="p-3"
                style={{
                  background: `linear-gradient(135deg, ${primaryColor} 0%, ${accentColor} 100%)`,
                }}
              >
                <div className="flex items-center gap-2">
                  {branding.email_header_logo_url || branding.pdf_header_logo_url ? (
                    <img
                      src={branding.email_header_logo_url || branding.pdf_header_logo_url || ""}
                      className="h-6 w-auto max-w-[60px] object-contain"
                      alt=""
                    />
                  ) : (
                    <div className="h-6 w-6 rounded bg-white/20 flex items-center justify-center text-white font-bold text-xs">
                      {companyName?.[0] || "B"}
                    </div>
                  )}
                  <div className="text-white text-xs font-semibold">
                    {companyName || "Your Brand"}
                  </div>
                </div>
              </div>
              {/* Content */}
              <div className="p-3 space-y-2">
                <div className="text-xs text-slate-600">Your report is ready!</div>
                <div className="h-1.5 bg-slate-100 rounded w-full" />
                <div className="h-1.5 bg-slate-100 rounded w-2/3" />
              </div>
              {/* Footer */}
              <div className="p-3 bg-white border-t flex items-center justify-between">
                <div className="text-[10px] text-slate-600 truncate">{userName}</div>
                {branding.email_footer_logo_url || branding.pdf_footer_logo_url ? (
                  <img
                    src={branding.email_footer_logo_url || branding.pdf_footer_logo_url || ""}
                    className="h-5 w-auto max-w-[50px] object-contain"
                    alt=""
                  />
                ) : (
                  <div className="text-[10px] font-semibold" style={{ color: primaryColor }}>
                    {companyName || "Your Brand"}
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Tip */}
          <div className="p-3 rounded-lg bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800">
            <p className="text-xs text-amber-800 dark:text-amber-200 flex items-start gap-2">
              <Lightbulb className="w-4 h-4 flex-shrink-0 mt-0.5" />
              Header logos should be light/white for the gradient background.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

