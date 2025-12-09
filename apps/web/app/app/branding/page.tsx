"use client"

import { useEffect, useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { 
  Save, 
  Loader2, 
  User, 
  Building2, 
  Palette,
  Eye,
  Mail,
  Globe,
  Phone,
  FileText,
  Download,
  Check,
  AlertCircle,
} from "lucide-react"
import { useToast } from "@/components/ui/use-toast"
import { ImageUpload } from "@/components/ui/image-upload"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { REPORT_TYPE_OPTIONS, ReportType } from "@/lib/sample-report-data"
import { cn } from "@/lib/utils"

type BrandingData = {
  brand_display_name: string
  logo_url: string | null
  primary_color: string | null
  accent_color: string | null
  rep_photo_url: string | null
  contact_line1: string | null
  contact_line2: string | null
  website_url: string | null
}

type FormData = BrandingData & {
  rep_name: string
  rep_title: string
  rep_email: string
  rep_phone: string
}

function parseContactLine1(line: string | null): { name: string; title: string } {
  if (!line) return { name: "", title: "" }
  if (line.includes("•")) {
    const parts = line.split("•").map(p => p.trim())
    return { name: parts[0] || "", title: parts[1] || "" }
  }
  return { name: line, title: "" }
}

function parseContactLine2(line: string | null): { phone: string; email: string } {
  if (!line) return { phone: "", email: "" }
  if (line.includes("•")) {
    const parts = line.split("•").map(p => p.trim())
    const emailPart = parts.find(p => p.includes("@")) || ""
    const phonePart = parts.find(p => !p.includes("@")) || ""
    return { phone: phonePart, email: emailPart }
  }
  if (line.includes("@")) return { phone: "", email: line }
  return { phone: line, email: "" }
}

function buildContactLine1(name: string, title: string): string | null {
  if (!name && !title) return null
  if (name && title) return `${name} • ${title}`
  return name || title
}

function buildContactLine2(phone: string, email: string): string | null {
  if (!phone && !email) return null
  if (phone && email) return `${phone} • ${email}`
  return phone || email
}

export default function BrandingPage() {
  const [isAffiliate, setIsAffiliate] = useState(false)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const { toast } = useToast()

  // Download & Email state
  const [reportType, setReportType] = useState<ReportType>("market_snapshot")
  const [isDownloading, setIsDownloading] = useState(false)
  const [downloadSuccess, setDownloadSuccess] = useState(false)
  const [downloadError, setDownloadError] = useState<string | null>(null)
  const [testEmail, setTestEmail] = useState("")
  const [isSending, setIsSending] = useState(false)
  const [sendSuccess, setSendSuccess] = useState(false)
  const [sendError, setSendError] = useState<string | null>(null)

  const [formData, setFormData] = useState<FormData>({
    brand_display_name: "",
    logo_url: null,
    primary_color: "#7C3AED",
    accent_color: "#F26B2B",
    rep_photo_url: null,
    contact_line1: null,
    contact_line2: null,
    website_url: null,
    rep_name: "",
    rep_title: "",
    rep_email: "",
    rep_phone: "",
  })

  useEffect(() => {
    loadData()
  }, [])

  async function loadData() {
    setLoading(true)
    try {
      const meRes = await fetch("/api/proxy/v1/me", { cache: "no-store" })
      const me = meRes.ok ? await meRes.json() : {}
      const isAff = me.account_type === "INDUSTRY_AFFILIATE"
      setIsAffiliate(isAff)

      const endpoint = isAff ? "/api/proxy/v1/affiliate/branding" : "/api/proxy/v1/account"
      const res = await fetch(endpoint, { cache: "no-store" })

      if (res.ok) {
        const data = await res.json()
        if (isAff) {
          const { name: repName, title: repTitle } = parseContactLine1(data.contact_line1)
          const { phone: repPhone, email: repEmail } = parseContactLine2(data.contact_line2)
          
          setFormData({
            brand_display_name: data.brand_display_name || "",
            logo_url: data.logo_url || null,
            primary_color: data.primary_color || "#7C3AED",
            accent_color: data.accent_color || "#F26B2B",
            rep_photo_url: data.rep_photo_url || null,
            contact_line1: data.contact_line1 || null,
            contact_line2: data.contact_line2 || null,
            website_url: data.website_url || null,
            rep_name: repName || me.name || "",
            rep_title: repTitle || "",
            rep_email: repEmail || me.email || "",
            rep_phone: repPhone || "",
          })
          setTestEmail(repEmail || me.email || "")
        } else {
          setFormData({
            brand_display_name: data.name || "",
            logo_url: data.logo_url || null,
            primary_color: data.primary_color || "#7C3AED",
            accent_color: data.secondary_color || "#F26B2B",
            rep_photo_url: null,
            contact_line1: null,
            contact_line2: null,
            website_url: null,
            rep_name: "",
            rep_title: "",
            rep_email: "",
            rep_phone: "",
          })
        }
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
      const endpoint = isAffiliate ? "/api/proxy/v1/affiliate/branding" : "/api/proxy/v1/account/branding"
      const contact_line1 = buildContactLine1(formData.rep_name, formData.rep_title)
      const contact_line2 = buildContactLine2(formData.rep_phone, formData.rep_email)

      const body = isAffiliate
        ? {
            brand_display_name: formData.brand_display_name,
            logo_url: formData.logo_url,
            primary_color: formData.primary_color,
            accent_color: formData.accent_color,
            rep_photo_url: formData.rep_photo_url,
            contact_line1,
            contact_line2,
            website_url: formData.website_url,
          }
        : {
            logo_url: formData.logo_url,
            primary_color: formData.primary_color,
            secondary_color: formData.accent_color,
          }

      const res = await fetch(endpoint, {
        method: isAffiliate ? "POST" : "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      })

      if (!res.ok) throw new Error("Failed to save branding")

      toast({
        title: "Saved!",
        description: "Your branding has been updated successfully.",
      })
      loadData()
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

  const handleDownloadPdf = async () => {
    setIsDownloading(true)
    setDownloadSuccess(false)
    setDownloadError(null)

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
      link.download = `${(formData.brand_display_name || "sample").replace(/\s+/g, "-").toLowerCase()}-${reportType.replace(/_/g, "-")}.pdf`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)

      setDownloadSuccess(true)
      setTimeout(() => setDownloadSuccess(false), 3000)
    } catch (err) {
      const message = err instanceof Error ? err.message : "Download failed"
      setDownloadError(message)
      setTimeout(() => setDownloadError(null), 5000)
    } finally {
      setIsDownloading(false)
    }
  }

  const handleSendTestEmail = async () => {
    if (!testEmail || !testEmail.includes("@")) {
      setSendError("Please enter a valid email address")
      return
    }

    setIsSending(true)
    setSendSuccess(false)
    setSendError(null)

    try {
      const response = await fetch("/api/proxy/v1/branding/test-email", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: testEmail, report_type: reportType }),
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.error || data.detail || "Failed to send email")
      }

      setSendSuccess(true)
      setTimeout(() => setSendSuccess(false), 5000)
    } catch (err) {
      const message = err instanceof Error ? err.message : "Send failed"
      setSendError(message)
      setTimeout(() => setSendError(null), 5000)
    } finally {
      setIsSending(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center">
          <Loader2 className="w-8 h-8 animate-spin text-primary mx-auto mb-4" />
          <p className="text-muted-foreground">Loading branding settings...</p>
        </div>
      </div>
    )
  }

  const primaryColor = formData.primary_color || "#7C3AED"
  const accentColor = formData.accent_color || "#F26B2B"

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">
            {isAffiliate ? "Affiliate Branding" : "Branding"}
          </h1>
          <p className="text-muted-foreground">
            {isAffiliate
              ? "Customize how your brand appears on all reports and emails"
              : "Personalize your reports with your brand"}
          </p>
        </div>
        <Button onClick={save} disabled={saving} className="gap-2">
          {saving ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              Saving...
            </>
          ) : (
            <>
              <Save className="w-4 h-4" />
              Save Changes
            </>
          )}
        </Button>
      </div>

      <div className="grid lg:grid-cols-2 gap-6">
        {/* LEFT: Settings Form */}
        <div className="space-y-6">
          <Tabs defaultValue="brand" className="w-full">
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="brand" className="gap-2">
                <Building2 className="w-4 h-4" />
                Brand
              </TabsTrigger>
              {isAffiliate && (
                <TabsTrigger value="contact" className="gap-2">
                  <User className="w-4 h-4" />
                  Contact Info
                </TabsTrigger>
              )}
              {!isAffiliate && (
                <TabsTrigger value="colors" className="gap-2">
                  <Palette className="w-4 h-4" />
                  Colors
                </TabsTrigger>
              )}
            </TabsList>

            {/* Brand Tab */}
            <TabsContent value="brand" className="mt-4 space-y-4">
              {/* Logo */}
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-base flex items-center gap-2">
                    <Building2 className="w-4 h-4 text-muted-foreground" />
                    Logo & Name
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <Label>Company Logo</Label>
                    <ImageUpload
                      label=""
                      value={formData.logo_url}
                      onChange={(url) => setFormData({ ...formData, logo_url: url })}
                      assetType="logo"
                      aspectRatio="wide"
                      helpText="PNG with transparency • 400×150px"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="brand_name">Brand Display Name</Label>
                    <Input
                      id="brand_name"
                      value={formData.brand_display_name}
                      onChange={(e) => setFormData({ ...formData, brand_display_name: e.target.value })}
                      placeholder="Your Company Name"
                    />
                  </div>
                </CardContent>
              </Card>

              {/* Colors */}
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-base flex items-center gap-2">
                    <Palette className="w-4 h-4 text-muted-foreground" />
                    Brand Colors
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>Primary</Label>
                      <div className="flex gap-2">
                        <div 
                          className="w-12 h-11 rounded-lg border-2 overflow-hidden cursor-pointer relative"
                          style={{ backgroundColor: primaryColor }}
                        >
                          <input
                            type="color"
                            value={primaryColor}
                            onChange={(e) => setFormData({ ...formData, primary_color: e.target.value })}
                            className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                          />
                        </div>
                        <Input
                          value={primaryColor}
                          onChange={(e) => setFormData({ ...formData, primary_color: e.target.value })}
                          className="flex-1 font-mono text-sm uppercase"
                          maxLength={7}
                        />
                      </div>
                    </div>
                    <div className="space-y-2">
                      <Label>Accent</Label>
                      <div className="flex gap-2">
                        <div 
                          className="w-12 h-11 rounded-lg border-2 overflow-hidden cursor-pointer relative"
                          style={{ backgroundColor: accentColor }}
                        >
                          <input
                            type="color"
                            value={accentColor}
                            onChange={(e) => setFormData({ ...formData, accent_color: e.target.value })}
                            className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                          />
                        </div>
                        <Input
                          value={accentColor}
                          onChange={(e) => setFormData({ ...formData, accent_color: e.target.value })}
                          className="flex-1 font-mono text-sm uppercase"
                          maxLength={7}
                        />
                      </div>
                    </div>
                  </div>
                  {/* Gradient Preview */}
                  <div 
                    className="h-10 rounded-lg"
                    style={{ background: `linear-gradient(135deg, ${primaryColor} 0%, ${accentColor} 100%)` }}
                  />
                </CardContent>
              </Card>
            </TabsContent>

            {/* Contact Tab (Affiliates only) */}
            {isAffiliate && (
              <TabsContent value="contact" className="mt-4 space-y-4">
                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-base flex items-center gap-2">
                      <User className="w-4 h-4 text-muted-foreground" />
                      Your Information
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    {/* Photo + Name Row */}
                    <div className="flex gap-4">
                      <div className="flex-shrink-0">
                        <Label className="text-sm mb-2 block">Photo</Label>
                        <div className="w-16 h-16 relative rounded-lg border-2 border-dashed overflow-hidden bg-muted/30 hover:bg-muted/50 transition-colors">
                          {formData.rep_photo_url ? (
                            <img
                              src={formData.rep_photo_url}
                              alt="Profile"
                              className="w-full h-full object-cover"
                            />
                          ) : (
                            <div className="w-full h-full flex items-center justify-center text-muted-foreground">
                              <User className="w-6 h-6" />
                            </div>
                          )}
                          <input
                            type="file"
                            accept="image/*"
                            className="absolute inset-0 opacity-0 cursor-pointer"
                            onChange={async (e) => {
                              const file = e.target.files?.[0]
                              if (!file) return
                              const formDataUpload = new FormData()
                              formDataUpload.append("file", file)
                              formDataUpload.append("asset_type", "headshot")
                              try {
                                const res = await fetch("/api/proxy/v1/assets/upload", {
                                  method: "POST",
                                  body: formDataUpload,
                                })
                                if (res.ok) {
                                  const data = await res.json()
                                  setFormData({ ...formData, rep_photo_url: data.url })
                                }
                              } catch (err) {
                                console.error("Upload failed:", err)
                              }
                            }}
                          />
                        </div>
                      </div>
                      <div className="flex-1 grid gap-3">
                        <div className="space-y-1">
                          <Label htmlFor="rep_name">Name</Label>
                          <Input
                            id="rep_name"
                            value={formData.rep_name}
                            onChange={(e) => setFormData({ ...formData, rep_name: e.target.value })}
                            placeholder="John Doe"
                          />
                        </div>
                        <div className="space-y-1">
                          <Label htmlFor="rep_title">Title</Label>
                          <Input
                            id="rep_title"
                            value={formData.rep_title}
                            onChange={(e) => setFormData({ ...formData, rep_title: e.target.value })}
                            placeholder="Senior Title Rep"
                          />
                        </div>
                      </div>
                    </div>

                    {/* Contact Details */}
                    <div className="grid grid-cols-2 gap-3">
                      <div className="space-y-1">
                        <Label htmlFor="rep_email" className="flex items-center gap-1">
                          <Mail className="w-3 h-3" /> Email
                        </Label>
                        <Input
                          id="rep_email"
                          type="email"
                          value={formData.rep_email}
                          onChange={(e) => setFormData({ ...formData, rep_email: e.target.value })}
                          placeholder="john@company.com"
                        />
                      </div>
                      <div className="space-y-1">
                        <Label htmlFor="rep_phone" className="flex items-center gap-1">
                          <Phone className="w-3 h-3" /> Phone
                        </Label>
                        <Input
                          id="rep_phone"
                          type="tel"
                          value={formData.rep_phone}
                          onChange={(e) => setFormData({ ...formData, rep_phone: e.target.value })}
                          placeholder="(555) 123-4567"
                        />
                      </div>
                    </div>
                    <div className="space-y-1">
                      <Label htmlFor="website" className="flex items-center gap-1">
                        <Globe className="w-3 h-3" /> Website
                      </Label>
                      <Input
                        id="website"
                        value={formData.website_url || ""}
                        onChange={(e) => setFormData({ ...formData, website_url: e.target.value })}
                        placeholder="https://www.yourcompany.com"
                      />
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>
            )}

            {/* Colors Tab (Non-affiliates) */}
            {!isAffiliate && (
              <TabsContent value="colors" className="mt-4 space-y-4">
                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-base flex items-center gap-2">
                      <Palette className="w-4 h-4 text-muted-foreground" />
                      Brand Colors
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label>Primary</Label>
                        <div className="flex gap-2">
                          <div 
                            className="w-12 h-11 rounded-lg border-2 overflow-hidden cursor-pointer relative"
                            style={{ backgroundColor: primaryColor }}
                          >
                            <input
                              type="color"
                              value={primaryColor}
                              onChange={(e) => setFormData({ ...formData, primary_color: e.target.value })}
                              className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                            />
                          </div>
                          <Input
                            value={primaryColor}
                            onChange={(e) => setFormData({ ...formData, primary_color: e.target.value })}
                            className="flex-1 font-mono text-sm uppercase"
                            maxLength={7}
                          />
                        </div>
                      </div>
                      <div className="space-y-2">
                        <Label>Accent</Label>
                        <div className="flex gap-2">
                          <div 
                            className="w-12 h-11 rounded-lg border-2 overflow-hidden cursor-pointer relative"
                            style={{ backgroundColor: accentColor }}
                          >
                            <input
                              type="color"
                              value={accentColor}
                              onChange={(e) => setFormData({ ...formData, accent_color: e.target.value })}
                              className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                            />
                          </div>
                          <Input
                            value={accentColor}
                            onChange={(e) => setFormData({ ...formData, accent_color: e.target.value })}
                            className="flex-1 font-mono text-sm uppercase"
                            maxLength={7}
                          />
                        </div>
                      </div>
                    </div>
                    <div 
                      className="h-10 rounded-lg"
                      style={{ background: `linear-gradient(135deg, ${primaryColor} 0%, ${accentColor} 100%)` }}
                    />
                  </CardContent>
                </Card>
              </TabsContent>
            )}
          </Tabs>
        </div>

        {/* RIGHT: Preview & Test */}
        <div className="space-y-6">
          {/* Test Your Branding - PROMINENT */}
          <Card className="border-2 border-primary/20 bg-primary/5">
            <CardHeader className="pb-3">
              <CardTitle className="text-base flex items-center gap-2">
                <FileText className="w-4 h-4 text-primary" />
                Test Your Branding
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Report Type Selector - PROMINENT */}
              <div className="space-y-2">
                <Label className="font-medium">Select Report Type</Label>
                <Select value={reportType} onValueChange={(v) => setReportType(v as ReportType)}>
                  <SelectTrigger className="w-full h-12 text-base">
                    <SelectValue placeholder="Select report type" />
                  </SelectTrigger>
                  <SelectContent>
                    {REPORT_TYPE_OPTIONS.map((type) => (
                      <SelectItem key={type.value} value={type.value}>
                        <div className="flex flex-col py-1">
                          <span className="font-medium">{type.label}</span>
                          <span className="text-xs text-muted-foreground">{type.description}</span>
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* Action Buttons */}
              <div className="grid grid-cols-2 gap-3">
                <Button
                  onClick={handleDownloadPdf}
                  disabled={isDownloading}
                  className={cn(
                    "h-12 gap-2",
                    downloadSuccess && "bg-green-600 hover:bg-green-600"
                  )}
                >
                  {isDownloading ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      Generating...
                    </>
                  ) : downloadSuccess ? (
                    <>
                      <Check className="w-4 h-4" />
                      Downloaded!
                    </>
                  ) : (
                    <>
                      <Download className="w-4 h-4" />
                      Download PDF
                    </>
                  )}
                </Button>
                <div className="space-y-1.5">
                  <div className="flex gap-2">
                    <Input
                      type="email"
                      placeholder="your@email.com"
                      value={testEmail}
                      onChange={(e) => setTestEmail(e.target.value)}
                      className="h-12 flex-1"
                    />
                    <Button
                      onClick={handleSendTestEmail}
                      disabled={isSending || !testEmail}
                      variant="outline"
                      className={cn(
                        "h-12 px-4",
                        sendSuccess && "border-green-600 text-green-600"
                      )}
                    >
                      {isSending ? (
                        <Loader2 className="w-4 h-4 animate-spin" />
                      ) : sendSuccess ? (
                        <Check className="w-4 h-4" />
                      ) : (
                        <Mail className="w-4 h-4" />
                      )}
                    </Button>
                  </div>
                </div>
              </div>

              {/* Errors */}
              {(downloadError || sendError) && (
                <div className="flex items-center gap-2 text-sm text-destructive">
                  <AlertCircle className="w-4 h-4" />
                  {downloadError || sendError}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Live Preview */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-base flex items-center gap-2">
                <Eye className="w-4 h-4 text-muted-foreground" />
                Live Preview
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Report Header Preview */}
              <div className="rounded-lg overflow-hidden border">
                <div
                  className="p-4"
                  style={{
                    background: `linear-gradient(135deg, ${primaryColor} 0%, ${accentColor} 100%)`,
                  }}
                >
                  <div className="flex items-center justify-between gap-4">
                    <div className="flex items-center gap-3">
                      {formData.logo_url ? (
                        <img
                          src={formData.logo_url}
                          className="h-8 w-auto max-w-[80px] object-contain brightness-0 invert"
                          alt={formData.brand_display_name}
                        />
                      ) : (
                        <div className="h-8 w-8 rounded bg-white/20 flex items-center justify-center text-white font-bold text-sm">
                          {(formData.brand_display_name || "B")[0].toUpperCase()}
                        </div>
                      )}
                      <div className="text-white">
                        <div className="font-semibold text-sm">{REPORT_TYPE_OPTIONS.find(t => t.value === reportType)?.label}</div>
                        <div className="text-xs opacity-80">Beverly Hills, CA</div>
                      </div>
                    </div>
                    <div className="text-right text-white text-xs opacity-80">
                      <div>{formData.brand_display_name || "Your Brand"}</div>
                    </div>
                  </div>
                </div>
                <div className="p-3 bg-white dark:bg-zinc-900">
                  <div className="grid grid-cols-3 gap-2">
                    {[
                      { label: "Median", value: "$1.85M" },
                      { label: "Sales", value: "42" },
                      { label: "DOM", value: "28" },
                    ].map((stat, i) => (
                      <div 
                        key={i}
                        className="p-2 rounded text-center text-white text-xs"
                        style={{ 
                          background: `linear-gradient(135deg, ${primaryColor} 0%, ${accentColor} 100%)` 
                        }}
                      >
                        <div className="opacity-70 text-[10px]">{stat.label}</div>
                        <div className="font-bold">{stat.value}</div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Footer Preview (Affiliates only) */}
              {isAffiliate && (
                <div className="rounded-lg overflow-hidden border">
                  <div className="p-3 bg-slate-50 dark:bg-zinc-900">
                    <div className="flex items-center justify-between gap-3">
                      <div className="flex items-center gap-2 min-w-0">
                        {formData.rep_photo_url ? (
                          <img
                            src={formData.rep_photo_url}
                            className="w-9 h-9 rounded-full object-cover flex-shrink-0"
                            style={{ border: `2px solid ${primaryColor}` }}
                            alt="Rep"
                          />
                        ) : (
                          <div 
                            className="w-9 h-9 rounded-full flex items-center justify-center text-white font-bold text-xs flex-shrink-0"
                            style={{ backgroundColor: primaryColor }}
                          >
                            {(formData.rep_name || "Y")[0].toUpperCase()}
                          </div>
                        )}
                        <div className="min-w-0 text-xs">
                          <div className="font-medium truncate">
                            {formData.rep_name || "Your Name"}
                            {formData.rep_title && <span className="text-muted-foreground"> • {formData.rep_title}</span>}
                          </div>
                          <div className="text-muted-foreground truncate">
                            {formData.rep_phone || formData.rep_email || "Contact info"}
                          </div>
                        </div>
                      </div>
                      {formData.logo_url && (
                        <img
                          src={formData.logo_url}
                          className="h-7 w-auto max-w-[60px] object-contain flex-shrink-0"
                          alt={formData.brand_display_name}
                        />
                      )}
                    </div>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
