"use client"

import { useEffect, useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { API_BASE, DEMO_ACC } from "@/lib/api"
import { Save, Palette } from "lucide-react"

type Account = {
  id: string
  name: string
  slug: string
  logo_url?: string
  primary_color?: string
  secondary_color?: string
}

export default function BrandingPage() {
  const [acct, setAcct] = useState<Account | null>(null)
  const [logoUrl, setLogoUrl] = useState("")
  const [primary, setPrimary] = useState("#2563EB")
  const [secondary, setSecondary] = useState("#F26B2B")
  const [saving, setSaving] = useState(false)
  const [msg, setMsg] = useState<string | null>(null)

  async function load() {
    const res = await fetch(`${API_BASE}/v1/account`, { headers: { "X-Demo-Account": DEMO_ACC } })
    const j = await res.json()
    setAcct(j)
    setLogoUrl(j.logo_url || "")
    setPrimary(j.primary_color || primary)
    setSecondary(j.secondary_color || secondary)
  }

  useEffect(() => {
    load()
    // eslint-disable-next-line
  }, [])

  async function save() {
    setSaving(true)
    setMsg(null)
    const res = await fetch(`${API_BASE}/v1/account/branding`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json", "X-Demo-Account": DEMO_ACC },
      body: JSON.stringify({ logo_url: logoUrl || null, primary_color: primary, secondary_color: secondary }),
    })
    if (!res.ok) {
      const t = await res.text()
      setMsg(`Save failed: ${t}`)
      setSaving(false)
      return
    }
    const j = await res.json()
    setAcct(j)
    setSaving(false)
    setMsg("Saved successfully!")
    setTimeout(() => setMsg(null), 3000)
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-bold text-3xl mb-2">Branding</h1>
        <p className="text-muted-foreground">Customize your brand identity for reports</p>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Palette className="w-5 h-5" />
                Brand Settings
              </CardTitle>
              <CardDescription>Update your logo and color scheme</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="logo">Logo URL</Label>
                <Input
                  id="logo"
                  value={logoUrl}
                  onChange={(e) => setLogoUrl(e.target.value)}
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
                      value={primary}
                      onChange={(e) => setPrimary(e.target.value)}
                      className="w-16 h-10 p-1"
                    />
                    <Input
                      type="text"
                      value={primary}
                      onChange={(e) => setPrimary(e.target.value)}
                      className="flex-1"
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="secondary">Secondary Color</Label>
                  <div className="flex gap-2">
                    <Input
                      id="secondary"
                      type="color"
                      value={secondary}
                      onChange={(e) => setSecondary(e.target.value)}
                      className="w-16 h-10 p-1"
                    />
                    <Input
                      type="text"
                      value={secondary}
                      onChange={(e) => setSecondary(e.target.value)}
                      className="flex-1"
                    />
                  </div>
                </div>
              </div>

              <Button onClick={save} disabled={saving} className="w-full gap-2">
                <Save className="w-4 h-4" />
                {saving ? "Saving..." : "Save Changes"}
              </Button>

              {msg && (
                <p className={`text-sm ${msg.includes("failed") ? "text-destructive" : "text-green-600"}`}>{msg}</p>
              )}
            </CardContent>
          </Card>
        </div>

        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Preview</CardTitle>
              <CardDescription>See how your branding will appear</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-3">
                <p className="text-sm font-medium text-muted-foreground">Logo</p>
                <div className="flex items-center gap-4">
                  <div
                    className="h-20 w-20 rounded-lg border border-border bg-muted flex items-center justify-center"
                    style={{
                      backgroundImage: logoUrl ? `url(${logoUrl})` : "none",
                      backgroundSize: "contain",
                      backgroundRepeat: "no-repeat",
                      backgroundPosition: "center",
                    }}
                  >
                    {!logoUrl && <span className="text-xs text-muted-foreground">No logo</span>}
                  </div>
                </div>
              </div>

              <div className="space-y-3">
                <p className="text-sm font-medium text-muted-foreground">Color Palette</p>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <div className="h-24 rounded-lg border border-border" style={{ background: primary }} />
                    <p className="text-xs font-mono text-center">{primary}</p>
                    <p className="text-xs text-muted-foreground text-center">Primary</p>
                  </div>
                  <div className="space-y-2">
                    <div className="h-24 rounded-lg border border-border" style={{ background: secondary }} />
                    <p className="text-xs font-mono text-center">{secondary}</p>
                    <p className="text-xs text-muted-foreground text-center">Secondary</p>
                  </div>
                </div>
              </div>

              <div className="space-y-3">
                <p className="text-sm font-medium text-muted-foreground">Sample Button</p>
                <Button className="w-full" style={{ backgroundColor: primary }}>
                  Primary Action
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
