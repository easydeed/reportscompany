"use client"

import { useEffect, useState, useCallback } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Badge } from "@/components/ui/badge"
import {
  User,
  Lock,
  Mail,
  Building,
  Phone,
  Save,
  Loader2,
  Eye,
  EyeOff,
  AlertCircle,
  CheckCircle2,
  CreditCard,
  Check,
  Shield,
  Settings,
  Sparkles,
  Camera,
} from "lucide-react"
import { useToast } from "@/components/ui/use-toast"
import { ImageUpload } from "@/components/ui/image-upload"
import { useRouter } from "next/navigation"

type UserProfile = {
  id: string
  email: string
  first_name: string | null
  last_name: string | null
  company_name: string | null
  phone: string | null
  avatar_url: string | null
  email_verified: boolean
  created_at: string | null
}

type ProfileFormData = {
  first_name: string
  last_name: string
  company_name: string
  phone: string
  avatar_url: string | null
}

type PasswordFormData = {
  currentPassword: string
  newPassword: string
  confirmPassword: string
}

type EmailFormData = {
  newEmail: string
  currentPassword: string
}

type PlanUsageData = {
  account: {
    id: string
    name: string
    account_type: string
    plan_slug: string
    billing_status?: string | null
  }
  plan: {
    plan_name: string
    plan_slug: string
    monthly_report_limit: number
  }
  usage: {
    report_count: number
  }
  stripe_billing?: {
    stripe_price_id: string
    amount: number
    currency: string
    interval: string
    interval_count: number
    nickname?: string | null
  } | null
}

// Phone number formatting helper
function formatPhoneNumber(value: string): string {
  const digits = value.replace(/\D/g, '')
  if (digits.length === 0) return ''
  if (digits.length <= 3) return `(${digits}`
  if (digits.length <= 6) return `(${digits.slice(0, 3)}) ${digits.slice(3)}`
  return `(${digits.slice(0, 3)}) ${digits.slice(3, 6)}-${digits.slice(6, 10)}`
}

// Available plans for upgrade
const plans = [
  {
    name: "Free",
    slug: "free",
    price: "$0",
    period: "/month",
    description: "Perfect for trying out",
    features: ["50 reports / month", "6 report types", "PDF export", "Email support"],
  },
  {
    name: "Solo Agent",
    slug: "solo",
    price: "$19",
    period: "/month",
    description: "For individual agents",
    features: ["500 reports / month", "All report types", "Custom branding", "Priority support"],
    popular: true,
  },
]

export default function AccountSettingsPage() {
  const [loading, setLoading] = useState(true)
  const [savingProfile, setSavingProfile] = useState(false)
  const [savingPassword, setSavingPassword] = useState(false)
  const [savingEmail, setSavingEmail] = useState(false)
  const [billingLoading, setBillingLoading] = useState(false)
  const { toast } = useToast()
  const router = useRouter()

  // User profile state
  const [profile, setProfile] = useState<UserProfile | null>(null)
  const [profileForm, setProfileForm] = useState<ProfileFormData>({
    first_name: "",
    last_name: "",
    company_name: "",
    phone: "",
    avatar_url: null,
  })

  // Password form state
  const [passwordForm, setPasswordForm] = useState<PasswordFormData>({
    currentPassword: "",
    newPassword: "",
    confirmPassword: "",
  })
  const [showCurrentPassword, setShowCurrentPassword] = useState(false)
  const [showNewPassword, setShowNewPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)

  // Email form state
  const [emailForm, setEmailForm] = useState<EmailFormData>({
    newEmail: "",
    currentPassword: "",
  })
  const [showEmailPassword, setShowEmailPassword] = useState(false)

  // Billing state
  const [billingData, setBillingData] = useState<PlanUsageData | null>(null)

  // Phone formatting handler
  const handlePhoneChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const formatted = formatPhoneNumber(e.target.value)
    setProfileForm(prev => ({ ...prev, phone: formatted }))
  }, [])

  useEffect(() => {
    loadAllData()
  }, [])

  async function loadAllData() {
    setLoading(true)
    try {
      // Fetch profile and billing in parallel
      const [profileRes, billingRes] = await Promise.all([
        fetch("/api/proxy/v1/users/me", { cache: "no-store", credentials: "include" }),
        fetch("/api/proxy/v1/account/plan-usage", { cache: "no-store", credentials: "include" }),
      ])

      // Process profile
      if (profileRes.ok) {
        const data: UserProfile = await profileRes.json()
        setProfile(data)
        setProfileForm({
          first_name: data.first_name || "",
          last_name: data.last_name || "",
          company_name: data.company_name || "",
          phone: data.phone ? formatPhoneNumber(data.phone) : "",
          avatar_url: data.avatar_url,
        })
        setEmailForm((prev) => ({ ...prev, newEmail: data.email }))
      }

      // Process billing
      if (billingRes.ok) {
        const billingData = await billingRes.json()
        setBillingData(billingData)
      }
    } catch (error) {
      console.error("Failed to load data:", error)
      toast({
        title: "Error",
        description: "Failed to load settings. Please try again.",
        variant: "destructive",
      })
    } finally {
      setLoading(false)
    }
  }

  async function checkout(planSlug: string) {
    setBillingLoading(true)
    try {
      const res = await fetch("/api/proxy/v1/billing/checkout", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ plan: planSlug }),
      })
      const j = await res.json()
      if (res.ok && j.url) {
        router.push(j.url)
      } else {
        toast({
          title: "Error",
          description: j.detail || "Failed to start checkout",
          variant: "destructive",
        })
      }
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to start checkout",
        variant: "destructive",
      })
    } finally {
      setBillingLoading(false)
    }
  }

  async function openBillingPortal() {
    setBillingLoading(true)
    try {
      const res = await fetch("/api/proxy/v1/billing/portal", { method: "POST" })
      const j = await res.json()
      if (res.ok && j.url) {
        router.push(j.url)
      } else {
        toast({
          title: "Error",
          description: j.detail || "Failed to open billing portal",
          variant: "destructive",
        })
      }
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to open billing portal",
        variant: "destructive",
      })
    } finally {
      setBillingLoading(false)
    }
  }

  function getPlanDisplay() {
    if (!billingData) return { planName: "Loading...", priceDisplay: "" }
    const sb = billingData.stripe_billing
    let planName = billingData.plan.plan_name || billingData.account.plan_slug
    let priceDisplay = ""

    if (sb && sb.amount != null && sb.currency && sb.interval) {
      const dollars = (sb.amount / 100).toFixed(2)
      planName = sb.nickname || planName
      priceDisplay = `$${dollars} / ${sb.interval}`
    }

    return { planName, priceDisplay }
  }

  async function saveProfile() {
    setSavingProfile(true)
    try {
      // Clean phone number for storage
      const cleanPhone = profileForm.phone.replace(/\D/g, '')
      
      const res = await fetch("/api/proxy/v1/users/me", {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          first_name: profileForm.first_name || null,
          last_name: profileForm.last_name || null,
          company_name: profileForm.company_name || null,
          phone: cleanPhone || null,
          avatar_url: profileForm.avatar_url,
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
        description: "Your profile has been updated successfully.",
      })
    } catch (error) {
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to save profile",
        variant: "destructive",
      })
    } finally {
      setSavingProfile(false)
    }
  }

  async function changePassword() {
    if (!passwordForm.currentPassword) {
      toast({ title: "Error", description: "Please enter your current password", variant: "destructive" })
      return
    }
    if (passwordForm.newPassword.length < 8) {
      toast({ title: "Error", description: "New password must be at least 8 characters", variant: "destructive" })
      return
    }
    if (passwordForm.newPassword !== passwordForm.confirmPassword) {
      toast({ title: "Error", description: "New passwords do not match", variant: "destructive" })
      return
    }

    setSavingPassword(true)
    try {
      const res = await fetch("/api/proxy/v1/users/me/password", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          current_password: passwordForm.currentPassword,
          new_password: passwordForm.newPassword,
        }),
      })

      if (!res.ok) {
        const error = await res.json()
        throw new Error(error.detail || "Failed to change password")
      }

      setPasswordForm({ currentPassword: "", newPassword: "", confirmPassword: "" })
      toast({
        title: "Password Changed",
        description: "Your password has been updated. Other sessions have been logged out.",
      })
    } catch (error) {
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to change password",
        variant: "destructive",
      })
    } finally {
      setSavingPassword(false)
    }
  }

  async function changeEmail() {
    if (!emailForm.newEmail) {
      toast({ title: "Error", description: "Please enter a new email address", variant: "destructive" })
      return
    }
    if (!emailForm.currentPassword) {
      toast({ title: "Error", description: "Please enter your current password", variant: "destructive" })
      return
    }
    if (emailForm.newEmail === profile?.email) {
      toast({ title: "Error", description: "New email must be different from current email", variant: "destructive" })
      return
    }

    setSavingEmail(true)
    try {
      const res = await fetch("/api/proxy/v1/users/me/email", {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          new_email: emailForm.newEmail,
          current_password: emailForm.currentPassword,
        }),
      })

      if (!res.ok) {
        const error = await res.json()
        throw new Error(error.detail || "Failed to change email")
      }

      const data = await res.json()
      setEmailForm((prev) => ({ ...prev, currentPassword: "" }))
      if (profile) setProfile({ ...profile, email: data.email })

      toast({ title: "Email Updated", description: "Your email address has been updated successfully." })
    } catch (error) {
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to change email",
        variant: "destructive",
      })
    } finally {
      setSavingEmail(false)
    }
  }

  function getInitials(): string {
    if (profileForm.first_name && profileForm.last_name) {
      return `${profileForm.first_name[0]}${profileForm.last_name[0]}`.toUpperCase()
    }
    if (profileForm.first_name) return profileForm.first_name[0].toUpperCase()
    if (profile?.email) return profile.email[0].toUpperCase()
    return "U"
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center">
          <Loader2 className="w-8 h-8 animate-spin text-primary mx-auto mb-4" />
          <p className="text-muted-foreground">Loading account settings...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* ========== HEADER ========== */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Account Settings</h1>
          <p className="text-muted-foreground mt-1">
            Manage your profile, security, and subscription
          </p>
        </div>
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        {/* ========== LEFT COLUMN: PROFILE & SECURITY ========== */}
        <div className="lg:col-span-2 space-y-6">
          
          {/* SECTION 1: Profile */}
          <section>
            <div className="flex items-center gap-2 mb-4">
              <div className="p-1.5 rounded-lg bg-violet-100 dark:bg-violet-900/30">
                <User className="w-4 h-4 text-violet-600" />
              </div>
              <h2 className="font-semibold text-lg">Profile Information</h2>
              <span className="text-xs text-muted-foreground ml-auto">Used on your reports</span>
            </div>
            
            <div className="bg-card border rounded-xl p-5 space-y-5">
              {/* Avatar Section */}
              <div className="flex items-start gap-5">
                <div className="flex flex-col items-center gap-2">
                  <Avatar className="w-24 h-24 border-4 border-background shadow-lg">
                    <AvatarImage src={profileForm.avatar_url || undefined} />
                    <AvatarFallback className="text-2xl bg-gradient-to-br from-violet-500 to-violet-600 text-white">
                      {getInitials()}
                    </AvatarFallback>
                  </Avatar>
                  <ImageUpload
                    label=""
                    value={profileForm.avatar_url}
                    onChange={(url) => setProfileForm({ ...profileForm, avatar_url: url })}
                    assetType="headshot"
                    aspectRatio="square"
                    helpText=""
                    className="w-24"
                  />
                </div>
                
                <div className="flex-1 space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label htmlFor="first_name" className="text-sm">First Name</Label>
                      <Input
                        id="first_name"
                        value={profileForm.first_name}
                        onChange={(e) => setProfileForm({ ...profileForm, first_name: e.target.value })}
                        placeholder="John"
                        className="mt-1.5 h-10"
                      />
                    </div>
                    <div>
                      <Label htmlFor="last_name" className="text-sm">Last Name</Label>
                      <Input
                        id="last_name"
                        value={profileForm.last_name}
                        onChange={(e) => setProfileForm({ ...profileForm, last_name: e.target.value })}
                        placeholder="Doe"
                        className="mt-1.5 h-10"
                      />
                    </div>
                  </div>
                  
                  <div>
                    <Label htmlFor="company_name" className="text-sm flex items-center gap-1.5">
                      <Building className="w-3.5 h-3.5 text-muted-foreground" /> Company
                    </Label>
                    <Input
                      id="company_name"
                      value={profileForm.company_name}
                      onChange={(e) => setProfileForm({ ...profileForm, company_name: e.target.value })}
                      placeholder="Acme Real Estate"
                      className="mt-1.5 h-10"
                    />
                  </div>
                  
                  <div>
                    <Label htmlFor="phone" className="text-sm flex items-center gap-1.5">
                      <Phone className="w-3.5 h-3.5 text-muted-foreground" /> Phone
                    </Label>
                    <Input
                      id="phone"
                      type="tel"
                      value={profileForm.phone}
                      onChange={handlePhoneChange}
                      placeholder="(555) 123-4567"
                      maxLength={14}
                      className="mt-1.5 h-10"
                    />
                  </div>
                </div>
              </div>

              {/* Email Display */}
              <div className="flex items-center gap-3 p-3 bg-muted/50 rounded-lg">
                <Mail className="w-4 h-4 text-muted-foreground" />
                <span className="text-sm">{profile?.email}</span>
                {profile?.email_verified && (
                  <Badge variant="secondary" className="ml-auto text-green-600 bg-green-50 border-green-200">
                    <CheckCircle2 className="w-3 h-3 mr-1" /> Verified
                  </Badge>
                )}
              </div>

              <Button onClick={saveProfile} disabled={savingProfile} className="w-full h-11">
                {savingProfile ? (
                  <><Loader2 className="w-4 h-4 animate-spin mr-2" /> Saving...</>
                ) : (
                  <><Save className="w-4 h-4 mr-2" /> Save Profile</>
                )}
              </Button>
            </div>
          </section>

          {/* SECTION 2: Security */}
          <section>
            <div className="flex items-center gap-2 mb-4">
              <div className="p-1.5 rounded-lg bg-amber-100 dark:bg-amber-900/30">
                <Shield className="w-4 h-4 text-amber-600" />
              </div>
              <h2 className="font-semibold text-lg">Security</h2>
            </div>
            
            <div className="grid sm:grid-cols-2 gap-4">
              {/* Password Change */}
              <div className="bg-card border rounded-xl p-5 space-y-4">
                <div className="flex items-center gap-2">
                  <Lock className="w-4 h-4 text-muted-foreground" />
                  <h3 className="font-medium">Change Password</h3>
                </div>
                
                <div className="space-y-3">
                  <div>
                    <Label className="text-sm">Current Password</Label>
                    <div className="relative mt-1">
                      <Input
                        type={showCurrentPassword ? "text" : "password"}
                        value={passwordForm.currentPassword}
                        onChange={(e) => setPasswordForm({ ...passwordForm, currentPassword: e.target.value })}
                        placeholder="••••••••"
                        className="h-10 pr-10"
                      />
                      <button
                        type="button"
                        onClick={() => setShowCurrentPassword(!showCurrentPassword)}
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                      >
                        {showCurrentPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                      </button>
                    </div>
                  </div>
                  
                  <div>
                    <Label className="text-sm">New Password</Label>
                    <div className="relative mt-1">
                      <Input
                        type={showNewPassword ? "text" : "password"}
                        value={passwordForm.newPassword}
                        onChange={(e) => setPasswordForm({ ...passwordForm, newPassword: e.target.value })}
                        placeholder="••••••••"
                        className="h-10 pr-10"
                      />
                      <button
                        type="button"
                        onClick={() => setShowNewPassword(!showNewPassword)}
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                      >
                        {showNewPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                      </button>
                    </div>
                    <p className="text-xs text-muted-foreground mt-1">Min. 8 characters</p>
                  </div>
                  
                  <div>
                    <Label className="text-sm">Confirm Password</Label>
                    <div className="relative mt-1">
                      <Input
                        type={showConfirmPassword ? "text" : "password"}
                        value={passwordForm.confirmPassword}
                        onChange={(e) => setPasswordForm({ ...passwordForm, confirmPassword: e.target.value })}
                        placeholder="••••••••"
                        className="h-10 pr-10"
                      />
                      <button
                        type="button"
                        onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                      >
                        {showConfirmPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                      </button>
                    </div>
                    {passwordForm.newPassword && passwordForm.confirmPassword && 
                     passwordForm.newPassword !== passwordForm.confirmPassword && (
                      <p className="text-xs text-destructive flex items-center gap-1 mt-1">
                        <AlertCircle className="w-3 h-3" /> Passwords don't match
                      </p>
                    )}
                  </div>
                </div>
                
                <Button onClick={changePassword} disabled={savingPassword} variant="outline" className="w-full h-10">
                  {savingPassword ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Lock className="w-4 h-4 mr-2" />}
                  {savingPassword ? "Updating..." : "Update Password"}
                </Button>
              </div>

              {/* Email Change */}
              <div className="bg-card border rounded-xl p-5 space-y-4">
                <div className="flex items-center gap-2">
                  <Mail className="w-4 h-4 text-muted-foreground" />
                  <h3 className="font-medium">Change Email</h3>
                </div>
                
                <div className="space-y-3">
                  <div className="p-2.5 bg-muted/50 rounded-lg text-sm">
                    <span className="text-muted-foreground">Current:</span> {profile?.email}
                  </div>
                  
                  <div>
                    <Label className="text-sm">New Email</Label>
                    <Input
                      type="email"
                      value={emailForm.newEmail}
                      onChange={(e) => setEmailForm({ ...emailForm, newEmail: e.target.value })}
                      placeholder="newemail@example.com"
                      className="mt-1 h-10"
                    />
                  </div>
                  
                  <div>
                    <Label className="text-sm">Your Password</Label>
                    <div className="relative mt-1">
                      <Input
                        type={showEmailPassword ? "text" : "password"}
                        value={emailForm.currentPassword}
                        onChange={(e) => setEmailForm({ ...emailForm, currentPassword: e.target.value })}
                        placeholder="Confirm with password"
                        className="h-10 pr-10"
                      />
                      <button
                        type="button"
                        onClick={() => setShowEmailPassword(!showEmailPassword)}
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                      >
                        {showEmailPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                      </button>
                    </div>
                  </div>
                </div>
                
                <Button onClick={changeEmail} disabled={savingEmail} variant="outline" className="w-full h-10">
                  {savingEmail ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Mail className="w-4 h-4 mr-2" />}
                  {savingEmail ? "Updating..." : "Update Email"}
                </Button>
              </div>
            </div>
          </section>
        </div>

        {/* ========== RIGHT COLUMN: PLAN & BILLING ========== */}
        <div className="lg:col-span-1 space-y-6">
          <section>
            <div className="flex items-center gap-2 mb-4">
              <div className="p-1.5 rounded-lg bg-emerald-100 dark:bg-emerald-900/30">
                <CreditCard className="w-4 h-4 text-emerald-600" />
              </div>
              <h2 className="font-semibold text-lg">Plan & Billing</h2>
            </div>

            {!billingData ? (
              <div className="bg-card border rounded-xl p-8 flex items-center justify-center">
                <Loader2 className="w-6 h-6 animate-spin text-muted-foreground" />
              </div>
            ) : billingData.account.account_type === "INDUSTRY_AFFILIATE" ? (
              <div className="bg-gradient-to-br from-violet-50 to-purple-50 dark:from-violet-950/30 dark:to-purple-950/30 border border-violet-200 dark:border-violet-800 rounded-xl p-5 space-y-4">
                <div className="flex items-center gap-2">
                  <Shield className="w-5 h-5 text-violet-600" />
                  <span className="font-semibold text-violet-900 dark:text-violet-100">Affiliate Plan</span>
                </div>
                <div>
                  <p className="text-2xl font-bold">{getPlanDisplay().planName}</p>
                  {getPlanDisplay().priceDisplay && (
                    <p className="text-sm text-muted-foreground">{getPlanDisplay().priceDisplay}</p>
                  )}
                </div>
                <Button onClick={openBillingPortal} disabled={billingLoading} className="w-full">
                  <CreditCard className="w-4 h-4 mr-2" />
                  {billingLoading ? "Loading..." : "Manage Billing"}
                </Button>
              </div>
            ) : (
              <div className="space-y-4">
                {/* Current Plan */}
                <div className="bg-card border rounded-xl p-5 space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-muted-foreground">Current Plan</span>
                    <Badge variant="secondary">{getPlanDisplay().planName}</Badge>
                  </div>
                  
                  <div>
                    <div className="flex items-baseline gap-2">
                      <span className="text-3xl font-bold">{billingData.usage.report_count}</span>
                      <span className="text-muted-foreground">/ {billingData.plan.monthly_report_limit}</span>
                    </div>
                    <p className="text-xs text-muted-foreground">Reports this month</p>
                    
                    {/* Usage bar */}
                    <div className="mt-3 h-2 bg-muted rounded-full overflow-hidden">
                      <div 
                        className="h-full bg-gradient-to-r from-violet-500 to-violet-600 rounded-full transition-all"
                        style={{ width: `${Math.min(100, (billingData.usage.report_count / billingData.plan.monthly_report_limit) * 100)}%` }}
                      />
                    </div>
                  </div>
                  
                  {billingData.stripe_billing && (
                    <Button onClick={openBillingPortal} variant="outline" disabled={billingLoading} className="w-full">
                      <CreditCard className="w-4 h-4 mr-2" />
                      {billingLoading ? "Loading..." : "Manage Billing"}
                    </Button>
                  )}
                </div>

                {/* Available Plans */}
                <div className="space-y-3">
                  <p className="text-sm font-medium text-muted-foreground">Available Plans</p>
                  {plans.map((plan) => (
                    <div 
                      key={plan.slug} 
                      className={`bg-card border rounded-xl p-4 ${plan.popular ? 'border-violet-300 ring-1 ring-violet-200' : ''}`}
                    >
                      <div className="flex items-center justify-between mb-2">
                        <span className="font-semibold">{plan.name}</span>
                        {plan.popular && <Badge className="bg-violet-100 text-violet-700 border-0">Popular</Badge>}
                      </div>
                      <div className="mb-3">
                        <span className="text-2xl font-bold">{plan.price}</span>
                        <span className="text-muted-foreground text-sm">{plan.period}</span>
                      </div>
                      <ul className="space-y-1.5 mb-4">
                        {plan.features.slice(0, 2).map((f, i) => (
                          <li key={i} className="flex items-center gap-2 text-xs text-muted-foreground">
                            <Check className="w-3 h-3 text-emerald-500" /> {f}
                          </li>
                        ))}
                      </ul>
                      <Button
                        onClick={() => checkout(plan.slug)}
                        disabled={billingLoading || billingData?.account.plan_slug === plan.slug}
                        variant={billingData?.account.plan_slug === plan.slug ? "secondary" : plan.popular ? "default" : "outline"}
                        className="w-full h-9 text-sm"
                      >
                        {billingData?.account.plan_slug === plan.slug ? "Current Plan" : "Upgrade"}
                      </Button>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </section>
        </div>
      </div>
    </div>
  )
}
