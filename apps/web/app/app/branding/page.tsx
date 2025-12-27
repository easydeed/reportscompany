"use client"

import { useEffect, useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { 
  Save, 
  Loader2, 
  User, 
  Palette,
  Mail,
  Globe,
  Phone,
  FileText,
  Download,
  Check,
  AlertCircle,
  Send,
  Sparkles,
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
  // PDF logos
  logo_url: string | null
  footer_logo_url: string | null
  // Email logos
  email_logo_url: string | null
  email_footer_logo_url: string | null
  // Colors
  primary_color: string | null
  accent_color: string | null
  // Contact
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

  // For regular users, we use their profile avatar automatically
  const [userAvatarUrl, setUserAvatarUrl] = useState<string | null>(null)

  const [reportType, setReportType] = useState<ReportType>("market_snapshot")
  const [isDownloading, setIsDownloading] = useState(false)
  const [downloadSuccess, setDownloadSuccess] = useState(false)
  const [downloadError, setDownloadError] = useState<string | null>(null)
  const [isDownloadingJpg, setIsDownloadingJpg] = useState(false)
  const [downloadJpgSuccess, setDownloadJpgSuccess] = useState(false)
  const [downloadJpgError, setDownloadJpgError] = useState<string | null>(null)
  const [testEmail, setTestEmail] = useState("")
  const [isSending, setIsSending] = useState(false)
  const [sendSuccess, setSendSuccess] = useState(false)
  const [sendError, setSendError] = useState<string | null>(null)

  const [formData, setFormData] = useState<FormData>({
    brand_display_name: "",
    logo_url: null,
    footer_logo_url: null,
    email_logo_url: null,
    email_footer_logo_url: null,
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
      // Fetch ALL endpoints in parallel - use the right one based on user type
      const [meRes, affiliateBrandingRes, accountRes] = await Promise.all([
        fetch("/api/proxy/v1/me", { cache: "no-store", credentials: "include" }),
        fetch("/api/proxy/v1/affiliate/branding", { cache: "no-store", credentials: "include" }),
        fetch("/api/proxy/v1/account", { cache: "no-store", credentials: "include" }),
      ])
      
      const me = meRes.ok ? await meRes.json() : {}
      const isAff = me.account_type === "INDUSTRY_AFFILIATE"
      setIsAffiliate(isAff)
      
      // For regular users, capture their profile avatar
      if (!isAff && me.avatar_url) {
        setUserAvatarUrl(me.avatar_url)
      }

      // Use the appropriate response based on user type
      const res = isAff ? affiliateBrandingRes : accountRes

      if (res.ok) {
        const data = await res.json()
        if (isAff) {
          const { name: repName, title: repTitle } = parseContactLine1(data.contact_line1)
          const { phone: repPhone, email: repEmail } = parseContactLine2(data.contact_line2)
          
          setFormData({
            brand_display_name: data.brand_display_name || "",
            logo_url: data.logo_url || null,
            footer_logo_url: data.footer_logo_url || null,
            email_logo_url: data.email_logo_url || null,
            email_footer_logo_url: data.email_footer_logo_url || null,
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
          // Regular user - load all branding fields including contact info
          // Option A: Use their profile avatar_url as rep_photo automatically
          const { name: repName, title: repTitle } = parseContactLine1(data.contact_line1)
          const { phone: repPhone, email: repEmail } = parseContactLine2(data.contact_line2)
          
          setFormData({
            brand_display_name: data.name || "",
            logo_url: data.logo_url || null,
            footer_logo_url: data.footer_logo_url || null,
            email_logo_url: data.email_logo_url || null,
            email_footer_logo_url: data.email_footer_logo_url || null,
            primary_color: data.primary_color || "#7C3AED",
            accent_color: data.secondary_color || "#F26B2B",
            rep_photo_url: me.avatar_url || null, // Use profile avatar for regular users
            contact_line1: data.contact_line1 || null,
            contact_line2: data.contact_line2 || null,
            website_url: data.website_url || null,
            rep_name: repName || me.name || "",
            rep_title: repTitle || "",
            rep_email: repEmail || me.email || "",
            rep_phone: repPhone || "",
          })
          setTestEmail(repEmail || me.email || "")
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
            footer_logo_url: formData.footer_logo_url,
            email_logo_url: formData.email_logo_url,
            email_footer_logo_url: formData.email_footer_logo_url,
            primary_color: formData.primary_color,
            accent_color: formData.accent_color,
            rep_photo_url: formData.rep_photo_url,
            contact_line1,
            contact_line2,
            website_url: formData.website_url,
          }
        : {
            // Regular users - headshot comes from profile (users.avatar_url)
            logo_url: formData.logo_url,
            footer_logo_url: formData.footer_logo_url,
            email_logo_url: formData.email_logo_url,
            email_footer_logo_url: formData.email_footer_logo_url,
            primary_color: formData.primary_color,
            secondary_color: formData.accent_color,
            // Note: rep_photo_url not saved - regular users use their profile avatar_url
            contact_line1,
            contact_line2,
            website_url: formData.website_url,
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

  const handleDownloadJpg = async () => {
    setIsDownloadingJpg(true)
    setDownloadJpgSuccess(false)
    setDownloadJpgError(null)

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
      link.download = `${(formData.brand_display_name || "sample").replace(/\s+/g, "-").toLowerCase()}-${reportType.replace(/_/g, "-")}-social.jpg`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)

      setDownloadJpgSuccess(true)
      setTimeout(() => setDownloadJpgSuccess(false), 3000)
    } catch (err) {
      const message = err instanceof Error ? err.message : "Download failed"
      setDownloadJpgError(message)
      setTimeout(() => setDownloadJpgError(null), 5000)
    } finally {
      setIsDownloadingJpg(false)
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
    <div className="space-y-6">
      {/* ========== HEADER ========== */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Brand Studio</h1>
          <p className="text-muted-foreground mt-1">
            Design how your brand appears on reports and emails
          </p>
        </div>
        <Button 
          onClick={save} 
          disabled={saving} 
          size="lg"
        >
          {saving ? (
            <><Loader2 className="w-4 h-4 animate-spin mr-2" /> Saving...</>
          ) : (
            <><Save className="w-4 h-4 mr-2" /> Save Changes</>
          )}
        </Button>
      </div>

      {/* Color Preview Bar */}
      <div 
        className="rounded-xl p-4 flex items-center justify-between"
        style={{ background: `linear-gradient(135deg, ${primaryColor} 0%, ${accentColor} 100%)` }}
      >
        <div className="flex items-center gap-3">
          <div className="p-2 bg-white/20 rounded-lg backdrop-blur-sm">
            <Sparkles className="h-5 w-5 text-white" />
          </div>
          <div className="text-white">
            <p className="font-semibold text-sm">Live Color Preview</p>
            <p className="text-white/70 text-xs">This is how your brand gradient looks</p>
          </div>
        </div>
        {formData.logo_url && (
          <img src={formData.logo_url} alt="Logo" className="h-8 w-auto brightness-0 invert" />
        )}
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
          {/* ========== LEFT COLUMN: FORM ========== */}
          <div className="lg:col-span-2 space-y-6">
            
            {/* SECTION 1: Company Name + Colors */}
            <section>
              <div className="flex items-center gap-2 mb-4">
                <div className="p-1.5 rounded-lg bg-violet-100 dark:bg-violet-900/30">
                  <Palette className="w-4 h-4 text-violet-600" />
                </div>
                <h2 className="font-semibold text-lg">Brand Identity</h2>
              </div>
              
              <div className="bg-card border rounded-xl p-5 space-y-5">
                <div>
                  <Label htmlFor="brand_name" className="text-sm font-medium">Company Name</Label>
                  <Input
                    id="brand_name"
                    value={formData.brand_display_name}
                    onChange={(e) => setFormData({ ...formData, brand_display_name: e.target.value })}
                    placeholder="Pacific Coast Title"
                    className="mt-1.5 h-11"
                  />
                </div>

                <div className="grid sm:grid-cols-2 gap-5">
                  <div>
                    <Label className="text-sm font-medium">Primary Color</Label>
                    <p className="text-xs text-muted-foreground mb-2">Headers & ribbons</p>
                    <div className="flex gap-2">
                      <div 
                        className="w-14 h-11 rounded-lg border-2 cursor-pointer relative shadow-sm flex-shrink-0"
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
                        className="font-mono text-sm uppercase h-11"
                        maxLength={7}
                      />
                    </div>
                  </div>
                  <div>
                    <Label className="text-sm font-medium">Accent Color</Label>
                    <p className="text-xs text-muted-foreground mb-2">Buttons & highlights</p>
                    <div className="flex gap-2">
                      <div 
                        className="w-14 h-11 rounded-lg border-2 cursor-pointer relative shadow-sm flex-shrink-0"
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
                        className="font-mono text-sm uppercase h-11"
                        maxLength={7}
                      />
                    </div>
                  </div>
                </div>
              </div>
            </section>

            {/* SECTION 2: PDF Logos */}
            <section>
              <div className="flex items-center gap-2 mb-4">
                <div className="p-1.5 rounded-lg bg-red-100 dark:bg-red-900/30">
                  <FileText className="w-4 h-4 text-red-600" />
                </div>
                <h2 className="font-semibold text-lg">PDF Report Logos</h2>
                <span className="text-xs text-muted-foreground ml-auto">For downloadable PDF reports</span>
              </div>
              
              <div className="bg-card border rounded-xl p-5">
                <div className="grid sm:grid-cols-2 gap-5">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <div className="w-6 h-6 rounded flex items-center justify-center text-white text-xs font-bold"
                           style={{ background: `linear-gradient(135deg, ${primaryColor}, ${accentColor})` }}>H</div>
                      <Label className="text-sm font-medium">Header Logo</Label>
                    </div>
                    <p className="text-xs text-muted-foreground mb-2">Appears on gradient header • use light/white version</p>
                    <ImageUpload
                      label=""
                      value={formData.logo_url}
                      onChange={(url) => setFormData({ ...formData, logo_url: url })}
                      assetType="logo"
                      aspectRatio="wide"
                      helpText=""
                    />
                  </div>
                  
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <div className="w-6 h-6 rounded flex items-center justify-center bg-slate-200 text-slate-600 text-xs font-bold">F</div>
                      <Label className="text-sm font-medium">Footer Logo</Label>
                    </div>
                    <p className="text-xs text-muted-foreground mb-2">Appears on gray footer • use dark/colored version</p>
                    <ImageUpload
                      label=""
                      value={formData.footer_logo_url}
                      onChange={(url) => setFormData({ ...formData, footer_logo_url: url })}
                      assetType="logo"
                      aspectRatio="wide"
                      helpText=""
                    />
                  </div>
                </div>
              </div>
            </section>

            {/* SECTION 3: Email Logos */}
            <section>
              <div className="flex items-center gap-2 mb-4">
                <div className="p-1.5 rounded-lg bg-purple-100 dark:bg-purple-900/30">
                  <Mail className="w-4 h-4 text-purple-600" />
                </div>
                <h2 className="font-semibold text-lg">Email Logos</h2>
                <span className="text-xs text-muted-foreground ml-auto">For report delivery emails</span>
              </div>
              
              <div className="bg-card border rounded-xl p-5">
                <div className="grid sm:grid-cols-2 gap-5">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <div className="w-6 h-6 rounded flex items-center justify-center text-white text-xs font-bold"
                           style={{ background: `linear-gradient(135deg, ${primaryColor}, ${accentColor})` }}>H</div>
                      <Label className="text-sm font-medium">Header Logo</Label>
                    </div>
                    <p className="text-xs text-muted-foreground mb-2">Appears on gradient header • use light/white version</p>
                    <ImageUpload
                      label=""
                      value={formData.email_logo_url}
                      onChange={(url) => setFormData({ ...formData, email_logo_url: url })}
                      assetType="logo"
                      aspectRatio="wide"
                      helpText=""
                    />
                  </div>
                  
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <div className="w-6 h-6 rounded flex items-center justify-center bg-white border text-slate-600 text-xs font-bold">F</div>
                      <Label className="text-sm font-medium">Footer Logo</Label>
                    </div>
                    <p className="text-xs text-muted-foreground mb-2">Appears on white footer • use dark/colored version</p>
                    <ImageUpload
                      label=""
                      value={formData.email_footer_logo_url}
                      onChange={(url) => setFormData({ ...formData, email_footer_logo_url: url })}
                      assetType="logo"
                      aspectRatio="wide"
                      helpText=""
                    />
                  </div>
                </div>
              </div>
            </section>

            {/* SECTION 4: Contact Info (All users) */}
            <section>
              <div className="flex items-center gap-2 mb-4">
                <div className="p-1.5 rounded-lg bg-blue-100 dark:bg-blue-900/30">
                  <User className="w-4 h-4 text-blue-600" />
                </div>
                <h2 className="font-semibold text-lg">Contact Information</h2>
                <span className="text-xs text-muted-foreground ml-auto">Appears on report footers</span>
              </div>
              
              <div className="bg-card border rounded-xl p-5 space-y-5">
                <div className="flex gap-4">
                  <div className="flex-shrink-0">
                    <Label className="text-sm font-medium mb-2 block">
                      {isAffiliate ? "Rep Photo" : "Your Headshot"}
                    </Label>
                    
                    {isAffiliate ? (
                      // Affiliates can upload a rep photo
                      <div className="w-20 h-20 relative rounded-xl border-2 border-dashed overflow-hidden bg-muted/30 hover:bg-muted/50 transition-colors">
                        {formData.rep_photo_url ? (
                          <img src={formData.rep_photo_url} alt="Profile" className="w-full h-full object-cover" />
                        ) : (
                          <div className="w-full h-full flex items-center justify-center text-muted-foreground">
                            <User className="w-8 h-8" />
                          </div>
                        )}
                        <input
                          type="file"
                          accept="image/*"
                          className="absolute inset-0 opacity-0 cursor-pointer"
                          onChange={async (e) => {
                            const file = e.target.files?.[0]
                            if (!file) return
                            const fd = new FormData()
                            fd.append("file", file)
                            try {
                              const res = await fetch("/api/proxy/v1/upload/branding/headshot", { method: "POST", body: fd })
                              if (res.ok) {
                                const data = await res.json()
                                setFormData({ ...formData, rep_photo_url: data.url })
                              }
                            } catch (err) { console.error("Upload failed:", err) }
                          }}
                        />
                      </div>
                    ) : (
                      // Regular users see their profile photo (from Account Settings)
                      <div className="space-y-2">
                        <div className="w-20 h-20 rounded-xl border overflow-hidden bg-muted/30">
                          {userAvatarUrl || formData.rep_photo_url ? (
                            <img 
                              src={userAvatarUrl || formData.rep_photo_url || ""} 
                              alt="Profile" 
                              className="w-full h-full object-cover" 
                            />
                          ) : (
                            <div className="w-full h-full flex items-center justify-center text-muted-foreground">
                              <User className="w-8 h-8" />
                            </div>
                          )}
                        </div>
                        <a 
                          href="/app/account/settings" 
                          className="text-xs text-primary hover:underline block"
                        >
                          Edit in Profile →
                        </a>
                      </div>
                    )}
                  </div>
                  
                  <div className="flex-1 space-y-3">
                    <div>
                      <Label htmlFor="rep_name" className="text-sm">Full Name</Label>
                      <Input
                        id="rep_name"
                        value={formData.rep_name}
                        onChange={(e) => setFormData({ ...formData, rep_name: e.target.value })}
                        placeholder="John Doe"
                        className="mt-1 h-10"
                      />
                    </div>
                    <div>
                      <Label htmlFor="rep_title" className="text-sm">Job Title</Label>
                      <Input
                        id="rep_title"
                        value={formData.rep_title}
                        onChange={(e) => setFormData({ ...formData, rep_title: e.target.value })}
                        placeholder={isAffiliate ? "Senior Title Rep" : "Real Estate Agent"}
                        className="mt-1 h-10"
                      />
                    </div>
                  </div>
                </div>

                <div className="grid sm:grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="rep_email" className="text-sm flex items-center gap-1.5">
                      <Mail className="w-3.5 h-3.5 text-muted-foreground" /> Email
                    </Label>
                    <Input
                      id="rep_email"
                      type="email"
                      value={formData.rep_email}
                      onChange={(e) => setFormData({ ...formData, rep_email: e.target.value })}
                      placeholder="john@company.com"
                      className="mt-1 h-10"
                    />
                  </div>
                  <div>
                    <Label htmlFor="rep_phone" className="text-sm flex items-center gap-1.5">
                      <Phone className="w-3.5 h-3.5 text-muted-foreground" /> Phone
                    </Label>
                    <Input
                      id="rep_phone"
                      type="tel"
                      value={formData.rep_phone}
                      onChange={(e) => setFormData({ ...formData, rep_phone: e.target.value })}
                      placeholder="(555) 123-4567"
                      className="mt-1 h-10"
                    />
                  </div>
                </div>

                <div>
                  <Label htmlFor="website" className="text-sm flex items-center gap-1.5">
                    <Globe className="w-3.5 h-3.5 text-muted-foreground" /> Website
                  </Label>
                  <Input
                    id="website"
                    value={formData.website_url || ""}
                    onChange={(e) => setFormData({ ...formData, website_url: e.target.value })}
                    placeholder="https://www.yourcompany.com"
                    className="mt-1 h-10"
                  />
                </div>
              </div>
            </section>

            {/* SECTION 5: Test Your Branding */}
            <section>
              <div className="flex items-center gap-2 mb-4">
                <div className="p-1.5 rounded-lg bg-green-100 dark:bg-green-900/30">
                  <Download className="w-4 h-4 text-green-600" />
                </div>
                <h2 className="font-semibold text-lg">Test Your Branding</h2>
              </div>
              
              <div className="bg-card border rounded-xl p-5">
                <div className="mb-4">
                  <Label className="text-sm font-medium">Report Type</Label>
                  <Select value={reportType} onValueChange={(v) => setReportType(v as ReportType)}>
                    <SelectTrigger className="mt-1.5 h-11">
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

                <div className="grid sm:grid-cols-3 gap-4">
                  {/* PDF Download */}
                  <div className="p-4 rounded-lg border bg-red-50 dark:bg-red-900/10">
                    <div className="flex items-center gap-2 mb-3">
                      <FileText className="w-4 h-4 text-red-600" />
                      <span className="font-medium text-sm">Sample PDF</span>
                    </div>
                    <Button
                      onClick={handleDownloadPdf}
                      disabled={isDownloading}
                      variant="outline"
                      className={cn("w-full h-10", downloadSuccess && "border-green-600 text-green-600")}
                    >
                      {isDownloading ? (
                        <><Loader2 className="w-4 h-4 animate-spin mr-2" /> Generating...</>
                      ) : downloadSuccess ? (
                        <><Check className="w-4 h-4 mr-2" /> Downloaded!</>
                      ) : (
                        <><Download className="w-4 h-4 mr-2" /> PDF</>
                      )}
                    </Button>
                    {downloadError && (
                      <p className="text-xs text-destructive mt-2 flex items-center gap-1">
                        <AlertCircle className="w-3 h-3" /> {downloadError}
                      </p>
                    )}
                  </div>

                  {/* JPG Social Download */}
                  <div className="p-4 rounded-lg border bg-pink-50 dark:bg-pink-900/10">
                    <div className="flex items-center gap-2 mb-3">
                      <Sparkles className="w-4 h-4 text-pink-600" />
                      <span className="font-medium text-sm">Social Image</span>
                    </div>
                    <Button
                      onClick={handleDownloadJpg}
                      disabled={isDownloadingJpg}
                      variant="outline"
                      className={cn("w-full h-10", downloadJpgSuccess && "border-green-600 text-green-600")}
                    >
                      {isDownloadingJpg ? (
                        <><Loader2 className="w-4 h-4 animate-spin mr-2" /> Generating...</>
                      ) : downloadJpgSuccess ? (
                        <><Check className="w-4 h-4 mr-2" /> Downloaded!</>
                      ) : (
                        <><Download className="w-4 h-4 mr-2" /> JPG</>
                      )}
                    </Button>
                    <p className="text-xs text-muted-foreground mt-2">1080×1920 for Stories</p>
                    {downloadJpgError && (
                      <p className="text-xs text-destructive mt-1 flex items-center gap-1">
                        <AlertCircle className="w-3 h-3" /> {downloadJpgError}
                      </p>
                    )}
                  </div>

                  {/* Test Email */}
                  <div className="p-4 rounded-lg border bg-purple-50 dark:bg-purple-900/10">
                    <div className="flex items-center gap-2 mb-3">
                      <Mail className="w-4 h-4 text-purple-600" />
                      <span className="font-medium text-sm">Test Email</span>
                    </div>
                    <div className="flex gap-2">
                      <Input
                        type="email"
                        placeholder="your@email.com"
                        value={testEmail}
                        onChange={(e) => setTestEmail(e.target.value)}
                        className="h-10 text-sm"
                      />
                      <Button
                        onClick={handleSendTestEmail}
                        disabled={isSending || !testEmail}
                        variant="outline"
                        size="icon"
                        className={cn("h-10 w-10 flex-shrink-0", sendSuccess && "border-green-600 text-green-600")}
                      >
                        {isSending ? <Loader2 className="w-4 h-4 animate-spin" /> : 
                         sendSuccess ? <Check className="w-4 h-4" /> : <Send className="w-4 h-4" />}
                      </Button>
                    </div>
                    {sendError && (
                      <p className="text-xs text-destructive mt-2 flex items-center gap-1">
                        <AlertCircle className="w-3 h-3" /> {sendError}
                      </p>
                    )}
                  </div>
                </div>
              </div>
            </section>
          </div>

          {/* ========== RIGHT COLUMN: LIVE PREVIEW ========== */}
          <div className="lg:col-span-1">
            <div className="lg:sticky lg:top-6 space-y-4">
              <div className="text-sm font-medium text-muted-foreground flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
                Live Preview
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
                    className="p-3"
                    style={{ background: `linear-gradient(135deg, ${primaryColor} 0%, ${accentColor} 100%)` }}
                  >
                    <div className="flex items-center gap-2">
                      {formData.logo_url ? (
                        <img src={formData.logo_url} className="h-6 w-auto max-w-[60px] object-contain brightness-0 invert" alt="" />
                      ) : (
                        <div className="h-6 w-6 rounded bg-white/20 flex items-center justify-center text-white font-bold text-xs">
                          {(formData.brand_display_name || "B")[0].toUpperCase()}
                        </div>
                      )}
                      <div className="text-white text-xs">
                        <div className="font-semibold">Market Snapshot</div>
                      </div>
                    </div>
                  </div>
                  {/* Content */}
                  <div className="p-3 space-y-2">
                    <div className="h-1.5 bg-slate-100 rounded w-full" />
                    <div className="h-1.5 bg-slate-100 rounded w-3/4" />
                  </div>
                  {/* Footer */}
                  <div className="p-3 bg-slate-50 border-t flex items-center justify-between">
                    {formData.rep_name && (
                      <div className="text-[10px] text-slate-600 truncate">{formData.rep_name}</div>
                    )}
                    {(formData.footer_logo_url || formData.logo_url) ? (
                      <img src={formData.footer_logo_url || formData.logo_url || ""} className="h-5 w-auto max-w-[50px] object-contain ml-auto" alt="" />
                    ) : (
                      <div className="text-[10px] font-semibold ml-auto" style={{ color: primaryColor }}>
                        {formData.brand_display_name || "Your Brand"}
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
                    style={{ background: `linear-gradient(135deg, ${primaryColor} 0%, ${accentColor} 100%)` }}
                  >
                    <div className="flex items-center gap-2">
                      {formData.email_logo_url ? (
                        <img src={formData.email_logo_url} className="h-6 w-auto max-w-[60px] object-contain" alt="" />
                      ) : formData.logo_url ? (
                        <img src={formData.logo_url} className="h-6 w-auto max-w-[60px] object-contain brightness-0 invert" alt="" />
                      ) : (
                        <div className="h-6 w-6 rounded bg-white/20 flex items-center justify-center text-white font-bold text-xs">
                          {(formData.brand_display_name || "B")[0].toUpperCase()}
                        </div>
                      )}
                      <div className="text-white text-xs font-semibold">
                        {formData.brand_display_name || "Your Brand"}
                      </div>
                    </div>
                  </div>
                  {/* Content */}
                  <div className="p-3 space-y-2">
                    <div className="text-[10px] text-slate-600">Your report is ready!</div>
                    <div className="h-1.5 bg-slate-100 rounded w-full" />
                    <div className="h-1.5 bg-slate-100 rounded w-2/3" />
                  </div>
                  {/* Footer */}
                  <div className="p-3 bg-white border-t flex items-center justify-between">
                    {formData.rep_name && (
                      <div className="text-[10px] text-slate-600 truncate">{formData.rep_name}</div>
                    )}
                    {(formData.email_footer_logo_url || formData.footer_logo_url || formData.logo_url) ? (
                      <img src={formData.email_footer_logo_url || formData.footer_logo_url || formData.logo_url || ""} className="h-5 w-auto max-w-[50px] object-contain ml-auto" alt="" />
                    ) : (
                      <div className="text-[10px] font-semibold ml-auto" style={{ color: primaryColor }}>
                        {formData.brand_display_name || "Your Brand"}
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* Tip */}
              <div className="p-3 rounded-lg bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800">
                <p className="text-xs text-amber-800 dark:text-amber-200">
                  <strong>Tip:</strong> Header logos appear on your brand gradient — use light/white versions. 
                  Footer logos appear on light backgrounds — use dark/colored versions.
                </p>
              </div>
            </div>
          </div>
        </div>
    </div>
  )
}
