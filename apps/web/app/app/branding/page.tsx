"use client"

import { useEffect, useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Save, Palette, Mail, FileText, Image } from "lucide-react"
import { useToast } from "@/components/ui/use-toast"

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

export default function BrandingPage() {
  const [isAffiliate, setIsAffiliate] = useState(false)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const { toast } = useToast()

  const [formData, setFormData] = useState<BrandingData>({
    brand_display_name: "",
    logo_url: null,
    primary_color: "#6366f1",
    accent_color: "#f59e0b",
    rep_photo_url: null,
    contact_line1: null,
    contact_line2: null,
    website_url: null,
  })

  useEffect(() => {
    loadData()
  }, [])

  async function loadData() {
    setLoading(true)
    try {
      // Check if user is affiliate
      const meRes = await fetch("/api/proxy/v1/me", { cache: "no-store" })
      const me = meRes.ok ? await meRes.json() : {}
      const isAff = me.account_type === "INDUSTRY_AFFILIATE"
      setIsAffiliate(isAff)

      // Load branding data
      const endpoint = isAff ? "/api/proxy/v1/affiliate/branding" : "/api/proxy/v1/account"
      const res = await fetch(endpoint, { cache: "no-store" })
      
      if (res.ok) {
        const data = await res.json()
        if (isAff) {
          // Full branding for affiliates
          setFormData(data)
        } else {
          // Limited branding for agents
          setFormData({
            brand_display_name: data.name || "",
            logo_url: data.logo_url || null,
            primary_color: data.primary_color || "#6366f1",
            accent_color: data.secondary_color || "#f59e0b",
            rep_photo_url: null,
            contact_line1: null,
            contact_line2: null,
            website_url: null,
          })
        }
      }
    } catch (error) {
      console.error("Failed to load branding:", error)
    } finally {
      setLoading(false)
    }
  }

  async function save() {
    setSaving(true)
    try {
      const endpoint = isAffiliate ? "/api/proxy/v1/affiliate/branding" : "/api/proxy/v1/account/branding"
      
      const body = isAffiliate
        ? formData
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

      if (!res.ok) {
        throw new Error("Failed to save branding")
      }

      toast({
        title: "Success",
        description: "Branding updated successfully",
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
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4" />
          <p className="text-muted-foreground">Loading branding...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">
          {isAffiliate ? "Affiliate Branding" : "Branding"}
        </h1>
        <p className="text-muted-foreground mt-1">
          {isAffiliate
            ? "These settings control how your brand appears on every email and PDF report generated for your sponsored agents. Your logo, colors, and contact info will be visible to their clients; TrendyReports stays invisible."
            : "Customize your brand identity for reports"}
        </p>
      </div>

      {isAffiliate && (
        <div className="grid gap-4 md:grid-cols-3">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Reports</CardTitle>
              <FileText className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-xs text-muted-foreground">
                Your brand appears on all PDF reports for your sponsored agents
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Emails</CardTitle>
              <Mail className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-xs text-muted-foreground">
                Scheduled report emails sent to clients display your branding
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">White Label</CardTitle>
              <Image className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-xs text-muted-foreground">
                TrendyReports remains invisible to your clients
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Form */}
        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Palette className="w-5 h-5" />
                Brand Settings
              </CardTitle>
              <CardDescription>
                {isAffiliate
                  ? "Configure your white-label branding"
                  : "Update your logo and color scheme"}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="brand_name">Brand Display Name</Label>
                <Input
                  id="brand_name"
                  value={formData.brand_display_name}
                  onChange={(e) =>
                    setFormData({ ...formData, brand_display_name: e.target.value })
                  }
                  placeholder="Your Company Name"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="logo">Logo URL</Label>
                <Input
                  id="logo"
                  value={formData.logo_url || ""}
                  onChange={(e) => setFormData({ ...formData, logo_url: e.target.value })}
                  placeholder="https://..."
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="primary">Primary Color</Label>
                  <div className="flex gap-2">
                    <Input
                      id="primary"
                      type="color"
                      value={formData.primary_color || "#6366f1"}
                      onChange={(e) =>
                        setFormData({ ...formData, primary_color: e.target.value })
                      }
                      className="w-16 h-10 p-1"
                    />
                    <Input
                      type="text"
                      value={formData.primary_color || "#6366f1"}
                      onChange={(e) =>
                        setFormData({ ...formData, primary_color: e.target.value })
                      }
                      className="flex-1"
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="accent">Accent Color</Label>
                  <div className="flex gap-2">
                    <Input
                      id="accent"
                      type="color"
                      value={formData.accent_color || "#f59e0b"}
                      onChange={(e) =>
                        setFormData({ ...formData, accent_color: e.target.value })
                      }
                      className="w-16 h-10 p-1"
                    />
                    <Input
                      type="text"
                      value={formData.accent_color || "#f59e0b"}
                      onChange={(e) =>
                        setFormData({ ...formData, accent_color: e.target.value })
                      }
                      className="flex-1"
                    />
                  </div>
                </div>
              </div>

              {isAffiliate && (
                <>
                  <div className="space-y-2">
                    <Label htmlFor="contact1">Contact Line 1</Label>
                    <Input
                      id="contact1"
                      value={formData.contact_line1 || ""}
                      onChange={(e) =>
                        setFormData({ ...formData, contact_line1: e.target.value })
                      }
                      placeholder="(555) 123-4567"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="contact2">Contact Line 2</Label>
                    <Input
                      id="contact2"
                      value={formData.contact_line2 || ""}
                      onChange={(e) =>
                        setFormData({ ...formData, contact_line2: e.target.value })
                      }
                      placeholder="info@company.com"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="website">Website URL</Label>
                    <Input
                      id="website"
                      value={formData.website_url || ""}
                      onChange={(e) =>
                        setFormData({ ...formData, website_url: e.target.value })
                      }
                      placeholder="https://www.company.com"
                    />
                  </div>
                </>
              )}

              <Button onClick={save} disabled={saving} className="w-full gap-2">
                <Save className="w-4 h-4" />
                {saving ? "Saving..." : "Save Changes"}
              </Button>
            </CardContent>
          </Card>
        </div>

        {/* Live Previews */}
        <div className="space-y-4">
          {/* Email Preview */}
          <Card>
            <CardHeader>
              <CardTitle>Email Preview</CardTitle>
              <CardDescription>Example of your email header</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="border rounded-md p-4 bg-white">
                <div className="flex items-center gap-3">
                  {formData.logo_url && (
                    <img
                      src={formData.logo_url}
                      className="h-8 w-auto max-w-[120px] object-contain"
                      alt={formData.brand_display_name}
                    />
                  )}
                  <div>
                    <div
                      className="text-sm font-semibold"
                      style={{ color: formData.primary_color || "#111827" }}
                    >
                      {formData.brand_display_name || "Your Brand Name"}
                    </div>
                    <div className="text-xs text-slate-500">
                      {formData.contact_line1 || formData.contact_line2
                        ? `${formData.contact_line1 || ""} ${formData.contact_line2 ? "• " + formData.contact_line2 : ""}`
                        : "Contact info will appear here"}
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* PDF Cover Preview */}
          <Card>
            <CardHeader>
              <CardTitle>PDF Cover Preview</CardTitle>
              <CardDescription>Example of a report cover</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="border rounded-md p-6 bg-gradient-to-br from-slate-50 to-slate-100">
                {formData.logo_url && (
                  <img
                    src={formData.logo_url}
                    className="h-10 w-auto max-w-[160px] object-contain mb-4"
                    alt={formData.brand_display_name}
                  />
                )}
                <div className="text-xs text-slate-500 mb-2">Market Snapshot Report</div>
                <div
                  className="text-xl font-semibold mb-2"
                  style={{ color: formData.primary_color || "#111827" }}
                >
                  {formData.brand_display_name || "Your Brand Name"}
                </div>
                <div className="text-xs text-slate-600 space-y-1">
                  {formData.contact_line1 && <div>{formData.contact_line1}</div>}
                  {formData.contact_line2 && <div>{formData.contact_line2}</div>}
                  {formData.website_url && <div>{formData.website_url}</div>}
                  {!formData.contact_line1 &&
                    !formData.contact_line2 &&
                    !formData.website_url && <div>Contact info will appear here</div>}
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
