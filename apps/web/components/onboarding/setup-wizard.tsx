"use client"

import { useState, useEffect, useCallback } from "react"
import { useRouter } from "next/navigation"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Progress } from "@/components/ui/progress"
import {
  User,
  Building,
  Phone,
  ArrowRight,
  ArrowLeft,
  Check,
  Sparkles,
  Loader2,
  Palette,
  FileText,
  Camera,
} from "lucide-react"
import { useToast } from "@/components/ui/use-toast"
import { ImageUpload } from "@/components/ui/image-upload"
import { cn } from "@/lib/utils"

interface SetupWizardProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onComplete?: () => void
  isAffiliate?: boolean
}

type WizardStep = "welcome" | "profile" | "branding" | "complete"

interface ProfileData {
  first_name: string
  last_name: string
  company_name: string
  phone: string
  avatar_url: string | null
}

interface BrandingData {
  logo_url: string | null
  primary_color: string
  accent_color: string
}

// Phone number formatting helper
function formatPhoneNumber(value: string): string {
  // Remove all non-digits
  const digits = value.replace(/\D/g, "")
  
  // Format as (XXX) XXX-XXXX
  if (digits.length === 0) return ""
  if (digits.length <= 3) return `(${digits}`
  if (digits.length <= 6) return `(${digits.slice(0, 3)}) ${digits.slice(3)}`
  return `(${digits.slice(0, 3)}) ${digits.slice(3, 6)}-${digits.slice(6, 10)}`
}

export function SetupWizard({ open, onOpenChange, onComplete, isAffiliate = false }: SetupWizardProps) {
  const router = useRouter()
  const { toast } = useToast()
  const [step, setStep] = useState<WizardStep>("welcome")
  const [saving, setSaving] = useState(false)
  const [accountType, setAccountType] = useState<string | null>(null)
  const [userName, setUserName] = useState<string>("")

  const [profile, setProfile] = useState<ProfileData>({
    first_name: "",
    last_name: "",
    company_name: "",
    phone: "",
    avatar_url: null,
  })

  const [branding, setBranding] = useState<BrandingData>({
    logo_url: null,
    primary_color: "#4F46E5",
    accent_color: "#F26B2B",
  })

  // Load existing data when dialog opens
  useEffect(() => {
    if (open) {
      loadExistingData()
    }
  }, [open])

  async function loadExistingData() {
    try {
      // Load profile
      const profileRes = await fetch("/api/proxy/v1/users/me")
      if (profileRes.ok) {
        const data = await profileRes.json()
        
        // If we have a name but not first/last name, split it
        let firstName = data.first_name || ""
        let lastName = data.last_name || ""
        
        if (!firstName && !lastName && data.name) {
          // Split full name into first and last
          const nameParts = data.name.trim().split(/\s+/)
          firstName = nameParts[0] || ""
          lastName = nameParts.slice(1).join(" ") || ""
        }
        
        // Also try to extract from account name (e.g., "John's Account" -> "John")
        if (!firstName && data.account_name) {
          const match = data.account_name.match(/^(.+?)'s Account$/i)
          if (match) {
            const nameParts = match[1].trim().split(/\s+/)
            firstName = nameParts[0] || ""
            lastName = nameParts.slice(1).join(" ") || ""
          }
        }
        
        setUserName(firstName || data.name || "there")
        setProfile({
          first_name: firstName,
          last_name: lastName,
          company_name: data.company_name || "",
          phone: data.phone ? formatPhoneNumber(data.phone) : "",
          avatar_url: data.avatar_url,
        })
      }

      // Load branding and account type
      const brandingRes = await fetch("/api/proxy/v1/account")
      if (brandingRes.ok) {
        const data = await brandingRes.json()
        setBranding({
          logo_url: data.logo_url || null,
          primary_color: data.primary_color || "#4F46E5",
          accent_color: data.secondary_color || "#F26B2B",
        })
        setAccountType(data.account_type || null)
        
        // Try to extract name from account name if not set
        if (!userName && data.name) {
          const match = data.name.match(/^(.+?)'s Account$/i)
          if (match) {
            setUserName(match[1].split(/\s+/)[0] || "there")
          }
        }
      }
    } catch (error) {
      console.error("Failed to load existing data:", error)
    }
  }
  
  // Handle phone number formatting
  const handlePhoneChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const formatted = formatPhoneNumber(e.target.value)
    setProfile(prev => ({ ...prev, phone: formatted }))
  }, [])

  // Check if user is an affiliate
  const isAffiliateAccount = isAffiliate || accountType === "INDUSTRY_AFFILIATE"

  async function saveProfile() {
    setSaving(true)
    try {
      // Strip phone formatting for storage
      const cleanPhone = profile.phone.replace(/\D/g, "")
      
      const res = await fetch("/api/proxy/v1/users/me", {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          first_name: profile.first_name,
          last_name: profile.last_name,
          company_name: profile.company_name,
          phone: cleanPhone,
          avatar_url: profile.avatar_url,
        }),
      })

      if (!res.ok) {
        throw new Error("Failed to save profile")
      }

      // Mark step complete
      await fetch("/api/proxy/v1/onboarding/complete-step", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ step_key: "profile_complete" }),
      })

      return true
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to save profile. Please try again.",
        variant: "destructive",
      })
      return false
    } finally {
      setSaving(false)
    }
  }

  async function saveBranding() {
    setSaving(true)
    try {
      const res = await fetch("/api/proxy/v1/account/branding", {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          logo_url: branding.logo_url,
          primary_color: branding.primary_color,
          secondary_color: branding.accent_color,
        }),
      })

      if (!res.ok) {
        throw new Error("Failed to save branding")
      }

      // Mark step complete
      await fetch("/api/proxy/v1/onboarding/complete-step", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ step_key: "branding_setup" }),
      })

      return true
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to save branding. Please try again.",
        variant: "destructive",
      })
      return false
    } finally {
      setSaving(false)
    }
  }

  async function handleNext() {
    if (step === "welcome") {
      setStep("profile")
    } else if (step === "profile") {
      const success = await saveProfile()
      if (success) {
        setStep("branding")
      }
    } else if (step === "branding") {
      const success = await saveBranding()
      if (success) {
        setStep("complete")
      }
    } else if (step === "complete") {
      onOpenChange(false)
      onComplete?.()
      // Route affiliates to their dashboard, agents to create report
      if (isAffiliateAccount) {
        router.push("/app/affiliate")
      } else {
        router.push("/app/reports/new")
      }
    }
  }

  function handleBack() {
    if (step === "profile") setStep("welcome")
    else if (step === "branding") setStep("profile")
  }

  function handleSkip() {
    if (step === "profile") setStep("branding")
    else if (step === "branding") setStep("complete")
  }

  const stepIndex = ["welcome", "profile", "branding", "complete"].indexOf(step)
  const progress = ((stepIndex + 1) / 4) * 100

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg">
        {/* Progress bar */}
        <div className="absolute top-0 left-0 right-0">
          <Progress value={progress} className="h-1 rounded-none" />
        </div>

        {/* Welcome Step */}
        {step === "welcome" && (
          <>
            <DialogHeader className="text-center pt-4">
              <div className="mx-auto w-16 h-16 rounded-full bg-gradient-to-br from-primary to-primary/60 flex items-center justify-center mb-4">
                <Sparkles className="w-8 h-8 text-white" />
              </div>
              <DialogTitle className="text-2xl">
                Welcome{userName ? `, ${userName}` : ""}!
              </DialogTitle>
              <DialogDescription className="text-base mt-2">
                Let's get your account set up in just a few steps. This will only take about 2 minutes.
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="grid gap-3">
                <div className="flex items-center gap-3 p-3 rounded-lg bg-muted/50">
                  <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center">
                    <User className="w-4 h-4 text-primary" />
                  </div>
                  <div>
                    <p className="font-medium text-sm">Complete your profile</p>
                    <p className="text-xs text-muted-foreground">Add your name and contact info</p>
                  </div>
                </div>
                <div className="flex items-center gap-3 p-3 rounded-lg bg-muted/50">
                  <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center">
                    <Palette className="w-4 h-4 text-primary" />
                  </div>
                  <div>
                    <p className="font-medium text-sm">
                      {isAffiliateAccount ? "Set up white-label branding" : "Set up your branding"}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {isAffiliateAccount ? "Your branding appears on sponsored agent reports" : "Upload your logo and colors"}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-3 p-3 rounded-lg bg-muted/50">
                  <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center">
                    {isAffiliateAccount ? (
                      <Building className="w-4 h-4 text-primary" />
                    ) : (
                      <FileText className="w-4 h-4 text-primary" />
                    )}
                  </div>
                  <div>
                    <p className="font-medium text-sm">
                      {isAffiliateAccount ? "Invite your first agent" : "Create your first report"}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {isAffiliateAccount ? "Sponsor agents with your branding" : "Generate a market snapshot"}
                    </p>
                  </div>
                </div>
              </div>
            </div>
            <div className="flex justify-end">
              <Button onClick={handleNext} className="gap-2">
                Get Started
                <ArrowRight className="w-4 h-4" />
              </Button>
            </div>
          </>
        )}

        {/* Profile Step */}
        {step === "profile" && (
          <>
            <DialogHeader>
              <DialogTitle>Complete your profile</DialogTitle>
              <DialogDescription>
                Tell us a bit about yourself so we can personalize your experience.
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-5 py-4">
              {/* Headshot Upload */}
              <div className="flex justify-center">
                <ImageUpload
                  label="Your Headshot"
                  value={profile.avatar_url}
                  onChange={(url) => setProfile({ ...profile, avatar_url: url })}
                  assetType="headshot"
                  aspectRatio="square"
                  helpText="Optional • Makes your reports more personal"
                  className="w-full max-w-[200px]"
                />
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="first_name">First Name</Label>
                  <Input
                    id="first_name"
                    value={profile.first_name}
                    onChange={(e) => setProfile({ ...profile, first_name: e.target.value })}
                    placeholder="John"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="last_name">Last Name</Label>
                  <Input
                    id="last_name"
                    value={profile.last_name}
                    onChange={(e) => setProfile({ ...profile, last_name: e.target.value })}
                    placeholder="Doe"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="company_name" className="flex items-center gap-2">
                  <Building className="w-4 h-4 text-muted-foreground" />
                  Company Name
                </Label>
                <Input
                  id="company_name"
                  value={profile.company_name}
                  onChange={(e) => setProfile({ ...profile, company_name: e.target.value })}
                  placeholder="Acme Real Estate"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="phone" className="flex items-center gap-2">
                  <Phone className="w-4 h-4 text-muted-foreground" />
                  Phone Number
                </Label>
                <Input
                  id="phone"
                  type="tel"
                  value={profile.phone}
                  onChange={handlePhoneChange}
                  placeholder="(555) 123-4567"
                  maxLength={14}
                />
              </div>
            </div>
            <div className="flex justify-between">
              <Button variant="ghost" onClick={handleBack} className="gap-2">
                <ArrowLeft className="w-4 h-4" />
                Back
              </Button>
              <div className="flex gap-2">
                <Button variant="ghost" onClick={handleSkip}>
                  Skip for now
                </Button>
                <Button onClick={handleNext} disabled={saving} className="gap-2">
                  {saving ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <>
                      Continue
                      <ArrowRight className="w-4 h-4" />
                    </>
                  )}
                </Button>
              </div>
            </div>
          </>
        )}

        {/* Branding Step */}
        {step === "branding" && (
          <>
            <DialogHeader>
              <DialogTitle>Set up your branding</DialogTitle>
              <DialogDescription>
                Add your logo and brand colors to personalize your reports.
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-5 py-4">
              <ImageUpload
                label="Company Logo"
                value={branding.logo_url}
                onChange={(url) => setBranding({ ...branding, logo_url: url })}
                assetType="logo"
                aspectRatio="wide"
                helpText="Recommended: 400x150px, PNG with transparency"
              />

              {/* Color Pickers - Side by Side */}
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label className="text-sm font-medium">Primary Color</Label>
                  <div className="flex items-center gap-2 p-3 rounded-lg border bg-muted/30">
                    <div className="relative">
                      <input
                        type="color"
                        value={branding.primary_color}
                        onChange={(e) => setBranding({ ...branding, primary_color: e.target.value })}
                        className="w-10 h-10 rounded-lg cursor-pointer border-0 p-0"
                        style={{ backgroundColor: branding.primary_color }}
                      />
                      <div 
                        className="absolute inset-0 rounded-lg pointer-events-none ring-1 ring-inset ring-black/10"
                        style={{ backgroundColor: branding.primary_color }}
                      />
                    </div>
                    <div className="flex-1">
                      <Input
                        type="text"
                        value={branding.primary_color}
                        onChange={(e) => setBranding({ ...branding, primary_color: e.target.value })}
                        className="font-mono text-xs h-8"
                        placeholder="#4F46E5"
                      />
                    </div>
                  </div>
                  <p className="text-xs text-muted-foreground">
                    Headers & buttons
                  </p>
                </div>

                <div className="space-y-2">
                  <Label className="text-sm font-medium">Accent Color</Label>
                  <div className="flex items-center gap-2 p-3 rounded-lg border bg-muted/30">
                    <div className="relative">
                      <input
                        type="color"
                        value={branding.accent_color}
                        onChange={(e) => setBranding({ ...branding, accent_color: e.target.value })}
                        className="w-10 h-10 rounded-lg cursor-pointer border-0 p-0"
                        style={{ backgroundColor: branding.accent_color }}
                      />
                      <div 
                        className="absolute inset-0 rounded-lg pointer-events-none ring-1 ring-inset ring-black/10"
                        style={{ backgroundColor: branding.accent_color }}
                      />
                    </div>
                    <div className="flex-1">
                      <Input
                        type="text"
                        value={branding.accent_color}
                        onChange={(e) => setBranding({ ...branding, accent_color: e.target.value })}
                        className="font-mono text-xs h-8"
                        placeholder="#F26B2B"
                      />
                    </div>
                  </div>
                  <p className="text-xs text-muted-foreground">
                    Highlights & gradients
                  </p>
                </div>
              </div>

              {/* Live Preview */}
              <div className="rounded-lg border p-3 bg-muted/20">
                <p className="text-xs text-muted-foreground mb-2">Preview</p>
                <div 
                  className="h-8 rounded-md flex items-center justify-center text-white text-xs font-medium"
                  style={{ 
                    background: `linear-gradient(90deg, ${branding.primary_color}, ${branding.accent_color})` 
                  }}
                >
                  Your Report Header
                </div>
              </div>
            </div>
            <div className="flex justify-between">
              <Button variant="ghost" onClick={handleBack} className="gap-2">
                <ArrowLeft className="w-4 h-4" />
                Back
              </Button>
              <div className="flex gap-2">
                <Button variant="ghost" onClick={handleSkip}>
                  Skip for now
                </Button>
                <Button onClick={handleNext} disabled={saving} className="gap-2">
                  {saving ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <>
                      Continue
                      <ArrowRight className="w-4 h-4" />
                    </>
                  )}
                </Button>
              </div>
            </div>
          </>
        )}

        {/* Complete Step */}
        {step === "complete" && (
          <>
            <DialogHeader className="text-center pt-4">
              <div className="mx-auto w-16 h-16 rounded-full bg-green-500 flex items-center justify-center mb-4">
                <Check className="w-8 h-8 text-white" />
              </div>
              <DialogTitle className="text-2xl">You're all set!</DialogTitle>
              <DialogDescription className="text-base mt-2">
                {isAffiliateAccount 
                  ? "Your affiliate account is ready. Start inviting agents to sponsor them with your branding."
                  : "Your account is ready. Let's create your first market report."
                }
              </DialogDescription>
            </DialogHeader>
            <div className="py-6">
              <div className="rounded-lg border bg-gradient-to-br from-primary/5 to-primary/10 p-4 text-center">
                {isAffiliateAccount ? (
                  <>
                    <Building className="w-12 h-12 text-primary mx-auto mb-3" />
                    <h3 className="font-semibold mb-1">Invite Your First Agent</h3>
                    <p className="text-sm text-muted-foreground mb-4">
                      Sponsored agents get your branding on all their reports.
                    </p>
                  </>
                ) : (
                  <>
                    <FileText className="w-12 h-12 text-primary mx-auto mb-3" />
                    <h3 className="font-semibold mb-1">Create Your First Report</h3>
                    <p className="text-sm text-muted-foreground mb-4">
                      Generate a beautiful market snapshot report in seconds.
                    </p>
                  </>
                )}
              </div>
            </div>
            <div className="flex justify-center">
              <Button onClick={handleNext} size="lg" className="gap-2">
                {isAffiliateAccount ? "Go to Dashboard" : "Create Report"}
                <ArrowRight className="w-4 h-4" />
              </Button>
            </div>
          </>
        )}
      </DialogContent>
    </Dialog>
  )
}
