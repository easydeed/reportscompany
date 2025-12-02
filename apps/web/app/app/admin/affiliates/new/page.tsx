"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { ImageUpload } from "@/components/ui/image-upload"
import { ArrowLeft, Building2, Loader2, CheckCircle, Copy } from "lucide-react"

export default function NewAffiliatePage() {
  const router = useRouter()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<{
    name: string
    email: string
    inviteUrl: string
    accountId: string
  } | null>(null)
  const [copied, setCopied] = useState(false)
  const [logoUrl, setLogoUrl] = useState<string | null>(null)
  const [primaryColor, setPrimaryColor] = useState("#7C3AED")
  const [accentColor, setAccentColor] = useState("#F26B2B")

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    setLoading(true)
    setError(null)

    const formData = new FormData(e.currentTarget)

    const body = {
      company_name: formData.get("company_name") as string,
      admin_email: formData.get("admin_email") as string,
      admin_first_name: formData.get("admin_first_name") as string || undefined,
      admin_last_name: formData.get("admin_last_name") as string || undefined,
      logo_url: logoUrl || undefined,
      primary_color: primaryColor || undefined,
      accent_color: accentColor || undefined,
      website_url: formData.get("website_url") as string || undefined,
    }

    try {
      const res = await fetch("/api/proxy/v1/admin/affiliates", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      })

      const data = await res.json()

      if (!res.ok) {
        throw new Error(data.detail || "Failed to create affiliate")
      }

      setSuccess({
        name: body.company_name,
        email: body.admin_email,
        inviteUrl: data.invite_url,
        accountId: data.account_id,
      })
    } catch (err: any) {
      setError(err.message || "Failed to create affiliate")
    } finally {
      setLoading(false)
    }
  }

  function copyToClipboard() {
    if (success?.inviteUrl) {
      navigator.clipboard.writeText(success.inviteUrl)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }

  if (success) {
    return (
      <div>
        <div className="flex items-center gap-4 mb-6">
          <Link href="/app/admin/affiliates">
            <Button variant="ghost" size="icon">
              <ArrowLeft className="h-4 w-4" />
            </Button>
          </Link>
          <div>
            <h1 className="text-3xl font-display font-bold text-foreground">Affiliate Created</h1>
          </div>
        </div>

        <Card className="max-w-2xl">
          <CardContent className="pt-6">
            <div className="text-center mb-6">
              <div className="w-16 h-16 rounded-full bg-green-100 flex items-center justify-center mx-auto mb-4">
                <CheckCircle className="h-8 w-8 text-green-600" />
              </div>
              <h2 className="text-xl font-semibold mb-2">{success.name} has been created!</h2>
              <p className="text-muted-foreground">
                An invitation email has been sent to {success.email}
              </p>
            </div>

            <div className="space-y-4">
              <div>
                <Label className="text-muted-foreground">Invite URL</Label>
                <div className="flex items-center gap-2 mt-1">
                  <Input value={success.inviteUrl} readOnly className="text-sm" />
                  <Button variant="outline" size="icon" onClick={copyToClipboard}>
                    {copied ? (
                      <CheckCircle className="h-4 w-4 text-green-600" />
                    ) : (
                      <Copy className="h-4 w-4" />
                    )}
                  </Button>
                </div>
                <p className="text-sm text-muted-foreground mt-1">
                  Share this link if the email doesn&apos;t arrive
                </p>
              </div>

              <div className="flex gap-3 pt-4">
                <Link href={`/app/admin/affiliates/${success.accountId}`}>
                  <Button>View Affiliate</Button>
                </Link>
                <Link href="/app/admin/affiliates/new">
                  <Button variant="outline" onClick={() => setSuccess(null)}>
                    Add Another
                  </Button>
                </Link>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div>
      <div className="flex items-center gap-4 mb-6">
        <Link href="/app/admin/affiliates">
          <Button variant="ghost" size="icon">
            <ArrowLeft className="h-4 w-4" />
          </Button>
        </Link>
        <div>
          <h1 className="text-3xl font-display font-bold text-foreground">Add Title Company</h1>
          <p className="text-muted-foreground mt-1">Create a new affiliate account</p>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6 max-w-2xl">
        {/* Company Info */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Building2 className="h-5 w-5" />
              Company Information
            </CardTitle>
            <CardDescription>Basic details about the title company</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label htmlFor="company_name">Company Name *</Label>
              <Input
                id="company_name"
                name="company_name"
                placeholder="Pacific Coast Title"
                required
                disabled={loading}
              />
            </div>
            <div>
              <Label htmlFor="website_url">Website URL</Label>
              <Input
                id="website_url"
                name="website_url"
                type="url"
                placeholder="https://example.com"
                disabled={loading}
              />
            </div>
          </CardContent>
        </Card>

        {/* Admin User */}
        <Card>
          <CardHeader>
            <CardTitle>Admin Contact</CardTitle>
            <CardDescription>The person who will manage this affiliate account</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label htmlFor="admin_email">Email Address *</Label>
              <Input
                id="admin_email"
                name="admin_email"
                type="email"
                placeholder="admin@example.com"
                required
                disabled={loading}
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="admin_first_name">First Name</Label>
                <Input
                  id="admin_first_name"
                  name="admin_first_name"
                  placeholder="John"
                  disabled={loading}
                />
              </div>
              <div>
                <Label htmlFor="admin_last_name">Last Name</Label>
                <Input
                  id="admin_last_name"
                  name="admin_last_name"
                  placeholder="Doe"
                  disabled={loading}
                />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Branding */}
        <Card>
          <CardHeader>
            <CardTitle>Branding (Optional)</CardTitle>
            <CardDescription>White-label branding for reports</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <ImageUpload
              label="Company Logo"
              value={logoUrl}
              onChange={setLogoUrl}
              assetType="logo"
              aspectRatio="wide"
              helpText="PNG or SVG with transparent background recommended"
            />
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="primary_color">Primary Color</Label>
                <div className="flex gap-2">
                  <Input
                    id="primary_color"
                    value={primaryColor}
                    onChange={(e) => setPrimaryColor(e.target.value)}
                    placeholder="#7C3AED"
                    disabled={loading}
                    className="flex-1"
                  />
                  <input
                    type="color"
                    value={primaryColor}
                    onChange={(e) => setPrimaryColor(e.target.value)}
                    className="w-10 h-10 rounded border cursor-pointer"
                    disabled={loading}
                  />
                </div>
              </div>
              <div>
                <Label htmlFor="accent_color">Accent Color</Label>
                <div className="flex gap-2">
                  <Input
                    id="accent_color"
                    value={accentColor}
                    onChange={(e) => setAccentColor(e.target.value)}
                    placeholder="#F26B2B"
                    disabled={loading}
                    className="flex-1"
                  />
                  <input
                    type="color"
                    value={accentColor}
                    onChange={(e) => setAccentColor(e.target.value)}
                    className="w-10 h-10 rounded border cursor-pointer"
                    disabled={loading}
                  />
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {error && (
          <Alert variant="destructive">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        <div className="flex gap-3">
          <Button type="submit" disabled={loading}>
            {loading && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
            Create Affiliate
          </Button>
          <Link href="/app/admin/affiliates">
            <Button type="button" variant="outline" disabled={loading}>
              Cancel
            </Button>
          </Link>
        </div>
      </form>
    </div>
  )
}
