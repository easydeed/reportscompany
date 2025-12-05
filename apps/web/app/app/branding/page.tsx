"use client"

import { useEffect, useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Separator } from "@/components/ui/separator"
import { 
  Save, 
  Loader2, 
  Upload, 
  User, 
  Building2, 
  Palette,
  Eye,
  Download,
  Mail,
  FileText,
  Globe,
  Phone,
  Sparkles,
} from "lucide-react"
import { useToast } from "@/components/ui/use-toast"
import { ImageUpload } from "@/components/ui/image-upload"
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

  return (
    <div className="max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-2">
          <div 
            className="w-10 h-10 rounded-xl flex items-center justify-center"
            style={{ background: `linear-gradient(135deg, ${formData.primary_color} 0%, ${formData.accent_color} 100%)` }}
          >
            <Sparkles className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-bold tracking-tight">
              {isAffiliate ? "Affiliate Branding" : "Branding"}
            </h1>
            <p className="text-sm text-muted-foreground">
              {isAffiliate
                ? "Customize how your brand appears on all reports and emails"
                : "Personalize your reports with your brand"}
            </p>
          </div>
        </div>
      </div>

      {/* Main Layout: Form + Preview */}
      <div className="grid lg:grid-cols-5 gap-8">
        {/* Left Column: Form */}
        <div className="lg:col-span-3 space-y-6">
          
          {/* Section 1: Brand Identity */}
          <Card className="overflow-hidden">
            <div className="px-6 py-4 bg-gradient-to-r from-violet-50 to-transparent dark:from-violet-950/30 border-b">
              <div className="flex items-center gap-3">
                <Building2 className="w-5 h-5 text-violet-600" />
                <div>
                  <h2 className="font-semibold">Brand Identity</h2>
                  <p className="text-xs text-muted-foreground">Your company logo and name</p>
                </div>
              </div>
            </div>
            <CardContent className="p-6 space-y-6">
              {/* Logo Upload */}
              <div className="space-y-3">
                <Label className="text-sm font-medium">Company Logo</Label>
                <ImageUpload
                  label=""
                  value={formData.logo_url}
                  onChange={(url) => setFormData({ ...formData, logo_url: url })}
                  assetType="logo"
                  aspectRatio="wide"
                  helpText="PNG with transparency recommended • 400×150px or similar"
                />
              </div>

              {/* Brand Name */}
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

          {/* Section 2: Colors */}
          <Card className="overflow-hidden">
            <div className="px-6 py-4 bg-gradient-to-r from-pink-50 to-transparent dark:from-pink-950/30 border-b">
              <div className="flex items-center gap-3">
                <Palette className="w-5 h-5 text-pink-600" />
                <div>
                  <h2 className="font-semibold">Brand Colors</h2>
                  <p className="text-xs text-muted-foreground">Customize your report appearance</p>
                </div>
              </div>
            </div>
            <CardContent className="p-6">
              <div className="grid sm:grid-cols-2 gap-6">
                {/* Primary Color */}
                <div className="space-y-3">
                  <Label>Primary Color</Label>
                  <div className="flex gap-3">
                    <div 
                      className="w-14 h-11 rounded-lg border-2 border-border overflow-hidden cursor-pointer relative"
                      style={{ backgroundColor: formData.primary_color || "#7C3AED" }}
                    >
                      <input
                        type="color"
                        value={formData.primary_color || "#7C3AED"}
                        onChange={(e) => setFormData({ ...formData, primary_color: e.target.value })}
                        className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                      />
                    </div>
                    <Input
                      type="text"
                      value={formData.primary_color || "#7C3AED"}
                      onChange={(e) => setFormData({ ...formData, primary_color: e.target.value })}
                      className="flex-1 font-mono text-sm uppercase"
                      maxLength={7}
                    />
                  </div>
                  <p className="text-xs text-muted-foreground">Used for headers, buttons, and accents</p>
                </div>

                {/* Accent Color */}
                <div className="space-y-3">
                  <Label>Accent Color</Label>
                  <div className="flex gap-3">
                    <div 
                      className="w-14 h-11 rounded-lg border-2 border-border overflow-hidden cursor-pointer relative"
                      style={{ backgroundColor: formData.accent_color || "#F26B2B" }}
                    >
                      <input
                        type="color"
                        value={formData.accent_color || "#F26B2B"}
                        onChange={(e) => setFormData({ ...formData, accent_color: e.target.value })}
                        className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                      />
                    </div>
                    <Input
                      type="text"
                      value={formData.accent_color || "#F26B2B"}
                      onChange={(e) => setFormData({ ...formData, accent_color: e.target.value })}
                      className="flex-1 font-mono text-sm uppercase"
                      maxLength={7}
                    />
                  </div>
                  <p className="text-xs text-muted-foreground">Used for gradients and highlights</p>
                </div>
              </div>

              {/* Color Preview Bar */}
              <div className="mt-6 p-4 rounded-lg border bg-muted/30">
                <p className="text-xs text-muted-foreground mb-3">Preview</p>
                <div 
                  className="h-12 rounded-lg"
                  style={{ 
                    background: `linear-gradient(135deg, ${formData.primary_color || "#7C3AED"} 0%, ${formData.accent_color || "#F26B2B"} 100%)` 
                  }}
                />
              </div>
            </CardContent>
          </Card>

          {/* Section 3: Contact Info (Affiliates Only) */}
          {isAffiliate && (
            <Card className="overflow-hidden">
              <div className="px-6 py-4 bg-gradient-to-r from-emerald-50 to-transparent dark:from-emerald-950/30 border-b">
                <div className="flex items-center gap-3">
                  <User className="w-5 h-5 text-emerald-600" />
                  <div>
                    <h2 className="font-semibold">Your Information</h2>
                    <p className="text-xs text-muted-foreground">Displayed in report footers and emails</p>
                  </div>
                </div>
              </div>
              <CardContent className="p-6 space-y-6">
                {/* Photo Upload */}
                <div className="space-y-3">
                  <Label className="text-sm font-medium">Profile Photo</Label>
                  <ImageUpload
                    label=""
                    value={formData.rep_photo_url}
                    onChange={(url) => setFormData({ ...formData, rep_photo_url: url })}
                    assetType="headshot"
                    aspectRatio="square"
                    helpText="Square format recommended • 400×400px"
                  />
                </div>

                <Separator />

                {/* Name & Title */}
                <div className="grid sm:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="rep_name" className="flex items-center gap-2">
                      <User className="w-3.5 h-3.5 text-muted-foreground" />
                      Your Name
                    </Label>
                    <Input
                      id="rep_name"
                      value={formData.rep_name}
                      onChange={(e) => setFormData({ ...formData, rep_name: e.target.value })}
                      placeholder="John Doe"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="rep_title">Title</Label>
                    <Input
                      id="rep_title"
                      value={formData.rep_title}
                      onChange={(e) => setFormData({ ...formData, rep_title: e.target.value })}
                      placeholder="Senior Title Rep"
                    />
                  </div>
                </div>

                {/* Email & Phone */}
                <div className="grid sm:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="rep_email" className="flex items-center gap-2">
                      <Mail className="w-3.5 h-3.5 text-muted-foreground" />
                      Email
                    </Label>
                    <Input
                      id="rep_email"
                      type="email"
                      value={formData.rep_email}
                      onChange={(e) => setFormData({ ...formData, rep_email: e.target.value })}
                      placeholder="john@company.com"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="rep_phone" className="flex items-center gap-2">
                      <Phone className="w-3.5 h-3.5 text-muted-foreground" />
                      Phone
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

                {/* Website */}
                <div className="space-y-2">
                  <Label htmlFor="website" className="flex items-center gap-2">
                    <Globe className="w-3.5 h-3.5 text-muted-foreground" />
                    Website
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
          )}

          {/* Save Button */}
          <Button 
            onClick={save} 
            disabled={saving} 
            size="lg" 
            className="w-full gap-2"
          >
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

        {/* Right Column: Live Preview (Sticky) */}
        <div className="lg:col-span-2">
          <div className="lg:sticky lg:top-6 space-y-4">
            <div className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
              <Eye className="w-4 h-4" />
              Live Preview
            </div>

            {/* Report Header Preview */}
            <Card className="overflow-hidden">
              <div
                className="p-5"
                style={{
                  background: `linear-gradient(135deg, ${formData.primary_color || "#7C3AED"} 0%, ${formData.accent_color || "#F26B2B"} 100%)`,
                }}
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex items-center gap-3">
                    {formData.logo_url ? (
                      <img
                        src={formData.logo_url}
                        className="h-10 w-auto max-w-[100px] object-contain brightness-0 invert"
                        alt={formData.brand_display_name}
                      />
                    ) : (
                      <div className="h-10 w-10 rounded-lg bg-white/20 flex items-center justify-center text-white font-bold text-lg">
                        {(formData.brand_display_name || "B")[0].toUpperCase()}
                      </div>
                    )}
                    <div className="text-white">
                      <div className="font-semibold text-sm">Market Snapshot</div>
                      <div className="text-xs opacity-80">Beverly Hills, CA</div>
                    </div>
                  </div>
                  <div className="text-right text-white text-xs opacity-80">
                    <div>{formData.brand_display_name || "Your Brand"}</div>
                    <div>Dec 2025</div>
                  </div>
                </div>
              </div>
              <div className="p-4 bg-white dark:bg-zinc-900">
                <div className="grid grid-cols-3 gap-3">
                  {[
                    { label: "Median Price", value: "$1.85M" },
                    { label: "Closed Sales", value: "42" },
                    { label: "Avg DOM", value: "28" },
                  ].map((stat, i) => (
                    <div 
                      key={i}
                      className="p-3 rounded-lg text-center text-white text-sm"
                      style={{ 
                        background: `linear-gradient(135deg, ${formData.primary_color || "#7C3AED"} 0%, ${formData.accent_color || "#F26B2B"} 100%)` 
                      }}
                    >
                      <div className="text-[10px] opacity-80">{stat.label}</div>
                      <div className="font-bold">{stat.value}</div>
                    </div>
                  ))}
                </div>
              </div>
            </Card>

            {/* Report Footer Preview */}
            {isAffiliate && (
              <Card className="overflow-hidden">
                <div className="p-4 bg-slate-50 dark:bg-zinc-900">
                  <div className="flex items-center justify-between gap-3">
                    <div className="flex items-center gap-3 min-w-0">
                      {formData.rep_photo_url ? (
                        <img
                          src={formData.rep_photo_url}
                          className="w-11 h-11 rounded-full object-cover flex-shrink-0"
                          style={{ border: `2px solid ${formData.primary_color || "#7C3AED"}` }}
                          alt="Representative"
                        />
                      ) : (
                        <div 
                          className="w-11 h-11 rounded-full flex items-center justify-center text-white font-bold text-sm flex-shrink-0"
                          style={{ backgroundColor: formData.primary_color || "#7C3AED" }}
                        >
                          {(formData.rep_name || "Y")[0].toUpperCase()}
                        </div>
                      )}
                      <div className="min-w-0">
                        <div className="text-sm font-semibold text-slate-800 dark:text-slate-200 truncate">
                          {formData.rep_name || "Your Name"}
                          {formData.rep_title && <span className="font-normal text-muted-foreground"> • {formData.rep_title}</span>}
                        </div>
                        <div className="text-xs text-muted-foreground truncate">
                          {formData.rep_phone || "(555) 123-4567"}
                          {(formData.rep_phone && formData.rep_email) && " • "}
                          {formData.rep_email || "email@company.com"}
                        </div>
                        {formData.website_url && (
                          <div className="text-xs truncate" style={{ color: formData.primary_color }}>
                            {formData.website_url.replace("https://", "").replace("http://", "")}
                          </div>
                        )}
                      </div>
                    </div>
                    {formData.logo_url && (
                      <img
                        src={formData.logo_url}
                        className="h-9 w-auto max-w-[80px] object-contain flex-shrink-0"
                        alt={formData.brand_display_name}
                      />
                    )}
                  </div>
                </div>
                <div className="px-4 py-2 border-t text-center text-[10px] text-muted-foreground">
                  Report generated by {formData.brand_display_name || "Your Brand"} • Data source: MLS
                </div>
              </Card>
            )}

            {/* Email Preview */}
            <Card className="overflow-hidden">
              <div className="px-4 py-3 border-b bg-muted/30">
                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                  <Mail className="w-3.5 h-3.5" />
                  Email Header Preview
                </div>
              </div>
              <div
                className="p-4"
                style={{
                  background: `linear-gradient(135deg, ${formData.primary_color || "#7C3AED"} 0%, ${formData.accent_color || "#F26B2B"} 100%)`,
                }}
              >
                <div className="flex items-center gap-3">
                  {formData.logo_url ? (
                    <img
                      src={formData.logo_url}
                      className="h-7 w-auto max-w-[80px] object-contain brightness-0 invert"
                      alt={formData.brand_display_name}
                    />
                  ) : (
                    <div className="h-7 w-7 rounded bg-white/20 flex items-center justify-center text-white font-bold text-sm">
                      {(formData.brand_display_name || "B")[0].toUpperCase()}
                    </div>
                  )}
                  <span className="text-white text-sm font-medium opacity-90">
                    {formData.brand_display_name || "Your Brand"}
                  </span>
                </div>
              </div>
              <div className="p-4 bg-white dark:bg-zinc-900">
                <div className="text-sm font-semibold text-slate-800 dark:text-slate-200">
                  📊 Your Market Snapshot is Ready
                </div>
                <div className="text-xs text-muted-foreground mt-1">
                  Beverly Hills • Last 30 days
                </div>
              </div>
            </Card>

            {/* Quick Actions */}
            <div className="flex gap-2">
              <Button variant="outline" size="sm" className="flex-1 gap-2" disabled>
                <Download className="w-3.5 h-3.5" />
                Sample PDF
              </Button>
              <Button variant="outline" size="sm" className="flex-1 gap-2" disabled>
                <Mail className="w-3.5 h-3.5" />
                Test Email
              </Button>
            </div>
            <p className="text-[10px] text-center text-muted-foreground">
              Save your changes first, then download samples
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
