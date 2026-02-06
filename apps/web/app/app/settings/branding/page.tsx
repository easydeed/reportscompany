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
  Image,
  Droplets,
  Upload,
} from "lucide-react"
import { useToast } from "@/components/ui/use-toast"
import { ImageUpload } from "@/components/ui/image-upload"
import { cn } from "@/lib/utils"
import { REPORT_TYPE_OPTIONS, ReportType } from "@/lib/sample-report-data"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"

type BrandingData = {
  primary_color: string
  accent_color: string
  pdf_header_logo_url: string | null
  pdf_footer_logo_url: string | null
  email_header_logo_url: string | null
  email_footer_logo_url: string | null
}

// Color presets for quick selection
const COLOR_PRESETS = [
  { name: "Indigo", primary: "#4F46E5", accent: "#F59E0B" },
  { name: "Ocean", primary: "#0EA5E9", accent: "#10B981" },
  { name: "Crimson", primary: "#DC2626", accent: "#1D4ED8" },
  { name: "Forest", primary: "#059669", accent: "#D97706" },
  { name: "Midnight", primary: "#1E293B", accent: "#818CF8" },
  { name: "Royal", primary: "#7C3AED", accent: "#EC4899" },
]

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
    <div className="max-w-6xl mx-auto">
      {/* Page Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-foreground">Branding</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Customize how your reports and emails look
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

      {/* Main Content - Tabs Layout */}
      <Tabs defaultValue="colors" className="space-y-6">
        <TabsList className="bg-muted/50 p-1">
          <TabsTrigger value="colors" className="gap-2">
            <Droplets className="w-4 h-4" />
            Colors
          </TabsTrigger>
          <TabsTrigger value="logos" className="gap-2">
            <Image className="w-4 h-4" />
            Logos
          </TabsTrigger>
          <TabsTrigger value="preview" className="gap-2">
            <Eye className="w-4 h-4" />
            Preview & Test
          </TabsTrigger>
        </TabsList>

        {/* Colors Tab */}
        <TabsContent value="colors" className="space-y-6">
          <div className="grid lg:grid-cols-2 gap-6">
            {/* Color Picker Card */}
            <div className="bg-card border border-border rounded-2xl shadow-[var(--shadow-card)] overflow-hidden">
              <div className="px-6 py-4 border-b border-border bg-muted/30 flex items-center gap-3">
                <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-indigo-500 to-amber-500 flex items-center justify-center">
                  <Palette className="w-4 h-4 text-white" />
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-foreground">Brand Colors</h3>
                  <p className="text-xs text-muted-foreground">Choose your primary and accent colors</p>
                </div>
              </div>
              
              <div className="p-6 space-y-6">
                {/* Primary Color */}
                <div className="space-y-3">
                  <Label className="text-sm font-medium text-foreground">Primary Color</Label>
                  <p className="text-xs text-muted-foreground -mt-2">Used for headers, ribbons, and backgrounds</p>
                  <div className="flex gap-3">
                    <div
                      className="w-16 h-12 rounded-xl border-2 border-border cursor-pointer relative shadow-inner flex-shrink-0 transition-all hover:scale-105 hover:shadow-md"
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
                      className="font-mono text-sm uppercase h-12 flex-1"
                      maxLength={7}
                    />
                  </div>
                </div>

                {/* Accent Color */}
                <div className="space-y-3">
                  <Label className="text-sm font-medium text-foreground">Accent Color</Label>
                  <p className="text-xs text-muted-foreground -mt-2">Used for buttons, highlights, and CTAs</p>
                  <div className="flex gap-3">
                    <div
                      className="w-16 h-12 rounded-xl border-2 border-border cursor-pointer relative shadow-inner flex-shrink-0 transition-all hover:scale-105 hover:shadow-md"
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
                      className="font-mono text-sm uppercase h-12 flex-1"
                      maxLength={7}
                    />
                  </div>
                </div>

                {/* Gradient Preview */}
                <div className="space-y-2">
                  <Label className="text-xs text-muted-foreground">Gradient Preview</Label>
                  <div
                    className="h-16 rounded-xl shadow-inner"
                    style={{ background: `linear-gradient(135deg, ${primaryColor} 0%, ${accentColor} 100%)` }}
                  />
                </div>
              </div>
            </div>

            {/* Color Presets */}
            <div className="bg-card border border-border rounded-2xl shadow-[var(--shadow-card)] overflow-hidden">
              <div className="px-6 py-4 border-b border-border bg-muted/30 flex items-center gap-3">
                <div className="w-9 h-9 rounded-lg bg-indigo-50 flex items-center justify-center">
                  <Sparkles className="w-4 h-4 text-indigo-600" />
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-foreground">Quick Presets</h3>
                  <p className="text-xs text-muted-foreground">Start with a professional color scheme</p>
                </div>
              </div>

              <div className="p-6">
                <div className="grid grid-cols-2 gap-3">
                  {COLOR_PRESETS.map((preset) => (
                    <button
                      key={preset.name}
                      onClick={() => setBranding({ ...branding, primary_color: preset.primary, accent_color: preset.accent })}
                      className={cn(
                        "group relative p-4 rounded-xl border-2 transition-all hover:scale-[1.02]",
                        primaryColor === preset.primary && accentColor === preset.accent
                          ? "border-indigo-500 bg-indigo-50/50 shadow-md"
                          : "border-border hover:border-indigo-200 hover:bg-muted/30"
                      )}
                    >
                      <div className="flex gap-2 mb-2">
                        <div
                          className="w-8 h-8 rounded-lg shadow-sm"
                          style={{ backgroundColor: preset.primary }}
                        />
                        <div
                          className="w-8 h-8 rounded-lg shadow-sm"
                          style={{ backgroundColor: preset.accent }}
                        />
                      </div>
                      <p className="text-xs font-medium text-foreground text-left">{preset.name}</p>
                      {primaryColor === preset.primary && accentColor === preset.accent && (
                        <div className="absolute top-2 right-2">
                          <Check className="w-4 h-4 text-indigo-600" />
                        </div>
                      )}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </TabsContent>

        {/* Logos Tab */}
        <TabsContent value="logos" className="space-y-6">
          <div className="grid lg:grid-cols-2 gap-6">
            {/* PDF Logos */}
            <div className="bg-card border border-border rounded-2xl shadow-[var(--shadow-card)] overflow-hidden">
              <div className="px-6 py-4 border-b border-border bg-muted/30 flex items-center gap-3">
                <div className="w-9 h-9 rounded-lg bg-red-50 flex items-center justify-center">
                  <FileText className="w-4 h-4 text-red-600" />
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-foreground">PDF Report Logos</h3>
                  <p className="text-xs text-muted-foreground">Logos for downloadable PDF reports</p>
                </div>
              </div>

              <div className="p-6 space-y-6">
                {/* Header Logo */}
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <div>
                      <Label className="text-sm font-medium text-foreground">Header Logo</Label>
                      <p className="text-xs text-muted-foreground">Light/white version for gradient background</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    <div 
                      className="w-24 h-16 rounded-lg flex items-center justify-center p-2"
                      style={{ background: `linear-gradient(135deg, ${primaryColor} 0%, ${accentColor} 100%)` }}
                    >
                      {branding.pdf_header_logo_url ? (
                        <img
                          src={branding.pdf_header_logo_url}
                          className="max-h-full max-w-full object-contain brightness-0 invert"
                          alt="Header logo"
                        />
                      ) : (
                        <Upload className="w-6 h-6 text-white/50" />
                      )}
                    </div>
                    <div className="flex-1">
                      <ImageUpload
                        label=""
                        value={branding.pdf_header_logo_url}
                        onChange={(url) => setBranding({ ...branding, pdf_header_logo_url: url })}
                        assetType="logo"
                        aspectRatio="wide"
                        helpText="PNG/SVG with transparent bg"
                      />
                    </div>
                  </div>
                </div>

                {/* Footer Logo */}
                <div className="space-y-3">
                  <div>
                    <Label className="text-sm font-medium text-foreground">Footer Logo</Label>
                    <p className="text-xs text-muted-foreground">Standard/dark version for light backgrounds</p>
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="w-24 h-16 rounded-lg bg-slate-50 border border-border flex items-center justify-center p-2">
                      {branding.pdf_footer_logo_url ? (
                        <img
                          src={branding.pdf_footer_logo_url}
                          className="max-h-full max-w-full object-contain"
                          alt="Footer logo"
                        />
                      ) : (
                        <Upload className="w-6 h-6 text-muted-foreground/30" />
                      )}
                    </div>
                    <div className="flex-1">
                      <ImageUpload
                        label=""
                        value={branding.pdf_footer_logo_url}
                        onChange={(url) => setBranding({ ...branding, pdf_footer_logo_url: url })}
                        assetType="logo"
                        aspectRatio="wide"
                        helpText="PNG/SVG with transparent bg"
                      />
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Email Logos */}
            <div className="bg-card border border-border rounded-2xl shadow-[var(--shadow-card)] overflow-hidden">
              <div className="px-6 py-4 border-b border-border bg-muted/30 flex items-center gap-3">
                <div className="w-9 h-9 rounded-lg bg-indigo-50 flex items-center justify-center">
                  <Mail className="w-4 h-4 text-indigo-600" />
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-foreground">Email Logos</h3>
                  <p className="text-xs text-muted-foreground">Logos for email reports</p>
                </div>
              </div>

              <div className="p-6 space-y-6">
                {/* Email Header Logo */}
                <div className="space-y-3">
                  <div>
                    <Label className="text-sm font-medium text-foreground">Header Logo</Label>
                    <p className="text-xs text-muted-foreground">Appears at top of email</p>
                  </div>
                  <div className="flex items-center gap-4">
                    <div 
                      className="w-24 h-16 rounded-lg flex items-center justify-center p-2"
                      style={{ background: `linear-gradient(135deg, ${primaryColor} 0%, ${accentColor} 100%)` }}
                    >
                      {branding.email_header_logo_url || branding.pdf_header_logo_url ? (
                        <img
                          src={branding.email_header_logo_url || branding.pdf_header_logo_url || ""}
                          className="max-h-full max-w-full object-contain"
                          alt="Email header logo"
                        />
                      ) : (
                        <Upload className="w-6 h-6 text-white/50" />
                      )}
                    </div>
                    <div className="flex-1">
                      <ImageUpload
                        label=""
                        value={branding.email_header_logo_url}
                        onChange={(url) => setBranding({ ...branding, email_header_logo_url: url })}
                        assetType="logo"
                        aspectRatio="wide"
                        helpText="Falls back to PDF header logo"
                      />
                    </div>
                  </div>
                </div>

                {/* Email Footer Logo */}
                <div className="space-y-3">
                  <div>
                    <Label className="text-sm font-medium text-foreground">Footer Logo</Label>
                    <p className="text-xs text-muted-foreground">Appears at bottom of email</p>
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="w-24 h-16 rounded-lg bg-white border border-border flex items-center justify-center p-2">
                      {branding.email_footer_logo_url || branding.pdf_footer_logo_url ? (
                        <img
                          src={branding.email_footer_logo_url || branding.pdf_footer_logo_url || ""}
                          className="max-h-full max-w-full object-contain"
                          alt="Email footer logo"
                        />
                      ) : (
                        <Upload className="w-6 h-6 text-muted-foreground/30" />
                      )}
                    </div>
                    <div className="flex-1">
                      <ImageUpload
                        label=""
                        value={branding.email_footer_logo_url}
                        onChange={(url) => setBranding({ ...branding, email_footer_logo_url: url })}
                        assetType="logo"
                        aspectRatio="wide"
                        helpText="Falls back to PDF footer logo"
                      />
                    </div>
                  </div>
                </div>

                {/* Tip */}
                <div className="p-3 rounded-lg bg-amber-50 border border-amber-200">
                  <p className="text-xs text-amber-800 flex items-start gap-2">
                    <Lightbulb className="w-4 h-4 flex-shrink-0 mt-0.5" />
                    Email logos may render differently across email clients. Test before sending.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </TabsContent>

        {/* Preview & Test Tab */}
        <TabsContent value="preview" className="space-y-6">
          <div className="grid lg:grid-cols-[1fr_380px] gap-6">
            {/* Live Previews */}
            <div className="space-y-6">
              {/* PDF Preview */}
              <div className="bg-card border border-border rounded-2xl shadow-[var(--shadow-card)] overflow-hidden">
                <div className="px-6 py-4 border-b border-border bg-muted/30 flex items-center gap-3">
                  <div className="w-9 h-9 rounded-lg bg-red-50 flex items-center justify-center">
                    <FileText className="w-4 h-4 text-red-600" />
                  </div>
                  <div>
                    <h3 className="text-sm font-semibold text-foreground">PDF Report Preview</h3>
                    <p className="text-xs text-muted-foreground">How your PDF reports will look</p>
                  </div>
                </div>
                
                <div className="p-6">
                  <div className="bg-white rounded-xl shadow-lg overflow-hidden border border-slate-200">
                    {/* Header */}
                    <div
                      className="p-6"
                      style={{ background: `linear-gradient(135deg, ${primaryColor} 0%, ${accentColor} 100%)` }}
                    >
                      <div className="flex items-center gap-4">
                        {branding.pdf_header_logo_url ? (
                          <img
                            src={branding.pdf_header_logo_url}
                            className="h-10 w-auto max-w-[100px] object-contain brightness-0 invert"
                            alt=""
                          />
                        ) : (
                          <div className="h-10 w-10 rounded-lg bg-white/20 flex items-center justify-center text-white font-bold text-lg">
                            {companyName?.[0] || "T"}
                          </div>
                        )}
                        <div className="text-white">
                          <div className="font-semibold text-base">Market Update</div>
                          <div className="text-sm text-white/70">January 2026 • Los Angeles, CA</div>
                        </div>
                      </div>
                    </div>
                    
                    {/* Content placeholder */}
                    <div className="p-6 space-y-3">
                      <div className="h-3 bg-slate-100 rounded w-full" />
                      <div className="h-3 bg-slate-100 rounded w-3/4" />
                      <div className="h-3 bg-slate-100 rounded w-5/6" />
                      <div className="grid grid-cols-3 gap-3 mt-4">
                        <div className="h-16 bg-slate-50 rounded-lg border border-slate-100" />
                        <div className="h-16 bg-slate-50 rounded-lg border border-slate-100" />
                        <div className="h-16 bg-slate-50 rounded-lg border border-slate-100" />
                      </div>
                    </div>
                    
                    {/* Footer */}
                    <div className="px-6 py-4 bg-slate-50 border-t border-slate-100 flex items-center justify-between">
                      <div className="text-sm text-slate-600">{userName || "Agent Name"}</div>
                      {branding.pdf_footer_logo_url ? (
                        <img
                          src={branding.pdf_footer_logo_url}
                          className="h-6 w-auto max-w-[80px] object-contain"
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
              </div>

              {/* Email Preview */}
              <div className="bg-card border border-border rounded-2xl shadow-[var(--shadow-card)] overflow-hidden">
                <div className="px-6 py-4 border-b border-border bg-muted/30 flex items-center gap-3">
                  <div className="w-9 h-9 rounded-lg bg-indigo-50 flex items-center justify-center">
                    <Mail className="w-4 h-4 text-indigo-600" />
                  </div>
                  <div>
                    <h3 className="text-sm font-semibold text-foreground">Email Preview</h3>
                    <p className="text-xs text-muted-foreground">How your email reports will look</p>
                  </div>
                </div>
                
                <div className="p-6">
                  <div className="bg-slate-100 rounded-xl p-4">
                    <div className="bg-white rounded-lg shadow-sm overflow-hidden max-w-md mx-auto">
                      {/* Email Header */}
                      <div
                        className="p-4"
                        style={{ background: `linear-gradient(135deg, ${primaryColor} 0%, ${accentColor} 100%)` }}
                      >
                        <div className="flex items-center gap-3">
                          {branding.email_header_logo_url || branding.pdf_header_logo_url ? (
                            <img
                              src={branding.email_header_logo_url || branding.pdf_header_logo_url || ""}
                              className="h-8 w-auto max-w-[80px] object-contain"
                              alt=""
                            />
                          ) : (
                            <div className="h-8 w-8 rounded bg-white/20 flex items-center justify-center text-white font-bold text-sm">
                              {companyName?.[0] || "T"}
                            </div>
                          )}
                          <div className="text-white text-sm font-semibold">
                            {companyName || "Your Brand"}
                          </div>
                        </div>
                      </div>
                      
                      {/* Email Content */}
                      <div className="p-4 space-y-3">
                        <div className="text-sm text-slate-700">Your market report is ready!</div>
                        <div className="h-2 bg-slate-100 rounded w-full" />
                        <div className="h-2 bg-slate-100 rounded w-2/3" />
                        <Button 
                          size="sm" 
                          className="mt-2"
                          style={{ backgroundColor: accentColor }}
                        >
                          View Report
                        </Button>
                      </div>
                      
                      {/* Email Footer */}
                      <div className="px-4 py-3 bg-white border-t border-slate-100 flex items-center justify-between">
                        <div className="text-xs text-slate-500">{userName || "Agent Name"}</div>
                        {branding.email_footer_logo_url || branding.pdf_footer_logo_url ? (
                          <img
                            src={branding.email_footer_logo_url || branding.pdf_footer_logo_url || ""}
                            className="h-5 w-auto max-w-[60px] object-contain"
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
                </div>
              </div>
            </div>

            {/* Test Panel */}
            <div className="space-y-6">
              <div className="bg-card border border-border rounded-2xl shadow-[var(--shadow-card)] overflow-hidden sticky top-20">
                <div className="px-6 py-4 border-b border-border bg-muted/30 flex items-center gap-3">
                  <div className="w-9 h-9 rounded-lg bg-emerald-50 flex items-center justify-center">
                    <Eye className="w-4 h-4 text-emerald-600" />
                  </div>
                  <div>
                    <h3 className="text-sm font-semibold text-foreground">Test Your Branding</h3>
                    <p className="text-xs text-muted-foreground">Download samples or send test</p>
                  </div>
                </div>

                <div className="p-6 space-y-5">
                  {/* Report Type */}
                  <div className="space-y-2">
                    <Label className="text-xs font-medium text-muted-foreground">Report Type</Label>
                    <Select value={reportType} onValueChange={(v) => setReportType(v as ReportType)}>
                      <SelectTrigger className="h-10">
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

                  {/* Download Buttons */}
                  <div className="space-y-2">
                    <Label className="text-xs font-medium text-muted-foreground">Download Sample</Label>
                    <div className="grid grid-cols-2 gap-2">
                      <Button
                        onClick={handleDownloadPdf}
                        disabled={isDownloadingPdf}
                        variant="outline"
                        className={cn(
                          "h-20 flex-col gap-2",
                          downloadSuccess === "pdf" && "border-emerald-500 text-emerald-600 bg-emerald-50"
                        )}
                      >
                        {isDownloadingPdf ? (
                          <Loader2 className="w-5 h-5 animate-spin" />
                        ) : downloadSuccess === "pdf" ? (
                          <Check className="w-5 h-5" />
                        ) : (
                          <Download className="w-5 h-5" />
                        )}
                        <span className="text-xs">{downloadSuccess === "pdf" ? "Downloaded!" : "PDF Report"}</span>
                      </Button>

                      <Button
                        onClick={handleDownloadJpg}
                        disabled={isDownloadingJpg}
                        variant="outline"
                        className={cn(
                          "h-20 flex-col gap-2",
                          downloadSuccess === "jpg" && "border-emerald-500 text-emerald-600 bg-emerald-50"
                        )}
                      >
                        {isDownloadingJpg ? (
                          <Loader2 className="w-5 h-5 animate-spin" />
                        ) : downloadSuccess === "jpg" ? (
                          <Check className="w-5 h-5" />
                        ) : (
                          <Sparkles className="w-5 h-5" />
                        )}
                        <span className="text-xs">{downloadSuccess === "jpg" ? "Downloaded!" : "Social Image"}</span>
                      </Button>
                    </div>
                  </div>

                  {/* Divider */}
                  <div className="relative py-2">
                    <div className="absolute inset-0 flex items-center">
                      <div className="w-full border-t border-border" />
                    </div>
                    <div className="relative flex justify-center">
                      <span className="bg-card px-3 text-xs text-muted-foreground">or</span>
                    </div>
                  </div>

                  {/* Email Test */}
                  <div className="space-y-2">
                    <Label className="text-xs font-medium text-muted-foreground">Send Test Email</Label>
                    <div className="flex gap-2">
                      <Input
                        type="email"
                        value={testEmail}
                        onChange={(e) => setTestEmail(e.target.value)}
                        placeholder="your@email.com"
                        className="flex-1 h-10"
                      />
                      <Button
                        onClick={handleSendTestEmail}
                        disabled={isSending}
                        className={cn(
                          "h-10 w-10 p-0",
                          sendSuccess && "bg-emerald-600 hover:bg-emerald-700"
                        )}
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
                      <p className="text-xs text-emerald-600 flex items-center gap-1">
                        <Check className="w-3 h-3" />
                        Test email sent! Check your inbox.
                      </p>
                    )}
                  </div>

                  {/* Tip */}
                  <div className="p-3 rounded-lg bg-amber-50 border border-amber-200">
                    <p className="text-xs text-amber-800 flex items-start gap-2">
                      <Lightbulb className="w-4 h-4 flex-shrink-0 mt-0.5" />
                      Remember to save your changes before testing!
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  )
}
