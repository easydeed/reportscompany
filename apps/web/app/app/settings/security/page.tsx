"use client"

import { useEffect, useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import {
  Mail,
  Lock,
  ChevronRight,
  Loader2,
  AlertTriangle,
  Eye,
  EyeOff,
  CheckCircle2,
  AlertCircle,
  Shield,
  KeyRound,
  Trash2,
} from "lucide-react"
import { useToast } from "@/components/ui/use-toast"

type UserProfile = {
  email: string
  email_verified: boolean
  password_changed_at?: string
}

export default function SecurityPage() {
  const [loading, setLoading] = useState(true)
  const { toast } = useToast()

  const [profile, setProfile] = useState<UserProfile | null>(null)

  // Email change modal
  const [emailModalOpen, setEmailModalOpen] = useState(false)
  const [newEmail, setNewEmail] = useState("")
  const [emailPassword, setEmailPassword] = useState("")
  const [showEmailPassword, setShowEmailPassword] = useState(false)
  const [savingEmail, setSavingEmail] = useState(false)

  // Password change modal
  const [passwordModalOpen, setPasswordModalOpen] = useState(false)
  const [currentPassword, setCurrentPassword] = useState("")
  const [newPassword, setNewPassword] = useState("")
  const [confirmPassword, setConfirmPassword] = useState("")
  const [showCurrentPassword, setShowCurrentPassword] = useState(false)
  const [showNewPassword, setShowNewPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)
  const [savingPassword, setSavingPassword] = useState(false)

  // Delete account modal
  const [deleteModalOpen, setDeleteModalOpen] = useState(false)
  const [deleteConfirmText, setDeleteConfirmText] = useState("")
  const [deleting, setDeleting] = useState(false)

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
        const data = await res.json()
        setProfile({
          email: data.email,
          email_verified: data.email_verified,
          password_changed_at: data.password_changed_at,
        })
        setNewEmail(data.email)
      }
    } catch (error) {
      console.error("Failed to load profile:", error)
    } finally {
      setLoading(false)
    }
  }

  async function changeEmail() {
    if (!newEmail || !newEmail.includes("@")) {
      toast({ title: "Error", description: "Please enter a valid email address", variant: "destructive" })
      return
    }
    if (!emailPassword) {
      toast({ title: "Error", description: "Please enter your password", variant: "destructive" })
      return
    }
    if (newEmail === profile?.email) {
      toast({ title: "Error", description: "New email must be different", variant: "destructive" })
      return
    }

    setSavingEmail(true)
    try {
      const res = await fetch("/api/proxy/v1/users/me/email", {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          new_email: newEmail,
          current_password: emailPassword,
        }),
      })

      if (!res.ok) {
        const error = await res.json()
        throw new Error(error.detail || "Failed to change email")
      }

      const data = await res.json()
      setProfile((prev) => (prev ? { ...prev, email: data.email } : null))
      setEmailModalOpen(false)
      setEmailPassword("")

      toast({ title: "Email Updated", description: "Your email address has been changed." })
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

  async function changePassword() {
    if (!currentPassword) {
      toast({ title: "Error", description: "Please enter your current password", variant: "destructive" })
      return
    }
    if (newPassword.length < 8) {
      toast({ title: "Error", description: "New password must be at least 8 characters", variant: "destructive" })
      return
    }
    if (newPassword !== confirmPassword) {
      toast({ title: "Error", description: "Passwords do not match", variant: "destructive" })
      return
    }

    setSavingPassword(true)
    try {
      const res = await fetch("/api/proxy/v1/users/me/password", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          current_password: currentPassword,
          new_password: newPassword,
        }),
      })

      if (!res.ok) {
        const error = await res.json()
        throw new Error(error.detail || "Failed to change password")
      }

      setPasswordModalOpen(false)
      setCurrentPassword("")
      setNewPassword("")
      setConfirmPassword("")

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

  async function deleteAccount() {
    if (deleteConfirmText !== "DELETE") {
      toast({ title: "Error", description: "Please type DELETE to confirm", variant: "destructive" })
      return
    }

    setDeleting(true)
    try {
      const res = await fetch("/api/proxy/v1/users/me", {
        method: "DELETE",
      })

      if (!res.ok) {
        const error = await res.json()
        throw new Error(error.detail || "Failed to delete account")
      }

      // Redirect to logout
      window.location.href = "/login"
    } catch (error) {
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to delete account",
        variant: "destructive",
      })
      setDeleting(false)
    }
  }

  function getPasswordLastChanged(): string {
    if (!profile?.password_changed_at) return "Never changed"
    const date = new Date(profile.password_changed_at)
    const now = new Date()
    const diffDays = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60 * 24))
    if (diffDays === 0) return "Changed today"
    if (diffDays === 1) return "Changed yesterday"
    if (diffDays < 30) return `Changed ${diffDays} days ago`
    if (diffDays < 60) return "Changed about a month ago"
    const months = Math.floor(diffDays / 30)
    return `Changed ${months} months ago`
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-24">
        <div className="text-center">
          <Loader2 className="w-8 h-8 animate-spin text-indigo-600 mx-auto mb-4" />
          <p className="text-muted-foreground text-sm">Loading security settings...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-3xl">
      {/* Page Header */}
      <div className="mb-6">
        <h1 className="text-xl font-semibold tracking-tight text-foreground">Security</h1>
        <p className="text-[13px] text-muted-foreground mt-0.5">
          Manage your account security and authentication.
        </p>
      </div>

      <div className="space-y-4">
        {/* Email & Password Card */}
        <div className="bg-card border border-border rounded-xl shadow-[var(--shadow-card)] overflow-hidden">
          <div className="divide-y divide-border">
            {/* Email Row */}
            <div className="p-5 flex items-center justify-between gap-4">
              <div className="flex items-center gap-4 min-w-0">
                <div className="w-10 h-10 rounded-lg bg-indigo-50 flex items-center justify-center flex-shrink-0">
                  <Mail className="w-5 h-5 text-indigo-600" />
                </div>
                <div className="min-w-0">
                  <div className="flex items-center gap-2">
                    <h3 className="text-sm font-medium text-foreground">Email Address</h3>
                    {profile?.email_verified && (
                      <Badge variant="secondary" className="text-emerald-600 bg-emerald-50 border-emerald-200 text-[10px] px-1.5 py-0">
                        <CheckCircle2 className="w-3 h-3 mr-0.5" />
                        Verified
                      </Badge>
                    )}
                  </div>
                  <p className="text-sm text-muted-foreground truncate">{profile?.email}</p>
                </div>
              </div>

              <Dialog open={emailModalOpen} onOpenChange={setEmailModalOpen}>
                <DialogTrigger asChild>
                  <Button variant="ghost" size="sm" className="text-indigo-600 hover:text-indigo-700 hover:bg-indigo-50 flex-shrink-0">
                    Change
                    <ChevronRight className="w-4 h-4 ml-1" />
                  </Button>
                </DialogTrigger>
                <DialogContent>
                  <DialogHeader>
                    <DialogTitle>Change Email Address</DialogTitle>
                    <DialogDescription>
                      Enter your new email and confirm with your password.
                    </DialogDescription>
                  </DialogHeader>
                  <div className="space-y-4 py-4">
                    <div className="space-y-1.5">
                      <Label className="text-xs font-medium text-muted-foreground">New Email</Label>
                      <Input
                        type="email"
                        value={newEmail}
                        onChange={(e) => setNewEmail(e.target.value)}
                        placeholder="newemail@example.com"
                        className="h-9"
                      />
                    </div>
                    <div className="space-y-1.5">
                      <Label className="text-xs font-medium text-muted-foreground">Current Password</Label>
                      <div className="relative">
                        <Input
                          type={showEmailPassword ? "text" : "password"}
                          value={emailPassword}
                          onChange={(e) => setEmailPassword(e.target.value)}
                          placeholder="••••••••"
                          className="h-9 pr-10"
                        />
                        <button
                          type="button"
                          onClick={() => setShowEmailPassword(!showEmailPassword)}
                          className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                        >
                          {showEmailPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                        </button>
                      </div>
                      <p className="text-[11px] text-muted-foreground">Required to confirm this change</p>
                    </div>
                  </div>
                  <DialogFooter>
                    <Button variant="outline" size="sm" onClick={() => setEmailModalOpen(false)}>
                      Cancel
                    </Button>
                    <Button size="sm" onClick={changeEmail} disabled={savingEmail}>
                      {savingEmail && <Loader2 className="w-4 h-4 animate-spin mr-1.5" />}
                      Update Email
                    </Button>
                  </DialogFooter>
                </DialogContent>
              </Dialog>
            </div>

            {/* Password Row */}
            <div className="p-5 flex items-center justify-between gap-4">
              <div className="flex items-center gap-4">
                <div className="w-10 h-10 rounded-lg bg-slate-100 flex items-center justify-center flex-shrink-0">
                  <KeyRound className="w-5 h-5 text-slate-600" />
                </div>
                <div>
                  <h3 className="text-sm font-medium text-foreground">Password</h3>
                  <p className="text-sm text-muted-foreground">{getPasswordLastChanged()}</p>
                </div>
              </div>

              <Dialog open={passwordModalOpen} onOpenChange={setPasswordModalOpen}>
                <DialogTrigger asChild>
                  <Button variant="ghost" size="sm" className="text-indigo-600 hover:text-indigo-700 hover:bg-indigo-50 flex-shrink-0">
                    Change
                    <ChevronRight className="w-4 h-4 ml-1" />
                  </Button>
                </DialogTrigger>
                <DialogContent>
                  <DialogHeader>
                    <DialogTitle>Change Password</DialogTitle>
                    <DialogDescription>
                      Enter your current password and choose a new one.
                    </DialogDescription>
                  </DialogHeader>
                  <div className="space-y-4 py-4">
                    <div className="space-y-1.5">
                      <Label className="text-xs font-medium text-muted-foreground">Current Password</Label>
                      <div className="relative">
                        <Input
                          type={showCurrentPassword ? "text" : "password"}
                          value={currentPassword}
                          onChange={(e) => setCurrentPassword(e.target.value)}
                          placeholder="••••••••"
                          className="h-9 pr-10"
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
                    <div className="space-y-1.5">
                      <Label className="text-xs font-medium text-muted-foreground">New Password</Label>
                      <div className="relative">
                        <Input
                          type={showNewPassword ? "text" : "password"}
                          value={newPassword}
                          onChange={(e) => setNewPassword(e.target.value)}
                          placeholder="••••••••"
                          className="h-9 pr-10"
                        />
                        <button
                          type="button"
                          onClick={() => setShowNewPassword(!showNewPassword)}
                          className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                        >
                          {showNewPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                        </button>
                      </div>
                      <p className="text-[11px] text-muted-foreground">At least 8 characters</p>
                    </div>
                    <div className="space-y-1.5">
                      <Label className="text-xs font-medium text-muted-foreground">Confirm New Password</Label>
                      <div className="relative">
                        <Input
                          type={showConfirmPassword ? "text" : "password"}
                          value={confirmPassword}
                          onChange={(e) => setConfirmPassword(e.target.value)}
                          placeholder="••••••••"
                          className="h-9 pr-10"
                        />
                        <button
                          type="button"
                          onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                          className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                        >
                          {showConfirmPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                        </button>
                      </div>
                      {newPassword && confirmPassword && newPassword !== confirmPassword && (
                        <p className="text-[11px] text-destructive flex items-center gap-1">
                          <AlertCircle className="w-3 h-3" />
                          Passwords don't match
                        </p>
                      )}
                    </div>
                  </div>
                  <DialogFooter>
                    <Button variant="outline" size="sm" onClick={() => setPasswordModalOpen(false)}>
                      Cancel
                    </Button>
                    <Button size="sm" onClick={changePassword} disabled={savingPassword}>
                      {savingPassword && <Loader2 className="w-4 h-4 animate-spin mr-1.5" />}
                      Update Password
                    </Button>
                  </DialogFooter>
                </DialogContent>
              </Dialog>
            </div>
          </div>
        </div>

        {/* Danger Zone Card */}
        <div className="bg-card border border-red-200 rounded-xl shadow-[var(--shadow-card)] overflow-hidden">
          <div className="px-5 py-3 border-b border-red-100 bg-red-50/50">
            <h3 className="text-[13px] font-semibold text-red-700 uppercase tracking-wide flex items-center gap-2">
              <Shield className="w-4 h-4" />
              Danger Zone
            </h3>
          </div>
          <div className="p-5">
            <div className="flex items-center justify-between gap-4">
              <div className="flex items-center gap-4">
                <div className="w-10 h-10 rounded-lg bg-red-50 flex items-center justify-center flex-shrink-0">
                  <Trash2 className="w-5 h-5 text-red-600" />
                </div>
                <div>
                  <h3 className="text-sm font-medium text-foreground">Delete Account</h3>
                  <p className="text-sm text-muted-foreground">
                    Permanently delete your account and all data.
                  </p>
                </div>
              </div>

              <Dialog open={deleteModalOpen} onOpenChange={setDeleteModalOpen}>
                <DialogTrigger asChild>
                  <Button variant="destructive" size="sm">
                    Delete Account
                  </Button>
                </DialogTrigger>
                <DialogContent>
                  <DialogHeader>
                    <DialogTitle className="flex items-center gap-2 text-red-600">
                      <AlertTriangle className="w-5 h-5" />
                      Delete Account
                    </DialogTitle>
                    <DialogDescription>
                      This will permanently delete your account, all reports, schedules, and data. This cannot be undone.
                    </DialogDescription>
                  </DialogHeader>
                  <div className="py-4">
                    <div className="space-y-1.5">
                      <Label className="text-xs font-medium text-muted-foreground">
                        Type DELETE to confirm
                      </Label>
                      <Input
                        value={deleteConfirmText}
                        onChange={(e) => setDeleteConfirmText(e.target.value)}
                        placeholder="DELETE"
                        className="h-9 font-mono"
                      />
                    </div>
                  </div>
                  <DialogFooter>
                    <Button variant="outline" size="sm" onClick={() => setDeleteModalOpen(false)}>
                      Cancel
                    </Button>
                    <Button
                      variant="destructive"
                      size="sm"
                      onClick={deleteAccount}
                      disabled={deleting || deleteConfirmText !== "DELETE"}
                    >
                      {deleting && <Loader2 className="w-4 h-4 animate-spin mr-1.5" />}
                      Delete Account
                    </Button>
                  </DialogFooter>
                </DialogContent>
              </Dialog>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
