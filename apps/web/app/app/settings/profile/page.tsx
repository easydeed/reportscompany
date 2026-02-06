"use client"

import { useEffect, useState, useCallback } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Badge } from "@/components/ui/badge"
import {
  Mail,
  Save,
  Loader2,
  CheckCircle2,
  X,
  Camera,
} from "lucide-react"
import { useToast } from "@/components/ui/use-toast"
import { ImageUpload } from "@/components/ui/image-upload"

type UserProfile = {
  id: string
  email: string
  first_name: string | null
  last_name: string | null
  job_title: string | null
  company_name: string | null
  phone: string | null
  website: string | null
  avatar_url: string | null
  email_verified: boolean
}

type ProfileFormData = {
  first_name: string
  last_name: string
  job_title: string
  company_name: string
  phone: string
  website: string
  avatar_url: string | null
}

function formatPhoneNumber(value: string): string {
  const digits = value.replace(/\D/g, "")
  if (digits.length === 0) return ""
  if (digits.length <= 3) return `(${digits}`
  if (digits.length <= 6) return `(${digits.slice(0, 3)}) ${digits.slice(3)}`
  return `(${digits.slice(0, 3)}) ${digits.slice(3, 6)}-${digits.slice(6, 10)}`
}

export default function ProfilePage() {
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const { toast } = useToast()

  const [profile, setProfile] = useState<UserProfile | null>(null)
  const [formData, setFormData] = useState<ProfileFormData>({
    first_name: "",
    last_name: "",
    job_title: "",
    company_name: "",
    phone: "",
    website: "",
    avatar_url: null,
  })

  const handlePhoneChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const formatted = formatPhoneNumber(e.target.value)
    setFormData((prev) => ({ ...prev, phone: formatted }))
  }, [])

  useEffect(() => {
    loadProfile()
  }, [])

  async function loadProfile() {
    setLoading(true)
    try {
      const res = await fetch("/api/proxy/v1/users/me", {
        cache: "no-store",
        credentials: "include",
      })

      if (res.ok) {
        const data: UserProfile = await res.json()
        setProfile(data)
        setFormData({
          first_name: data.first_name || "",
          last_name: data.last_name || "",
          job_title: data.job_title || "",
          company_name: data.company_name || "",
          phone: data.phone ? formatPhoneNumber(data.phone) : "",
          website: data.website || "",
          avatar_url: data.avatar_url,
        })
      }
    } catch (error) {
      console.error("Failed to load profile:", error)
      toast({
        title: "Error",
        description: "Failed to load profile",
        variant: "destructive",
      })
    } finally {
      setLoading(false)
    }
  }

  async function saveProfile() {
    setSaving(true)
    try {
      const cleanPhone = formData.phone.replace(/\D/g, "")

      const res = await fetch("/api/proxy/v1/users/me", {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          first_name: formData.first_name || null,
          last_name: formData.last_name || null,
          job_title: formData.job_title || null,
          company_name: formData.company_name || null,
          phone: cleanPhone || null,
          website: formData.website || null,
          avatar_url: formData.avatar_url,
        }),
      })

      if (!res.ok) {
        const error = await res.json()
        throw new Error(error.detail || "Failed to save profile")
      }

      const data = await res.json()
      setProfile(data)

      toast({
        title: "Profile Updated",
        description: "Your profile has been saved successfully.",
      })
    } catch (error) {
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to save profile",
        variant: "destructive",
      })
    } finally {
      setSaving(false)
    }
  }

  function getInitials(): string {
    if (formData.first_name && formData.last_name) {
      return `${formData.first_name[0]}${formData.last_name[0]}`.toUpperCase()
    }
    if (formData.first_name) return formData.first_name[0].toUpperCase()
    if (profile?.email) return profile.email[0].toUpperCase()
    return "U"
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-24">
        <div className="text-center">
          <Loader2 className="w-8 h-8 animate-spin text-indigo-600 mx-auto mb-4" />
          <p className="text-muted-foreground text-sm">Loading profile...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-3xl">
      {/* Page Header */}
      <div className="mb-6">
        <h1 className="text-xl font-semibold tracking-tight text-foreground">Profile</h1>
        <p className="text-[13px] text-muted-foreground mt-0.5">
          Your personal information appears on reports and emails.
        </p>
      </div>

      {/* Main Card */}
      <div className="bg-card border border-border rounded-xl shadow-[var(--shadow-card)] overflow-hidden">
        {/* Avatar Section */}
        <div className="p-6 border-b border-border">
          <div className="flex items-center gap-5">
            <div className="relative group">
              <Avatar className="w-20 h-20 border-2 border-border shadow-sm">
                <AvatarImage src={formData.avatar_url || undefined} />
                <AvatarFallback className="text-xl font-semibold bg-gradient-to-br from-indigo-500 to-indigo-600 text-white">
                  {getInitials()}
                </AvatarFallback>
              </Avatar>
              <div className="absolute inset-0 rounded-full bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                <Camera className="w-5 h-5 text-white" />
              </div>
            </div>
            
            <div className="flex-1">
              <h3 className="font-medium text-foreground">Profile Photo</h3>
              <p className="text-xs text-muted-foreground mt-0.5 mb-3">
                Recommended: Square image, at least 400×400px
              </p>
              <div className="flex items-center gap-2">
                <ImageUpload
                  label="Upload"
                  value={formData.avatar_url}
                  onChange={(url) => setFormData({ ...formData, avatar_url: url })}
                  assetType="headshot"
                  aspectRatio="square"
                  helpText=""
                  className="w-auto"
                />
                {formData.avatar_url && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setFormData({ ...formData, avatar_url: null })}
                    className="text-muted-foreground hover:text-destructive"
                  >
                    <X className="w-4 h-4" />
                  </Button>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Form Sections */}
        <div className="divide-y divide-border">
          {/* Personal Information */}
          <div className="p-6">
            <h3 className="text-[13px] font-semibold text-foreground uppercase tracking-wide mb-4">
              Personal Information
            </h3>
            <div className="grid gap-4">
              <div className="grid sm:grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <Label htmlFor="first_name" className="text-xs font-medium text-muted-foreground">
                    First Name
                  </Label>
                  <Input
                    id="first_name"
                    value={formData.first_name}
                    onChange={(e) => setFormData({ ...formData, first_name: e.target.value })}
                    placeholder="Jerry"
                    className="h-9"
                  />
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="last_name" className="text-xs font-medium text-muted-foreground">
                    Last Name
                  </Label>
                  <Input
                    id="last_name"
                    value={formData.last_name}
                    onChange={(e) => setFormData({ ...formData, last_name: e.target.value })}
                    placeholder="Mendoza"
                    className="h-9"
                  />
                </div>
              </div>

              <div className="grid sm:grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <Label htmlFor="job_title" className="text-xs font-medium text-muted-foreground">
                    Job Title
                  </Label>
                  <Input
                    id="job_title"
                    value={formData.job_title}
                    onChange={(e) => setFormData({ ...formData, job_title: e.target.value })}
                    placeholder="Real Estate Agent"
                    className="h-9"
                  />
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="company_name" className="text-xs font-medium text-muted-foreground">
                    Company
                  </Label>
                  <Input
                    id="company_name"
                    value={formData.company_name}
                    onChange={(e) => setFormData({ ...formData, company_name: e.target.value })}
                    placeholder="Century 21 Masters"
                    className="h-9"
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Contact Information */}
          <div className="p-6">
            <h3 className="text-[13px] font-semibold text-foreground uppercase tracking-wide mb-4">
              Contact Information
            </h3>
            <div className="grid gap-4">
              {/* Email (read-only) */}
              <div className="space-y-1.5">
                <Label className="text-xs font-medium text-muted-foreground">Email Address</Label>
                <div className="flex items-center gap-3 px-3 py-2 h-9 bg-muted/50 rounded-md border border-border">
                  <Mail className="w-4 h-4 text-muted-foreground flex-shrink-0" />
                  <span className="text-sm text-foreground flex-1 truncate">{profile?.email}</span>
                  {profile?.email_verified && (
                    <Badge variant="secondary" className="text-emerald-600 bg-emerald-50 border-emerald-200 text-[10px] px-1.5 py-0">
                      <CheckCircle2 className="w-3 h-3 mr-0.5" />
                      Verified
                    </Badge>
                  )}
                </div>
                <p className="text-[11px] text-muted-foreground">
                  Change your email in{" "}
                  <a href="/app/settings/security" className="text-indigo-600 hover:underline">
                    Security settings
                  </a>
                </p>
              </div>

              <div className="grid sm:grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <Label htmlFor="phone" className="text-xs font-medium text-muted-foreground">
                    Phone Number
                  </Label>
                  <Input
                    id="phone"
                    type="tel"
                    value={formData.phone}
                    onChange={handlePhoneChange}
                    placeholder="(626) 555-1234"
                    maxLength={14}
                    className="h-9"
                  />
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="website" className="text-xs font-medium text-muted-foreground">
                    Website
                  </Label>
                  <Input
                    id="website"
                    type="url"
                    value={formData.website}
                    onChange={(e) => setFormData({ ...formData, website: e.target.value })}
                    placeholder="https://jerry.century21masters.com"
                    className="h-9"
                  />
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 bg-muted/30 border-t border-border flex justify-end">
          <Button onClick={saveProfile} disabled={saving} size="sm">
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
      </div>
    </div>
  )
}
