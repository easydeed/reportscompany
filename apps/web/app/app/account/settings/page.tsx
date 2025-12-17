"use client"

import { useEffect, useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Separator } from "@/components/ui/separator"
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

/**
 * Account Settings Page
 *
 * Tabs:
 * - Profile: Edit personal information (name, company, phone, avatar)
 * - Security: Change password, update email
 * - Plan & Billing: View and manage subscription
 */
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

  useEffect(() => {
    loadProfile()
    loadBillingData()
  }, [])

  async function loadProfile() {
    setLoading(true)
    try {
      const res = await fetch("/api/proxy/v1/users/me", { cache: "no-store" })

      if (res.ok) {
        const data: UserProfile = await res.json()
        setProfile(data)
        setProfileForm({
          first_name: data.first_name || "",
          last_name: data.last_name || "",
          company_name: data.company_name || "",
          phone: data.phone || "",
          avatar_url: data.avatar_url,
        })
        setEmailForm((prev) => ({ ...prev, newEmail: data.email }))
      } else {
        throw new Error("Failed to load profile")
      }
    } catch (error) {
      console.error("Failed to load profile:", error)
      toast({
        title: "Error",
        description: "Failed to load profile. Please try again.",
        variant: "destructive",
      })
    } finally {
      setLoading(false)
    }
  }

  async function loadBillingData() {
    try {
      const res = await fetch("/api/proxy/v1/account/plan-usage", { cache: "no-store" })
      if (res.ok) {
        const data = await res.json()
        setBillingData(data)
      }
    } catch (error) {
      console.error("Failed to load billing data:", error)
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

  // Helper to format price display from Stripe billing data
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
      const res = await fetch("/api/proxy/v1/users/me", {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          first_name: profileForm.first_name || null,
          last_name: profileForm.last_name || null,
          company_name: profileForm.company_name || null,
          phone: profileForm.phone || null,
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
    // Validation
    if (!passwordForm.currentPassword) {
      toast({
        title: "Error",
        description: "Please enter your current password",
        variant: "destructive",
      })
      return
    }

    if (passwordForm.newPassword.length < 8) {
      toast({
        title: "Error",
        description: "New password must be at least 8 characters",
        variant: "destructive",
      })
      return
    }

    if (passwordForm.newPassword !== passwordForm.confirmPassword) {
      toast({
        title: "Error",
        description: "New passwords do not match",
        variant: "destructive",
      })
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

      // Clear form
      setPasswordForm({
        currentPassword: "",
        newPassword: "",
        confirmPassword: "",
      })

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
    // Validation
    if (!emailForm.newEmail) {
      toast({
        title: "Error",
        description: "Please enter a new email address",
        variant: "destructive",
      })
      return
    }

    if (!emailForm.currentPassword) {
      toast({
        title: "Error",
        description: "Please enter your current password",
        variant: "destructive",
      })
      return
    }

    if (emailForm.newEmail === profile?.email) {
      toast({
        title: "Error",
        description: "New email must be different from current email",
        variant: "destructive",
      })
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

      // Clear password field and update profile
      setEmailForm((prev) => ({ ...prev, currentPassword: "" }))
      if (profile) {
        setProfile({ ...profile, email: data.email })
      }

      toast({
        title: "Email Updated",
        description: "Your email address has been updated successfully.",
      })
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

  // Get user initials for avatar fallback
  function getInitials(): string {
    if (profileForm.first_name && profileForm.last_name) {
      return `${profileForm.first_name[0]}${profileForm.last_name[0]}`.toUpperCase()
    }
    if (profileForm.first_name) {
      return profileForm.first_name[0].toUpperCase()
    }
    if (profile?.email) {
      return profile.email[0].toUpperCase()
    }
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
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Account Settings</h1>
        <p className="text-muted-foreground mt-1">
          Manage your account information and security settings
        </p>
      </div>

      {/* Tabs */}
      <Tabs defaultValue="profile" className="space-y-6">
        <TabsList className="grid w-full grid-cols-3 max-w-lg h-14 p-1.5 bg-muted/60 border border-border/50 rounded-xl shadow-sm">
          <TabsTrigger value="profile" className="gap-2 h-full rounded-lg text-sm font-medium data-[state=active]:bg-background data-[state=active]:shadow-md transition-all duration-200">
            <User className="w-4 h-4" />
            <span>Profile</span>
          </TabsTrigger>
          <TabsTrigger value="security" className="gap-2 h-full rounded-lg text-sm font-medium data-[state=active]:bg-background data-[state=active]:shadow-md transition-all duration-200">
            <Lock className="w-4 h-4" />
            <span>Security</span>
          </TabsTrigger>
          <TabsTrigger value="billing" className="gap-2 h-full rounded-lg text-sm font-medium data-[state=active]:bg-background data-[state=active]:shadow-md transition-all duration-200">
            <CreditCard className="w-4 h-4" />
            <span>Plan & Billing</span>
          </TabsTrigger>
        </TabsList>

        {/* Profile Tab */}
        <TabsContent value="profile" className="space-y-6">
          <div className="grid gap-6 lg:grid-cols-3">
            {/* Avatar Section */}
            <Card className="lg:col-span-1">
              <CardHeader>
                <CardTitle>Profile Picture</CardTitle>
                <CardDescription>
                  Upload a photo to personalize your account
                </CardDescription>
              </CardHeader>
              <CardContent className="flex flex-col items-center gap-4">
                <Avatar className="w-32 h-32">
                  <AvatarImage src={profileForm.avatar_url || undefined} />
                  <AvatarFallback className="text-2xl bg-primary text-primary-foreground">
                    {getInitials()}
                  </AvatarFallback>
                </Avatar>
                <ImageUpload
                  label=""
                  value={profileForm.avatar_url}
                  onChange={(url) => setProfileForm({ ...profileForm, avatar_url: url })}
                  assetType="headshot"
                  aspectRatio="square"
                  helpText="Square format recommended (e.g., 400x400px)"
                />
              </CardContent>
            </Card>

            {/* Profile Form */}
            <Card className="lg:col-span-2">
              <CardHeader>
                <CardTitle>Personal Information</CardTitle>
                <CardDescription>
                  Update your personal details
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="first_name">First Name</Label>
                    <Input
                      id="first_name"
                      value={profileForm.first_name}
                      onChange={(e) =>
                        setProfileForm({ ...profileForm, first_name: e.target.value })
                      }
                      placeholder="John"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="last_name">Last Name</Label>
                    <Input
                      id="last_name"
                      value={profileForm.last_name}
                      onChange={(e) =>
                        setProfileForm({ ...profileForm, last_name: e.target.value })
                      }
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
                    value={profileForm.company_name}
                    onChange={(e) =>
                      setProfileForm({ ...profileForm, company_name: e.target.value })
                    }
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
                    value={profileForm.phone}
                    onChange={(e) =>
                      setProfileForm({ ...profileForm, phone: e.target.value })
                    }
                    placeholder="(555) 123-4567"
                  />
                </div>

                <Separator />

                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Mail className="w-4 h-4" />
                  <span>Email: {profile?.email}</span>
                  {profile?.email_verified && (
                    <span className="flex items-center gap-1 text-green-600">
                      <CheckCircle2 className="w-3 h-3" />
                      Verified
                    </span>
                  )}
                </div>

                <Button
                  onClick={saveProfile}
                  disabled={savingProfile}
                  className="w-full gap-2"
                >
                  {savingProfile ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <Save className="w-4 h-4" />
                  )}
                  {savingProfile ? "Saving..." : "Save Changes"}
                </Button>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Security Tab */}
        <TabsContent value="security" className="space-y-6">
          <div className="grid gap-6 lg:grid-cols-2">
            {/* Password Change */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Lock className="w-5 h-5" />
                  Change Password
                </CardTitle>
                <CardDescription>
                  Update your password to keep your account secure. Other sessions will be logged out.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="currentPassword">Current Password</Label>
                  <div className="relative">
                    <Input
                      id="currentPassword"
                      type={showCurrentPassword ? "text" : "password"}
                      value={passwordForm.currentPassword}
                      onChange={(e) =>
                        setPasswordForm({ ...passwordForm, currentPassword: e.target.value })
                      }
                      placeholder="Enter current password"
                    />
                    <button
                      type="button"
                      onClick={() => setShowCurrentPassword(!showCurrentPassword)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                    >
                      {showCurrentPassword ? (
                        <EyeOff className="w-4 h-4" />
                      ) : (
                        <Eye className="w-4 h-4" />
                      )}
                    </button>
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="newPassword">New Password</Label>
                  <div className="relative">
                    <Input
                      id="newPassword"
                      type={showNewPassword ? "text" : "password"}
                      value={passwordForm.newPassword}
                      onChange={(e) =>
                        setPasswordForm({ ...passwordForm, newPassword: e.target.value })
                      }
                      placeholder="Enter new password"
                    />
                    <button
                      type="button"
                      onClick={() => setShowNewPassword(!showNewPassword)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                    >
                      {showNewPassword ? (
                        <EyeOff className="w-4 h-4" />
                      ) : (
                        <Eye className="w-4 h-4" />
                      )}
                    </button>
                  </div>
                  <p className="text-xs text-muted-foreground">
                    Minimum 8 characters
                  </p>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="confirmPassword">Confirm New Password</Label>
                  <div className="relative">
                    <Input
                      id="confirmPassword"
                      type={showConfirmPassword ? "text" : "password"}
                      value={passwordForm.confirmPassword}
                      onChange={(e) =>
                        setPasswordForm({ ...passwordForm, confirmPassword: e.target.value })
                      }
                      placeholder="Confirm new password"
                    />
                    <button
                      type="button"
                      onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                    >
                      {showConfirmPassword ? (
                        <EyeOff className="w-4 h-4" />
                      ) : (
                        <Eye className="w-4 h-4" />
                      )}
                    </button>
                  </div>
                  {passwordForm.newPassword &&
                    passwordForm.confirmPassword &&
                    passwordForm.newPassword !== passwordForm.confirmPassword && (
                      <p className="text-xs text-destructive flex items-center gap-1">
                        <AlertCircle className="w-3 h-3" />
                        Passwords do not match
                      </p>
                    )}
                </div>

                <Button
                  onClick={changePassword}
                  disabled={savingPassword}
                  className="w-full gap-2"
                >
                  {savingPassword ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <Lock className="w-4 h-4" />
                  )}
                  {savingPassword ? "Updating..." : "Update Password"}
                </Button>
              </CardContent>
            </Card>

            {/* Email Change */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Mail className="w-5 h-5" />
                  Change Email
                </CardTitle>
                <CardDescription>
                  Update your email address. You will need to enter your current password to confirm.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label>Current Email</Label>
                  <div className="flex items-center gap-2 p-3 bg-muted rounded-md">
                    <Mail className="w-4 h-4 text-muted-foreground" />
                    <span className="text-sm">{profile?.email}</span>
                    {profile?.email_verified && (
                      <span className="flex items-center gap-1 text-xs text-green-600 ml-auto">
                        <CheckCircle2 className="w-3 h-3" />
                        Verified
                      </span>
                    )}
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="newEmail">New Email Address</Label>
                  <Input
                    id="newEmail"
                    type="email"
                    value={emailForm.newEmail}
                    onChange={(e) =>
                      setEmailForm({ ...emailForm, newEmail: e.target.value })
                    }
                    placeholder="newemail@example.com"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="emailPassword">Current Password</Label>
                  <div className="relative">
                    <Input
                      id="emailPassword"
                      type={showEmailPassword ? "text" : "password"}
                      value={emailForm.currentPassword}
                      onChange={(e) =>
                        setEmailForm({ ...emailForm, currentPassword: e.target.value })
                      }
                      placeholder="Enter your password to confirm"
                    />
                    <button
                      type="button"
                      onClick={() => setShowEmailPassword(!showEmailPassword)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                    >
                      {showEmailPassword ? (
                        <EyeOff className="w-4 h-4" />
                      ) : (
                        <Eye className="w-4 h-4" />
                      )}
                    </button>
                  </div>
                </div>

                <Button
                  onClick={changeEmail}
                  disabled={savingEmail}
                  className="w-full gap-2"
                >
                  {savingEmail ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <Mail className="w-4 h-4" />
                  )}
                  {savingEmail ? "Updating..." : "Update Email"}
                </Button>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Plan & Billing Tab */}
        <TabsContent value="billing" className="space-y-6">
          {!billingData ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="w-6 h-6 animate-spin text-muted-foreground" />
            </div>
          ) : billingData.account.account_type === "INDUSTRY_AFFILIATE" ? (
            // Affiliate billing UI
            <Card className="border-purple-200 bg-purple-50/30 dark:bg-purple-950/20">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Shield className="w-5 h-5 text-purple-600" />
                  Your Affiliate Plan
                </CardTitle>
                <CardDescription>
                  Manage or cancel your affiliate subscription in the billing portal.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <p className="text-sm text-muted-foreground mb-1">Current plan</p>
                  <p className="text-lg font-semibold">{getPlanDisplay().planName}</p>
                  {getPlanDisplay().priceDisplay && (
                    <p className="text-sm text-muted-foreground mt-1">
                      Billing: <strong>{getPlanDisplay().priceDisplay}</strong>
                    </p>
                  )}
                  {billingData.account.billing_status && (
                    <p className="text-xs text-muted-foreground mt-1">
                      Status: <span className="capitalize">{billingData.account.billing_status}</span>
                    </p>
                  )}
                </div>
                <Separator />
                <Button onClick={openBillingPortal} disabled={billingLoading} className="gap-2">
                  <CreditCard className="w-4 h-4" />
                  {billingLoading ? "Loading..." : "Manage Billing"}
                </Button>
                <p className="text-xs text-muted-foreground">
                  Update payment method or cancel subscription via Stripe.
                </p>
              </CardContent>
            </Card>
          ) : (
            // Agent billing UI
            <div className="space-y-6">
              {/* Current Plan Card */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <CreditCard className="w-5 h-5" />
                    Current Plan
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex items-center gap-6">
                    <div className="flex-1">
                      <p className="text-sm text-muted-foreground">Plan</p>
                      <p className="text-lg font-semibold">{getPlanDisplay().planName}</p>
                      {getPlanDisplay().priceDisplay && (
                        <p className="text-sm text-muted-foreground">{getPlanDisplay().priceDisplay}</p>
                      )}
                      {billingData.account.billing_status && (
                        <p className="text-xs text-muted-foreground mt-1">
                          Status: <span className="capitalize">{billingData.account.billing_status}</span>
                        </p>
                      )}
                    </div>
                    <div className="flex-1">
                      <p className="text-sm text-muted-foreground">Usage</p>
                      <p className="text-lg font-semibold">
                        {billingData.usage.report_count} / {billingData.plan.monthly_report_limit} reports
                      </p>
                      <p className="text-xs text-muted-foreground">This month</p>
                    </div>
                  </div>
                  {billingData.stripe_billing && (
                    <Button onClick={openBillingPortal} variant="outline" disabled={billingLoading} className="gap-2">
                      <CreditCard className="w-4 h-4" />
                      {billingLoading ? "Loading..." : "Manage Billing"}
                    </Button>
                  )}
                </CardContent>
              </Card>

              {/* Available Plans */}
              <div>
                <h3 className="text-lg font-semibold mb-4">Available Plans</h3>
                <div className="grid gap-4 md:grid-cols-2">
                  {plans.map((plan) => (
                    <Card key={plan.slug} className={plan.popular ? "border-primary shadow-md" : ""}>
                      <CardHeader className="pb-3">
                        {plan.popular && (
                          <Badge className="w-fit mb-2" variant="default">
                            Most Popular
                          </Badge>
                        )}
                        <CardTitle className="text-lg">{plan.name}</CardTitle>
                        <CardDescription>{plan.description}</CardDescription>
                      </CardHeader>
                      <CardContent className="space-y-4">
                        <div>
                          <span className="text-3xl font-bold">{plan.price}</span>
                          <span className="text-muted-foreground">{plan.period}</span>
                        </div>

                        <ul className="space-y-2">
                          {plan.features.map((feature, i) => (
                            <li key={i} className="flex items-start gap-2 text-sm">
                              <Check className="w-4 h-4 text-primary shrink-0 mt-0.5" />
                              <span>{feature}</span>
                            </li>
                          ))}
                        </ul>

                        <Button
                          onClick={() => checkout(plan.slug)}
                          disabled={billingLoading || billingData?.account.plan_slug === plan.slug}
                          className="w-full"
                          variant={plan.popular ? "default" : "outline"}
                        >
                          {billingData?.account.plan_slug === plan.slug ? "Current Plan" : "Choose " + plan.name}
                        </Button>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </div>
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  )
}
