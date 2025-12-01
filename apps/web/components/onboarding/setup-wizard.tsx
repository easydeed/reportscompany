"use client"

import { useState, useEffect } from "react"
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
} from "lucide-react"
import { useToast } from "@/components/ui/use-toast"
import { ImageUpload } from "@/components/ui/image-upload"
import { cn } from "@/lib/utils"

interface SetupWizardProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onComplete?: () => void
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
}

export function SetupWizard({ open, onOpenChange, onComplete }: SetupWizardProps) {
  const router = useRouter()
  const { toast } = useToast()
  const [step, setStep] = useState<WizardStep>("welcome")
  const [saving, setSaving] = useState(false)

  const [profile, setProfile] = useState<ProfileData>({
    first_name: "",
    last_name: "",
    company_name: "",
    phone: "",
    avatar_url: null,
  })

  const [branding, setBranding] = useState<BrandingData>({
    logo_url: null,
    primary_color: "#7C3AED",
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
        setProfile({
          first_name: data.first_name || "",
          last_name: data.last_name || "",
          company_name: data.company_name || "",
          phone: data.phone || "",
          avatar_url: data.avatar_url,
        })
      }

      // Load branding
      const brandingRes = await fetch("/api/proxy/v1/account")
      if (brandingRes.ok) {
        const data = await brandingRes.json()
        setBranding({
          logo_url: data.logo_url || null,
          primary_color: data.primary_color || "#7C3AED",
        })
      }
    } catch (error) {
      console.error("Failed to load existing data:", error)
    }
  }

  async function saveProfile() {
    setSaving(true)
    try {
      const res = await fetch("/api/proxy/v1/users/me", {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(profile),
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
      router.push("/app/reports/new")
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
              <DialogTitle className="text-2xl">Welcome to Market Reports!</DialogTitle>
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
                    <p className="font-medium text-sm">Set up your branding</p>
                    <p className="text-xs text-muted-foreground">Upload your logo and colors</p>
                  </div>
                </div>
                <div className="flex items-center gap-3 p-3 rounded-lg bg-muted/50">
                  <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center">
                    <FileText className="w-4 h-4 text-primary" />
                  </div>
                  <div>
                    <p className="font-medium text-sm">Create your first report</p>
                    <p className="text-xs text-muted-foreground">Generate a market snapshot</p>
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
            <div className="space-y-4 py-4">
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
                  <Building className="w-4 h-4" />
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
                  <Phone className="w-4 h-4" />
                  Phone Number
                </Label>
                <Input
                  id="phone"
                  type="tel"
                  value={profile.phone}
                  onChange={(e) => setProfile({ ...profile, phone: e.target.value })}
                  placeholder="(555) 123-4567"
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
                Add your logo to personalize your reports. You can customize more later.
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <ImageUpload
                label="Company Logo"
                value={branding.logo_url}
                onChange={(url) => setBranding({ ...branding, logo_url: url })}
                assetType="logo"
                aspectRatio="wide"
                helpText="Recommended: 400x150px, PNG with transparency"
              />

              <div className="space-y-2">
                <Label>Primary Color</Label>
                <div className="flex gap-2">
                  <Input
                    type="color"
                    value={branding.primary_color}
                    onChange={(e) => setBranding({ ...branding, primary_color: e.target.value })}
                    className="w-14 h-10 p-1 cursor-pointer"
                  />
                  <Input
                    type="text"
                    value={branding.primary_color}
                    onChange={(e) => setBranding({ ...branding, primary_color: e.target.value })}
                    className="flex-1 font-mono text-sm"
                    placeholder="#7C3AED"
                  />
                </div>
                <p className="text-xs text-muted-foreground">
                  Used for headers and accents on your reports
                </p>
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
                Your account is ready. Let's create your first market report.
              </DialogDescription>
            </DialogHeader>
            <div className="py-6">
              <div className="rounded-lg border bg-gradient-to-br from-primary/5 to-primary/10 p-4 text-center">
                <FileText className="w-12 h-12 text-primary mx-auto mb-3" />
                <h3 className="font-semibold mb-1">Create Your First Report</h3>
                <p className="text-sm text-muted-foreground mb-4">
                  Generate a beautiful market snapshot report in seconds.
                </p>
              </div>
            </div>
            <div className="flex justify-center">
              <Button onClick={handleNext} size="lg" className="gap-2">
                Create Report
                <ArrowRight className="w-4 h-4" />
              </Button>
            </div>
          </>
        )}
      </DialogContent>
    </Dialog>
  )
}
