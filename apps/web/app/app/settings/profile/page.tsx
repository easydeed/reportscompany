"use client"

import { useEffect, useState, useCallback } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Badge } from "@/components/ui/badge"
import {
  User,
  Building,
  Phone,
  Globe,
  Mail,
  Briefcase,
  Save,
  Loader2,
  CheckCircle2,
  Upload,
  X,
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
          <p className="text-muted-foreground">Loading profile...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-8 max-w-2xl">
      {/* Section Header */}
      <div>
        <h2 className="text-lg font-semibold">Profile</h2>
        <p className="text-sm text-muted-foreground mt-1">
          Your personal information. This appears on your reports and emails.
        </p>
      </div>

      {/* Photo Section */}
      <div className="bg-card border border-border rounded-xl overflow-hidden shadow-[var(--shadow-card)]">
        <div className="px-5 py-3.5 border-b border-border bg-muted/20">
          <h3 className="text-[13px] font-semibold text-foreground">Photo</h3>
        </div>
        <div className="p-5">
          <div className="flex items-start gap-6">
            <Avatar className="w-24 h-24 border-4 border-background shadow-lg">
              <AvatarImage src={formData.avatar_url || undefined} />
              <AvatarFallback className="text-2xl bg-indigo-600 text-white">
                {getInitials()}
              </AvatarFallback>
            </Avatar>

            <div className="flex-1 space-y-3">
              <p className="text-sm text-muted-foreground">
                Your photo appears on reports and emails.
              </p>
              <div className="flex gap-2">
                <ImageUpload
                  label="Upload Photo"
                  value={formData.avatar_url}
                  onChange={(url) => setFormData({ ...formData, avatar_url: url })}
                  assetType="headshot"
                  aspectRatio="square"
                  helpText=""
                  className="w-auto"
                />
                {formData.avatar_url && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setFormData({ ...formData, avatar_url: null })}
                  >
                    <X className="w-4 h-4 mr-1" />
                    Remove
                  </Button>
                )}
              </div>
              <p className="text-xs text-muted-foreground">
                Recommended: Square image, at least 400×400px
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Personal Information */}
      <div className="bg-card border border-border rounded-xl overflow-hidden shadow-[var(--shadow-card)]">
        <div className="px-5 py-3.5 border-b border-border bg-muted/20">
          <h3 className="text-[13px] font-semibold text-foreground">Personal Information</h3>
        </div>
        <div className="p-5">
        <div className="space-y-4">
          <div className="grid sm:grid-cols-2 gap-4">
            <div>
              <Label htmlFor="first_name">First Name</Label>
              <Input
                id="first_name"
                value={formData.first_name}
                onChange={(e) => setFormData({ ...formData, first_name: e.target.value })}
                placeholder="Jerry"
                className="mt-1.5"
              />
            </div>
            <div>
              <Label htmlFor="last_name">Last Name</Label>
              <Input
                id="last_name"
                value={formData.last_name}
                onChange={(e) => setFormData({ ...formData, last_name: e.target.value })}
                placeholder="Mendoza"
                className="mt-1.5"
              />
            </div>
          </div>

          <div>
            <Label htmlFor="job_title">Job Title</Label>
            <Input
              id="job_title"
              value={formData.job_title}
              onChange={(e) => setFormData({ ...formData, job_title: e.target.value })}
              placeholder="Real Estate Agent"
              className="mt-1.5"
            />
          </div>

          <div>
            <Label htmlFor="company_name">Company</Label>
            <Input
              id="company_name"
              value={formData.company_name}
              onChange={(e) => setFormData({ ...formData, company_name: e.target.value })}
              placeholder="Century 21 Masters"
              className="mt-1.5"
            />
          </div>
        </div>
        </div>
      </div>

      {/* Contact Information */}
      <div className="bg-card border border-border rounded-xl overflow-hidden shadow-[var(--shadow-card)]">
        <div className="px-5 py-3.5 border-b border-border bg-muted/20">
          <h3 className="text-[13px] font-semibold text-foreground">Contact Information</h3>
        </div>
        <div className="p-5 space-y-4">
          {/* Email (read-only) */}
          <div>
            <Label>Email</Label>
            <div className="mt-1.5 flex items-center gap-3 px-3 py-2.5 bg-muted/50 rounded-lg border">
              <Mail className="w-4 h-4 text-muted-foreground" />
              <span className="text-sm flex-1">{profile?.email}</span>
              {profile?.email_verified && (
                <Badge variant="secondary" className="text-green-600 bg-green-50 border-green-200">
                  <CheckCircle2 className="w-3 h-3 mr-1" />
                  Verified
                </Badge>
              )}
            </div>
            <p className="text-xs text-muted-foreground mt-1.5">
              This is your login email. Change it in{" "}
              <a href="/app/settings/security" className="text-indigo-600 hover:underline">
                Security settings
              </a>
              .
            </p>
          </div>

          <div>
            <Label htmlFor="phone">Phone</Label>
            <Input
              id="phone"
              type="tel"
              value={formData.phone}
              onChange={handlePhoneChange}
              placeholder="(626) 555-1234"
              maxLength={14}
              className="mt-1.5"
            />
          </div>

          <div>
            <Label htmlFor="website">Website</Label>
            <Input
              id="website"
              type="url"
              value={formData.website}
              onChange={(e) => setFormData({ ...formData, website: e.target.value })}
              placeholder="https://jerry.century21masters.com"
              className="mt-1.5"
            />
          </div>
        </div>
      </div>

      {/* Save Button */}
      <div className="flex justify-end">
        <Button onClick={saveProfile} disabled={saving} size="lg">
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
    </div>
  )
}

