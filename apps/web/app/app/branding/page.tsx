"use client"

import { useEffect, useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Save, Palette, Mail, FileText, Image, Eye, Download, Loader2 } from "lucide-react"
import { useToast } from "@/components/ui/use-toast"
import { ImageUpload } from "@/components/ui/image-upload"

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

/**
 * Branding Page - Pass B2.2
 * 
 * Tabbed interface with:
 * - Brand Identity: Logo upload, colors, contact info
 * - Preview: Live report template preview (Pass B3)
 * - Download: Sample PDF download (Pass B4)
 */
export default function BrandingPage() {
  const [isAffiliate, setIsAffiliate] = useState(false)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const { toast } = useToast()

  const [formData, setFormData] = useState<BrandingData>({
    brand_display_name: "",
    logo_url: null,
    primary_color: "#7C3AED",
    accent_color: "#F26B2B",
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
          setFormData({
            brand_display_name: data.brand_display_name || "",
            logo_url: data.logo_url || null,
            primary_color: data.primary_color || "#7C3AED",
            accent_color: data.accent_color || "#F26B2B",
            rep_photo_url: data.rep_photo_url || null,
            contact_line1: data.contact_line1 || null,
            contact_line2: data.contact_line2 || null,
            website_url: data.website_url || null,
          })
        } else {
          // Limited branding for agents
          setFormData({
            brand_display_name: data.name || "",
            logo_url: data.logo_url || null,
            primary_color: data.primary_color || "#7C3AED",
            accent_color: data.secondary_color || "#F26B2B",
            rep_photo_url: null,
            contact_line1: null,
            contact_line2: null,
            website_url: null,
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
          <Loader2 className="w-8 h-8 animate-spin text-primary mx-auto mb-4" />
          <p className="text-muted-foreground">Loading branding settings...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">
          {isAffiliate ? "White-Label Branding" : "Branding"}
        </h1>
        <p className="text-muted-foreground mt-1">
          {isAffiliate
            ? "Customize how your brand appears on reports and emails sent to your sponsored agents' clients. TrendyReports stays invisible."
            : "Customize your brand identity for reports"}
        </p>
      </div>

      {/* Info cards for affiliates */}
      {isAffiliate && (
        <div className="grid gap-4 md:grid-cols-3">
          <Card className="bg-gradient-to-br from-violet-50 to-white dark:from-violet-950/20 dark:to-background border-violet-200 dark:border-violet-800">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">PDF Reports</CardTitle>
              <FileText className="h-4 w-4 text-violet-600" />
            </CardHeader>
            <CardContent>
              <div className="text-xs text-muted-foreground">
                Your logo and colors appear on all PDF reports for sponsored agents
              </div>
            </CardContent>
          </Card>

          <Card className="bg-gradient-to-br from-orange-50 to-white dark:from-orange-950/20 dark:to-background border-orange-200 dark:border-orange-800">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Email Delivery</CardTitle>
              <Mail className="h-4 w-4 text-orange-600" />
            </CardHeader>
            <CardContent>
              <div className="text-xs text-muted-foreground">
                Scheduled report emails display your branding and contact info
              </div>
            </CardContent>
          </Card>

          <Card className="bg-gradient-to-br from-emerald-50 to-white dark:from-emerald-950/20 dark:to-background border-emerald-200 dark:border-emerald-800">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">100% White Label</CardTitle>
              <Image className="h-4 w-4 text-emerald-600" />
            </CardHeader>
            <CardContent>
              <div className="text-xs text-muted-foreground">
                TrendyReports branding is completely hidden from your clients
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Main content with tabs */}
      <Tabs defaultValue="identity" className="space-y-6">
        <TabsList className="grid w-full grid-cols-3 max-w-md">
          <TabsTrigger value="identity" className="gap-2">
            <Palette className="w-4 h-4" />
            <span className="hidden sm:inline">Brand</span>
          </TabsTrigger>
          <TabsTrigger value="preview" className="gap-2">
            <Eye className="w-4 h-4" />
            <span className="hidden sm:inline">Preview</span>
          </TabsTrigger>
          <TabsTrigger value="download" className="gap-2">
            <Download className="w-4 h-4" />
            <span className="hidden sm:inline">Export</span>
          </TabsTrigger>
        </TabsList>

        {/* Brand Identity Tab */}
        <TabsContent value="identity" className="space-y-6">
          <div className="grid gap-6 lg:grid-cols-2">
            {/* Form */}
            <div className="space-y-6">
              {/* Logo Upload */}
              <Card>
                <CardHeader>
                  <CardTitle>Logo</CardTitle>
                  <CardDescription>
                    Upload your company logo. It will appear on report headers and emails.
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <ImageUpload
                    label=""
                    value={formData.logo_url}
                    onChange={(url) => setFormData({ ...formData, logo_url: url })}
                    assetType="logo"
                    aspectRatio="wide"
                    helpText="Recommended: 400x150px or similar wide format. PNG with transparency works best."
                  />
                </CardContent>
              </Card>

              {/* Brand Name & Colors */}
              <Card>
                <CardHeader>
                  <CardTitle>Brand Identity</CardTitle>
                  <CardDescription>
                    Set your brand name and colors for reports
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
                    <p className="text-xs text-muted-foreground">
                      This name appears in report headers and footers
                    </p>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="primary">Primary Color</Label>
                      <div className="flex gap-2">
                        <Input
                          id="primary"
                          type="color"
                          value={formData.primary_color || "#7C3AED"}
                          onChange={(e) =>
                            setFormData({ ...formData, primary_color: e.target.value })
                          }
                          className="w-14 h-10 p-1 cursor-pointer"
                        />
                        <Input
                          type="text"
                          value={formData.primary_color || "#7C3AED"}
                          onChange={(e) =>
                            setFormData({ ...formData, primary_color: e.target.value })
                          }
                          className="flex-1 font-mono text-sm"
                          placeholder="#7C3AED"
                        />
                      </div>
                      <p className="text-xs text-muted-foreground">Headers & ribbons</p>
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="accent">Accent Color</Label>
                      <div className="flex gap-2">
                        <Input
                          id="accent"
                          type="color"
                          value={formData.accent_color || "#F26B2B"}
                          onChange={(e) =>
                            setFormData({ ...formData, accent_color: e.target.value })
                          }
                          className="w-14 h-10 p-1 cursor-pointer"
                        />
                        <Input
                          type="text"
                          value={formData.accent_color || "#F26B2B"}
                          onChange={(e) =>
                            setFormData({ ...formData, accent_color: e.target.value })
                          }
                          className="flex-1 font-mono text-sm"
                          placeholder="#F26B2B"
                        />
                      </div>
                      <p className="text-xs text-muted-foreground">Buttons & highlights</p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Affiliate-only: Contact Info & Headshot */}
              {isAffiliate && (
                <>
                  <Card>
                    <CardHeader>
                      <CardTitle>Representative Photo</CardTitle>
                      <CardDescription>
                        Optional headshot for personalized emails
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      <ImageUpload
                        label=""
                        value={formData.rep_photo_url}
                        onChange={(url) => setFormData({ ...formData, rep_photo_url: url })}
                        assetType="headshot"
                        aspectRatio="square"
                        helpText="Square format recommended (e.g., 400x400px)"
                      />
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader>
                      <CardTitle>Contact Information</CardTitle>
                      <CardDescription>
                        Displayed in report footers and emails
                      </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <div className="space-y-2">
                        <Label htmlFor="contact1">Contact Line 1</Label>
                        <Input
                          id="contact1"
                          value={formData.contact_line1 || ""}
                          onChange={(e) =>
                            setFormData({ ...formData, contact_line1: e.target.value })
                          }
                          placeholder="John Doe • Senior Title Rep"
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
                          placeholder="(555) 123-4567 • john@company.com"
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
                          placeholder="https://www.yourcompany.com"
                        />
                      </div>
                    </CardContent>
                  </Card>
                </>
              )}

              {/* Save Button */}
              <Button onClick={save} disabled={saving} className="w-full gap-2" size="lg">
                {saving ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Save className="w-4 h-4" />
                )}
                {saving ? "Saving..." : "Save Changes"}
              </Button>
            </div>

            {/* Live Previews */}
            <div className="space-y-6">
              {/* Email Preview */}
              <Card>
                <CardHeader>
                  <CardTitle>Email Header Preview</CardTitle>
                  <CardDescription>How your brand appears in email headers</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="border rounded-lg p-4 bg-white dark:bg-zinc-900">
                    <div className="flex items-center gap-4">
                      {formData.logo_url ? (
                        <img
                          src={formData.logo_url}
                          className="h-10 w-auto max-w-[140px] object-contain"
                          alt={formData.brand_display_name}
                        />
                      ) : (
                        <div
                          className="h-10 w-10 rounded-lg flex items-center justify-center text-white font-bold text-lg"
                          style={{ backgroundColor: formData.primary_color || "#7C3AED" }}
                        >
                          {(formData.brand_display_name || "B")[0].toUpperCase()}
                        </div>
                      )}
                      <div>
                        <div
                          className="font-semibold"
                          style={{ color: formData.primary_color || "#111827" }}
                        >
                          {formData.brand_display_name || "Your Brand Name"}
                        </div>
                        <div className="text-xs text-slate-500">
                          {formData.contact_line1 || formData.contact_line2
                            ? `${formData.contact_line1 || ""} ${formData.contact_line2 ? "• " + formData.contact_line2 : ""}`
                            : "Contact info appears here"}
                        </div>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* PDF Header Preview */}
              <Card>
                <CardHeader>
                  <CardTitle>Report Header Preview</CardTitle>
                  <CardDescription>How your brand appears on PDF reports</CardDescription>
                </CardHeader>
                <CardContent>
                  <div
                    className="border rounded-lg overflow-hidden"
                    style={{
                      background: `linear-gradient(135deg, ${formData.primary_color || "#7C3AED"} 0%, ${formData.accent_color || "#F26B2B"} 100%)`,
                    }}
                  >
                    <div className="p-6 text-white">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-4">
                          {formData.logo_url ? (
                            <img
                              src={formData.logo_url}
                              className="h-12 w-auto max-w-[160px] object-contain brightness-0 invert"
                              alt={formData.brand_display_name}
                            />
                          ) : (
                            <div className="h-12 w-12 rounded-xl bg-white/20 flex items-center justify-center text-2xl font-bold">
                              {(formData.brand_display_name || "B")[0].toUpperCase()}
                            </div>
                          )}
                          <div>
                            <div className="text-xl font-bold">Market Snapshot</div>
                            <div className="text-sm opacity-80">Beverly Hills, CA</div>
                          </div>
                        </div>
                        <div className="text-right text-sm opacity-80">
                          <div>{formData.brand_display_name || "Your Brand"} Insights</div>
                          <div>November 2025</div>
                        </div>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Footer Preview */}
              <Card>
                <CardHeader>
                  <CardTitle>Report Footer Preview</CardTitle>
                  <CardDescription>Bottom of each report page</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="border rounded-lg p-4 bg-slate-50 dark:bg-zinc-900">
                    <div className="flex items-center justify-between text-xs text-slate-600 dark:text-slate-400">
                      <div className="flex items-center gap-2">
                        {formData.rep_photo_url && (
                          <img
                            src={formData.rep_photo_url}
                            className="w-8 h-8 rounded-full object-cover"
                            alt="Representative"
                          />
                        )}
                        <div>
                          {formData.contact_line1 && <div>{formData.contact_line1}</div>}
                          {formData.contact_line2 && <div>{formData.contact_line2}</div>}
                          {!formData.contact_line1 && !formData.contact_line2 && (
                            <div className="italic">Contact info appears here</div>
                          )}
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="font-medium" style={{ color: formData.primary_color }}>
                          {formData.brand_display_name || "Your Brand"}
                        </div>
                        {formData.website_url && (
                          <div className="text-slate-400">{formData.website_url}</div>
                        )}
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        </TabsContent>

        {/* Preview Tab - Pass B3 */}
        <TabsContent value="preview">
          <Card>
            <CardHeader>
              <CardTitle>Live Report Preview</CardTitle>
              <CardDescription>
                See exactly how your branding appears on different report types
              </CardDescription>
            </CardHeader>
            <CardContent className="min-h-[400px] flex items-center justify-center">
              <div className="text-center text-muted-foreground">
                <Eye className="w-12 h-12 mx-auto mb-4 opacity-50" />
                <p className="text-lg font-medium">Coming Soon</p>
                <p className="text-sm mt-2">
                  Live preview of all 8 report types with your branding
                </p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Download Tab - Pass B4 */}
        <TabsContent value="download">
          <Card>
            <CardHeader>
              <CardTitle>Download & Test</CardTitle>
              <CardDescription>
                Download sample reports and send test emails with your branding
              </CardDescription>
            </CardHeader>
            <CardContent className="min-h-[400px] flex items-center justify-center">
              <div className="text-center text-muted-foreground">
                <Download className="w-12 h-12 mx-auto mb-4 opacity-50" />
                <p className="text-lg font-medium">Coming Soon</p>
                <p className="text-sm mt-2">
                  Download sample PDFs and send test emails to yourself
                </p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
