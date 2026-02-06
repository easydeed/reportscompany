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
  User,
  Building2,
  Phone,
  Globe,
  Briefcase,
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
    <div className="max-w-4xl mx-auto">
      {/* Page Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-foreground">Profile</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Your personal information appears on reports and emails
          </p>
        </div>
        <Button onClick={saveProfile} disabled={saving}>
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

      <div className="grid lg:grid-cols-[280px_1fr] gap-8">
        {/* Left Column - Avatar Card */}
        <div className="space-y-6">
          {/* Avatar Card */}
          <div className="bg-card border border-border rounded-2xl shadow-[var(--shadow-card)] p-6 text-center">
            <div className="relative inline-block group mb-4">
              <Avatar className="w-28 h-28 border-4 border-background shadow-lg">
                <AvatarImage src={formData.avatar_url || undefined} />
                <AvatarFallback className="text-3xl font-semibold bg-gradient-to-br from-indigo-500 to-indigo-600 text-white">
                  {getInitials()}
                </AvatarFallback>
              </Avatar>
              <div className="absolute inset-0 rounded-full bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center cursor-pointer">
                <Camera className="w-6 h-6 text-white" />
              </div>
            </div>
            
            <h3 className="font-semibold text-foreground text-lg">
              {formData.first_name && formData.last_name 
                ? `${formData.first_name} ${formData.last_name}`
                : formData.first_name || "Your Name"
              }
            </h3>
            {formData.job_title && (
              <p className="text-sm text-muted-foreground">{formData.job_title}</p>
            )}
            {formData.company_name && (
              <p className="text-sm text-muted-foreground mt-0.5">{formData.company_name}</p>
            )}
            
            <div className="mt-4 pt-4 border-t border-border">
              <ImageUpload
                label="Change Photo"
                value={formData.avatar_url}
                onChange={(url) => setFormData({ ...formData, avatar_url: url })}
                assetType="headshot"
                aspectRatio="square"
                helpText=""
                className="w-full"
              />
              {formData.avatar_url && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setFormData({ ...formData, avatar_url: null })}
                  className="mt-2 text-muted-foreground hover:text-destructive w-full"
                >
                  <X className="w-4 h-4 mr-1.5" />
                  Remove Photo
                </Button>
              )}
            </div>
          </div>

          {/* Email Status Card */}
          <div className="bg-card border border-border rounded-2xl shadow-[var(--shadow-card)] p-5">
            <div className="flex items-center gap-3 mb-3">
              <div className="w-10 h-10 rounded-xl bg-indigo-50 flex items-center justify-center">
                <Mail className="w-5 h-5 text-indigo-600" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-xs text-muted-foreground font-medium uppercase tracking-wide">Email</p>
                <p className="text-sm text-foreground truncate">{profile?.email}</p>
              </div>
            </div>
            {profile?.email_verified ? (
              <Badge className="bg-emerald-50 text-emerald-700 border-emerald-200 w-full justify-center py-1.5">
                <CheckCircle2 className="w-3.5 h-3.5 mr-1.5" />
                Verified
              </Badge>
            ) : (
              <Badge variant="secondary" className="w-full justify-center py-1.5">
                Unverified
              </Badge>
            )}
            <p className="text-[11px] text-muted-foreground mt-3 text-center">
              Change email in{" "}
              <a href="/app/settings/security" className="text-indigo-600 hover:underline">
                Security settings
              </a>
            </p>
          </div>
        </div>

        {/* Right Column - Form */}
        <div className="space-y-6">
          {/* Personal Information */}
          <div className="bg-card border border-border rounded-2xl shadow-[var(--shadow-card)] overflow-hidden">
            <div className="px-6 py-4 border-b border-border bg-muted/30 flex items-center gap-3">
              <div className="w-9 h-9 rounded-lg bg-indigo-50 flex items-center justify-center">
                <User className="w-4 h-4 text-indigo-600" />
              </div>
              <div>
                <h3 className="text-sm font-semibold text-foreground">Personal Information</h3>
                <p className="text-xs text-muted-foreground">Your name as it appears on reports</p>
              </div>
            </div>
            <div className="p-6 grid sm:grid-cols-2 gap-5">
              <div className="space-y-2">
                <Label htmlFor="first_name" className="text-xs font-medium text-muted-foreground">
                  First Name
                </Label>
                <Input
                  id="first_name"
                  value={formData.first_name}
                  onChange={(e) => setFormData({ ...formData, first_name: e.target.value })}
                  placeholder="Jerry"
                  className="h-10"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="last_name" className="text-xs font-medium text-muted-foreground">
                  Last Name
                </Label>
                <Input
                  id="last_name"
                  value={formData.last_name}
                  onChange={(e) => setFormData({ ...formData, last_name: e.target.value })}
                  placeholder="Mendoza"
                  className="h-10"
                />
              </div>
            </div>
          </div>

          {/* Professional Information */}
          <div className="bg-card border border-border rounded-2xl shadow-[var(--shadow-card)] overflow-hidden">
            <div className="px-6 py-4 border-b border-border bg-muted/30 flex items-center gap-3">
              <div className="w-9 h-9 rounded-lg bg-amber-50 flex items-center justify-center">
                <Briefcase className="w-4 h-4 text-amber-600" />
              </div>
              <div>
                <h3 className="text-sm font-semibold text-foreground">Professional Details</h3>
                <p className="text-xs text-muted-foreground">Your title and company</p>
              </div>
            </div>
            <div className="p-6 grid sm:grid-cols-2 gap-5">
              <div className="space-y-2">
                <Label htmlFor="job_title" className="text-xs font-medium text-muted-foreground">
                  Job Title
                </Label>
                <Input
                  id="job_title"
                  value={formData.job_title}
                  onChange={(e) => setFormData({ ...formData, job_title: e.target.value })}
                  placeholder="Real Estate Agent"
                  className="h-10"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="company_name" className="text-xs font-medium text-muted-foreground">
                  Company
                </Label>
                <Input
                  id="company_name"
                  value={formData.company_name}
                  onChange={(e) => setFormData({ ...formData, company_name: e.target.value })}
                  placeholder="Century 21 Masters"
                  className="h-10"
                />
              </div>
            </div>
          </div>

          {/* Contact Information */}
          <div className="bg-card border border-border rounded-2xl shadow-[var(--shadow-card)] overflow-hidden">
            <div className="px-6 py-4 border-b border-border bg-muted/30 flex items-center gap-3">
              <div className="w-9 h-9 rounded-lg bg-emerald-50 flex items-center justify-center">
                <Phone className="w-4 h-4 text-emerald-600" />
              </div>
              <div>
                <h3 className="text-sm font-semibold text-foreground">Contact Information</h3>
                <p className="text-xs text-muted-foreground">How clients can reach you</p>
              </div>
            </div>
            <div className="p-6 grid sm:grid-cols-2 gap-5">
              <div className="space-y-2">
                <Label htmlFor="phone" className="text-xs font-medium text-muted-foreground">
                  Phone Number
                </Label>
                <div className="relative">
                  <Phone className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                  <Input
                    id="phone"
                    type="tel"
                    value={formData.phone}
                    onChange={handlePhoneChange}
                    placeholder="(626) 555-1234"
                    maxLength={14}
                    className="h-10 pl-10"
                  />
                </div>
              </div>
              <div className="space-y-2">
                <Label htmlFor="website" className="text-xs font-medium text-muted-foreground">
                  Website
                </Label>
                <div className="relative">
                  <Globe className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                  <Input
                    id="website"
                    type="url"
                    value={formData.website}
                    onChange={(e) => setFormData({ ...formData, website: e.target.value })}
                    placeholder="https://yoursite.com"
                    className="h-10 pl-10"
                  />
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
