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
  Rocket,
  CircleDot,
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

const STEPS: { key: WizardStep; label: string; icon: React.ComponentType<{ className?: string }> }[] = [
  { key: "welcome", label: "Welcome", icon: Sparkles },
  { key: "profile", label: "Profile", icon: User },
  { key: "branding", label: "Branding", icon: Palette },
  { key: "complete", label: "Done", icon: Check },
]

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

  const stepIndex = STEPS.findIndex(s => s.key === step)

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg overflow-hidden p-0">
        {/* Modern step indicator bar */}
        <div className="px-6 pt-6 pb-0">
          <div className="flex items-center justify-between mb-1">
            {STEPS.map((s, i) => {
              const Icon = s.icon
              const isCompleted = i < stepIndex
              const isCurrent = i === stepIndex
              return (
                <div key={s.key} className="flex items-center flex-1 last:flex-none">
                  <div className="flex flex-col items-center gap-1">
                    <div
                      className={cn(
                        "w-9 h-9 rounded-full flex items-center justify-center transition-all duration-300 ring-2",
                        isCompleted
                          ? "bg-green-500 ring-green-200 text-white scale-100"
                          : isCurrent
                          ? "bg-primary ring-primary/30 text-primary-foreground scale-110 shadow-lg shadow-primary/20"
                          : "bg-muted ring-border text-muted-foreground scale-90"
                      )}
                    >
                      {isCompleted ? (
                        <Check className="w-4 h-4" />
                      ) : (
                        <Icon className="w-4 h-4" />
                      )}
                    </div>
                    <span
                      className={cn(
                        "text-[10px] font-medium transition-colors duration-300",
                        isCurrent ? "text-primary" : isCompleted ? "text-green-600" : "text-muted-foreground"
                      )}
                    >
                      {s.label}
                    </span>
                  </div>
                  {i < STEPS.length - 1 && (
                    <div className="flex-1 mx-2 mb-4">
                      <div className="h-0.5 rounded-full bg-border overflow-hidden">
                        <div
                          className={cn(
                            "h-full rounded-full transition-all duration-500",
                            isCompleted ? "bg-green-500 w-full" : "bg-border w-0"
                          )}
                        />
                      </div>
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        </div>

        <div className="px-6 pb-6">
          {/* Welcome Step */}
          {step === "welcome" && (
            <div className="animate-in fade-in slide-in-from-right-4 duration-300">
              <DialogHeader className="text-center pt-2 pb-4">
                <div className="mx-auto w-20 h-20 rounded-2xl bg-gradient-to-br from-primary via-primary/80 to-primary/60 flex items-center justify-center mb-4 shadow-xl shadow-primary/20 rotate-3 hover:rotate-0 transition-transform duration-300">
                  <Sparkles className="w-10 h-10 text-white" />
                </div>
                <DialogTitle className="text-2xl font-bold">
                  Welcome{userName ? `, ${userName}` : ""}! 🎉
                </DialogTitle>
                <DialogDescription className="text-base mt-2 text-muted-foreground/80">
                  Let&apos;s get your account set up in just a few quick steps.
                </DialogDescription>
              </DialogHeader>

              <div className="space-y-3 py-2">
                {[
                  {
                    icon: User,
                    title: "Complete your profile",
                    desc: "Add your name and contact info",
                    color: "bg-blue-500/10 text-blue-600",
                  },
                  {
                    icon: Palette,
                    title: isAffiliateAccount ? "Set up white-label branding" : "Set up your branding",
                    desc: isAffiliateAccount
                      ? "Your branding appears on sponsored agent reports"
                      : "Upload your logo and brand colors",
                    color: "bg-orange-500/10 text-orange-600",
                  },
                  {
                    icon: isAffiliateAccount ? Building : FileText,
                    title: isAffiliateAccount ? "Invite your first agent" : "Create your first report",
                    desc: isAffiliateAccount
                      ? "Sponsor agents with your branding"
                      : "Generate a market snapshot in seconds",
                    color: "bg-emerald-500/10 text-emerald-600",
                  },
                ].map((item, i) => (
                  <div
                    key={i}
                    className="flex items-center gap-4 p-3.5 rounded-xl border border-border/50 bg-muted/30 hover:bg-muted/50 transition-colors duration-200"
                    style={{ animationDelay: `${(i + 1) * 100}ms` }}
                  >
                    <div className={cn("w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0", item.color)}>
                      <item.icon className="w-5 h-5" />
                    </div>
                    <div>
                      <p className="font-semibold text-sm">{item.title}</p>
                      <p className="text-xs text-muted-foreground">{item.desc}</p>
                    </div>
                    <div className="ml-auto">
                      <CircleDot className="w-4 h-4 text-muted-foreground/40" />
                    </div>
                  </div>
                ))}
              </div>

              <p className="text-xs text-center text-muted-foreground mt-3">
                ⏱️ Takes about 2 minutes
              </p>

              <div className="flex justify-end mt-4">
                <Button onClick={handleNext} size="lg" className="gap-2 shadow-lg shadow-primary/20 hover:shadow-xl hover:shadow-primary/30 transition-all">
                  Get Started
                  <ArrowRight className="w-4 h-4" />
                </Button>
              </div>
            </div>
          )}

          {/* Profile Step */}
          {step === "profile" && (
            <div className="animate-in fade-in slide-in-from-right-4 duration-300">
              <DialogHeader className="pb-2">
                <DialogTitle className="text-xl">Complete your profile</DialogTitle>
                <DialogDescription>
                  Tell us a bit about yourself so we can personalize your experience.
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-5 py-3">
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
                    <Label htmlFor="first_name" className="text-xs font-medium">First Name</Label>
                    <Input
                      id="first_name"
                      value={profile.first_name}
                      onChange={(e) => setProfile({ ...profile, first_name: e.target.value })}
                      placeholder="John"
                      className="h-10"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="last_name" className="text-xs font-medium">Last Name</Label>
                    <Input
                      id="last_name"
                      value={profile.last_name}
                      onChange={(e) => setProfile({ ...profile, last_name: e.target.value })}
                      placeholder="Doe"
                      className="h-10"
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="company_name" className="flex items-center gap-2 text-xs font-medium">
                    <Building className="w-3.5 h-3.5 text-muted-foreground" />
                    Company Name
                  </Label>
                  <Input
                    id="company_name"
                    value={profile.company_name}
                    onChange={(e) => setProfile({ ...profile, company_name: e.target.value })}
                    placeholder="Acme Real Estate"
                    className="h-10"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="phone" className="flex items-center gap-2 text-xs font-medium">
                    <Phone className="w-3.5 h-3.5 text-muted-foreground" />
                    Phone Number
                  </Label>
                  <Input
                    id="phone"
                    type="tel"
                    value={profile.phone}
                    onChange={handlePhoneChange}
                    placeholder="(555) 123-4567"
                    maxLength={14}
                    className="h-10"
                  />
                </div>
              </div>
              <div className="flex justify-between pt-2">
                <Button variant="ghost" onClick={handleBack} className="gap-2">
                  <ArrowLeft className="w-4 h-4" />
                  Back
                </Button>
                <div className="flex gap-2">
                  <Button variant="ghost" onClick={handleSkip} className="text-muted-foreground">
                    Skip for now
                  </Button>
                  <Button onClick={handleNext} disabled={saving} className="gap-2 min-w-[120px]">
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
            </div>
          )}

          {/* Branding Step */}
          {step === "branding" && (
            <div className="animate-in fade-in slide-in-from-right-4 duration-300">
              <DialogHeader className="pb-2">
                <DialogTitle className="text-xl">Set up your branding</DialogTitle>
                <DialogDescription>
                  Add your logo and brand colors to personalize your reports.
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-5 py-3">
                <ImageUpload
                  label="Company Logo"
                  value={branding.logo_url}
                  onChange={(url) => setBranding({ ...branding, logo_url: url })}
                  assetType="logo"
                  aspectRatio="wide"
                  helpText="Recommended: 400x150px, PNG with transparency"
                />

                {/* Color Pickers - Modern layout */}
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label className="text-xs font-medium">Primary Color</Label>
                    <div className="flex items-center gap-2.5 p-3 rounded-xl border bg-muted/20 hover:bg-muted/40 transition-colors">
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
                    <p className="text-[10px] text-muted-foreground">
                      Headers & buttons
                    </p>
                  </div>

                  <div className="space-y-2">
                    <Label className="text-xs font-medium">Accent Color</Label>
                    <div className="flex items-center gap-2.5 p-3 rounded-xl border bg-muted/20 hover:bg-muted/40 transition-colors">
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
                    <p className="text-[10px] text-muted-foreground">
                      Highlights & gradients
                    </p>
                  </div>
                </div>

                {/* Live Preview - Enhanced */}
                <div className="rounded-xl border bg-muted/10 p-4 space-y-2">
                  <p className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Live Preview</p>
                  <div 
                    className="h-10 rounded-lg flex items-center justify-center text-white text-xs font-semibold shadow-md"
                    style={{ 
                      background: `linear-gradient(135deg, ${branding.primary_color}, ${branding.accent_color})` 
                    }}
                  >
                    Your Report Header
                  </div>
                  <div className="flex gap-2 mt-2">
                    <div
                      className="flex-1 h-2 rounded-full"
                      style={{ backgroundColor: branding.primary_color }}
                    />
                    <div
                      className="w-16 h-2 rounded-full"
                      style={{ backgroundColor: branding.accent_color }}
                    />
                  </div>
                </div>
              </div>
              <div className="flex justify-between pt-2">
                <Button variant="ghost" onClick={handleBack} className="gap-2">
                  <ArrowLeft className="w-4 h-4" />
                  Back
                </Button>
                <div className="flex gap-2">
                  <Button variant="ghost" onClick={handleSkip} className="text-muted-foreground">
                    Skip for now
                  </Button>
                  <Button onClick={handleNext} disabled={saving} className="gap-2 min-w-[120px]">
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
            </div>
          )}

          {/* Complete Step */}
          {step === "complete" && (
            <div className="animate-in fade-in slide-in-from-right-4 duration-300">
              <DialogHeader className="text-center pt-4 pb-2">
                <div className="mx-auto w-20 h-20 rounded-2xl bg-gradient-to-br from-green-400 to-emerald-600 flex items-center justify-center mb-4 shadow-xl shadow-green-500/20 animate-in zoom-in-50 duration-500">
                  <Check className="w-10 h-10 text-white" />
                </div>
                <DialogTitle className="text-2xl font-bold">You&apos;re all set! 🚀</DialogTitle>
                <DialogDescription className="text-base mt-2">
                  {isAffiliateAccount 
                    ? "Your affiliate account is ready. Start inviting agents to sponsor them with your branding."
                    : "Your account is ready. Let's create your first market report."
                  }
                </DialogDescription>
              </DialogHeader>
              <div className="py-4">
                <div className="rounded-xl border-2 border-dashed border-primary/20 bg-gradient-to-br from-primary/5 via-primary/10 to-primary/5 p-6 text-center">
                  {isAffiliateAccount ? (
                    <>
                      <div className="w-14 h-14 rounded-2xl bg-primary/10 flex items-center justify-center mx-auto mb-3">
                        <Building className="w-7 h-7 text-primary" />
                      </div>
                      <h3 className="font-bold text-lg mb-1">Invite Your First Agent</h3>
                      <p className="text-sm text-muted-foreground mb-4 max-w-xs mx-auto">
                        Sponsored agents get your branding on all their reports.
                      </p>
                    </>
                  ) : (
                    <>
                      <div className="w-14 h-14 rounded-2xl bg-primary/10 flex items-center justify-center mx-auto mb-3">
                        <Rocket className="w-7 h-7 text-primary" />
                      </div>
                      <h3 className="font-bold text-lg mb-1">Create Your First Report</h3>
                      <p className="text-sm text-muted-foreground mb-4 max-w-xs mx-auto">
                        Generate a beautiful market snapshot report in just seconds.
                      </p>
                    </>
                  )}
                </div>
              </div>
              <div className="flex justify-center">
                <Button onClick={handleNext} size="lg" className="gap-2 shadow-lg shadow-primary/20 hover:shadow-xl hover:shadow-primary/30 transition-all px-8">
                  {isAffiliateAccount ? "Go to Dashboard" : "Create Report"}
                  <ArrowRight className="w-4 h-4" />
                </Button>
              </div>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  )
}
