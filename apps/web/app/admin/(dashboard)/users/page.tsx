"use client"

import { useState, useEffect } from "react"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  Users,
  Search,
  Mail,
  UserCheck,
  UserX,
  Loader2,
  RefreshCw,
  CheckCircle,
  XCircle,
  Shield,
  ShieldOff,
  Send,
  KeyRound,
} from "lucide-react"

interface User {
  user_id: string
  email: string
  first_name: string | null
  last_name: string | null
  is_active: boolean
  email_verified: boolean
  created_at: string
  last_login_at: string | null
  account_id: string
  account_name: string
  account_type: string
  role: string  // Tenant role from account_users (OWNER/ADMIN/MEMBER)
  is_platform_admin: boolean  // Platform admin flag from users table
}

export default function UsersPage() {
  const [users, setUsers] = useState<User[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState("")
  const [roleFilter, setRoleFilter] = useState<string>("all")
  const [statusFilter, setStatusFilter] = useState<string>("all")
  const [total, setTotal] = useState(0)
  const [actionLoading, setActionLoading] = useState<string | null>(null)

  useEffect(() => {
    fetchUsers()
  }, [search, roleFilter, statusFilter])

  async function fetchUsers() {
    setLoading(true)
    try {
      const params = new URLSearchParams()
      if (search) params.set("search", search)
      if (roleFilter !== "all") params.set("role", roleFilter)
      if (statusFilter === "active") params.set("is_active", "true")
      if (statusFilter === "inactive") params.set("is_active", "false")

      const res = await fetch(`/api/v1/admin/users?${params.toString()}`, {
        credentials: "include",
      })
      if (res.ok) {
        const data = await res.json()
        setUsers(data.users || [])
        setTotal(data.total || 0)
      }
    } catch (error) {
      console.error("Failed to fetch users:", error)
    } finally {
      setLoading(false)
    }
  }

  async function updateUser(userId: string, updates: { is_active?: boolean; email_verified?: boolean; is_platform_admin?: boolean }) {
    setActionLoading(userId)
    try {
      const params = new URLSearchParams()
      if (updates.is_active !== undefined) params.set("is_active", String(updates.is_active))
      if (updates.email_verified !== undefined) params.set("email_verified", String(updates.email_verified))
      if (updates.is_platform_admin !== undefined) params.set("is_platform_admin", String(updates.is_platform_admin))

      const res = await fetch(`/api/v1/admin/users/${userId}?${params.toString()}`, {
        method: "PATCH",
        credentials: "include",
      })
      if (res.ok) {
        fetchUsers()
      }
    } catch (error) {
      console.error("Failed to update user:", error)
    } finally {
      setActionLoading(null)
    }
  }

  async function resendInvite(userId: string) {
    setActionLoading(userId)
    try {
      const res = await fetch(`/api/v1/admin/users/${userId}/resend-invite`, {
        method: "POST",
        credentials: "include",
      })
      if (res.ok) {
        alert("Invite sent successfully!")
      }
    } catch (error) {
      console.error("Failed to resend invite:", error)
    } finally {
      setActionLoading(null)
    }
  }

  async function forcePasswordReset(userId: string, email: string) {
    if (!confirm(`Send password reset email to ${email}? They will receive a link to set a new password.`)) {
      return
    }
    setActionLoading(userId)
    try {
      const res = await fetch(`/api/v1/admin/users/${userId}/force-password-reset`, {
        method: "POST",
        credentials: "include",
      })
      if (res.ok) {
        const data = await res.json()
        alert(`Password reset email sent to ${email}!\n\nReset URL: ${data.reset_url}`)
      } else {
        alert("Failed to send password reset email")
      }
    } catch (error) {
      console.error("Failed to send password reset:", error)
      alert("Failed to send password reset email")
    } finally {
      setActionLoading(null)
    }
  }

  const formatDate = (date: string | null) => {
    if (!date) return "-"
    return new Date(date).toLocaleDateString()
  }

  const formatTimeAgo = (date: string | null) => {
    if (!date) return "Never"
    const d = new Date(date)
    const now = new Date()
    const diff = now.getTime() - d.getTime()
    const days = Math.floor(diff / (1000 * 60 * 60 * 24))
    if (days === 0) return "Today"
    if (days === 1) return "Yesterday"
    if (days < 7) return `${days} days ago`
    if (days < 30) return `${Math.floor(days / 7)} weeks ago`
    return `${Math.floor(days / 30)} months ago`
  }

  // Calculate stats
  const activeUsers = users.filter(u => u.is_active).length
  const verifiedUsers = users.filter(u => u.email_verified).length
  const platformAdmins = users.filter(u => u.is_platform_admin).length
  const tenantAdmins = users.filter(u => u.role === 'ADMIN' || u.role === 'OWNER').length

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-slate-900">Users</h1>
          <p className="text-slate-500 mt-1">Manage all users across the platform</p>
        </div>
        <Badge variant="outline" className="border-slate-300 text-slate-700 text-lg px-4 py-2">
          <Users className="h-4 w-4 mr-2" />
          {total} total
        </Badge>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="bg-white border-slate-200 shadow-sm">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">Total Users</p>
                <p className="text-2xl font-bold text-slate-900">{total}</p>
              </div>
              <Users className="h-8 w-8 text-slate-200" />
            </div>
          </CardContent>
        </Card>
        <Card className="bg-white border-slate-200 shadow-sm">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">Active Users</p>
                <p className="text-2xl font-bold text-emerald-600">{activeUsers}</p>
              </div>
              <UserCheck className="h-8 w-8 text-emerald-200" />
            </div>
          </CardContent>
        </Card>
        <Card className="bg-white border-slate-200 shadow-sm">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">Verified</p>
                <p className="text-2xl font-bold text-blue-600">{verifiedUsers}</p>
              </div>
              <CheckCircle className="h-8 w-8 text-blue-200" />
            </div>
          </CardContent>
        </Card>
        <Card className="bg-white border-slate-200 shadow-sm">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">Platform Admins</p>
                <p className="text-2xl font-bold text-indigo-600">{platformAdmins}</p>
              </div>
              <Shield className="h-8 w-8 text-indigo-200" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card className="bg-white border-slate-200 shadow-sm">
        <CardContent className="pt-6">
          <div className="flex flex-wrap gap-4">
            <div className="relative flex-1 min-w-64">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
              <Input
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search by email or name..."
                className="pl-10 bg-white border-slate-300 text-slate-900"
              />
            </div>
            <Select value={roleFilter} onValueChange={setRoleFilter}>
              <SelectTrigger className="w-40 bg-white border-slate-300 text-slate-900">
                <SelectValue placeholder="Role" />
              </SelectTrigger>
              <SelectContent className="bg-white border-slate-200">
                <SelectItem value="all">All Roles</SelectItem>
                <SelectItem value="OWNER">Owner</SelectItem>
                <SelectItem value="ADMIN">Admin</SelectItem>
                <SelectItem value="MEMBER">Member</SelectItem>
              </SelectContent>
            </Select>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-40 bg-white border-slate-300 text-slate-900">
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent className="bg-white border-slate-200">
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="active">Active</SelectItem>
                <SelectItem value="inactive">Inactive</SelectItem>
              </SelectContent>
            </Select>
            <Button
              variant="outline"
              onClick={fetchUsers}
              className="border-slate-300 text-slate-600 hover:bg-slate-50"
            >
              <RefreshCw className="h-4 w-4" />
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Users Table */}
      <Card className="bg-white border-slate-200 shadow-sm">
        <CardContent className="pt-6">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-slate-400" />
            </div>
          ) : users.length === 0 ? (
            <div className="text-center py-12">
              <Users className="h-12 w-12 mx-auto text-slate-300 mb-4" />
              <p className="text-slate-500">No users found</p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow className="border-slate-200 hover:bg-transparent">
                  <TableHead className="text-slate-500">User</TableHead>
                  <TableHead className="text-slate-500">Account</TableHead>
                  <TableHead className="text-slate-500">Platform Admin</TableHead>
                  <TableHead className="text-slate-500">Tenant Role</TableHead>
                  <TableHead className="text-slate-500">Status</TableHead>
                  <TableHead className="text-slate-500">Verified</TableHead>
                  <TableHead className="text-slate-500">Created</TableHead>
                  <TableHead className="text-slate-500 text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {users.map((user) => (
                  <TableRow key={user.user_id} className="border-slate-100">
                    <TableCell>
                      <div>
                        <p className="text-slate-900 font-medium">
                          {user.first_name || user.last_name
                            ? `${user.first_name || ''} ${user.last_name || ''}`.trim()
                            : '-'}
                        </p>
                        <p className="text-sm text-slate-400">{user.email}</p>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div>
                        <p className="text-slate-700">{user.account_name}</p>
                        <p className="text-xs text-slate-400">
                          {user.account_type === "INDUSTRY_AFFILIATE" ? "Affiliate" : "Regular"}
                        </p>
                      </div>
                    </TableCell>
                    <TableCell>
                      {user.is_platform_admin ? (
                        <Badge className="bg-indigo-100 text-indigo-700 border-indigo-200">
                          <Shield className="h-3 w-3 mr-1" />
                          Yes
                        </Badge>
                      ) : (
                        <span className="text-slate-400">—</span>
                      )}
                    </TableCell>
                    <TableCell>
                      <Badge
                        variant="outline"
                        className={
                          user.role === "OWNER" ? "border-amber-300 text-amber-700 bg-amber-50" :
                          user.role === "ADMIN" ? "border-blue-300 text-blue-700 bg-blue-50" :
                          "border-slate-300 text-slate-600"
                        }
                      >
                        {user.role || "Member"}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Badge className={user.is_active ? "bg-emerald-100 text-emerald-700" : "bg-red-100 text-red-700"}>
                        {user.is_active ? "Active" : "Inactive"}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      {user.email_verified ? (
                        <CheckCircle className="h-5 w-5 text-emerald-500" />
                      ) : (
                        <XCircle className="h-5 w-5 text-slate-300" />
                      )}
                    </TableCell>
                    <TableCell className="text-slate-400 text-sm">
                      {formatDate(user.created_at)}
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center justify-end gap-1">
                        {actionLoading === user.user_id ? (
                          <Loader2 className="h-4 w-4 animate-spin text-slate-400" />
                        ) : (
                          <>
                            {/* Toggle Active/Inactive */}
                            {user.is_active ? (
                              <Button
                                size="sm"
                                variant="ghost"
                                onClick={() => updateUser(user.user_id, { is_active: false })}
                                className="h-8 px-2 text-red-600 hover:text-red-700 hover:bg-red-50"
                                title="Deactivate user"
                              >
                                <UserX className="h-4 w-4" />
                              </Button>
                            ) : (
                              <Button
                                size="sm"
                                variant="ghost"
                                onClick={() => updateUser(user.user_id, { is_active: true })}
                                className="h-8 px-2 text-emerald-600 hover:text-emerald-700 hover:bg-emerald-50"
                                title="Activate user"
                              >
                                <UserCheck className="h-4 w-4" />
                              </Button>
                            )}

                            {/* Verify Email (only if not verified) */}
                            {!user.email_verified && (
                              <Button
                                size="sm"
                                variant="ghost"
                                onClick={() => updateUser(user.user_id, { email_verified: true })}
                                className="h-8 px-2 text-blue-600 hover:text-blue-700 hover:bg-blue-50"
                                title="Mark as verified"
                              >
                                <CheckCircle className="h-4 w-4" />
                              </Button>
                            )}

                            {/* Resend Invite (only if not verified) */}
                            {!user.email_verified && (
                              <Button
                                size="sm"
                                variant="ghost"
                                onClick={() => resendInvite(user.user_id)}
                                className="h-8 px-2 text-slate-600 hover:text-slate-700 hover:bg-slate-100"
                                title="Resend invite email"
                              >
                                <Send className="h-4 w-4" />
                              </Button>
                            )}

                            {/* Force Password Reset */}
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => forcePasswordReset(user.user_id, user.email)}
                              className="h-8 px-2 text-amber-600 hover:text-amber-700 hover:bg-amber-50"
                              title="Send password reset email"
                            >
                              <KeyRound className="h-4 w-4" />
                            </Button>

                            {/* Toggle Platform Admin */}
                            {user.is_platform_admin ? (
                              <Button
                                size="sm"
                                variant="ghost"
                                onClick={() => {
                                  if (confirm(`Revoke platform admin from ${user.email}? They will lose access to /admin.`)) {
                                    updateUser(user.user_id, { is_platform_admin: false })
                                  }
                                }}
                                className="h-8 px-2 text-red-600 hover:text-red-700 hover:bg-red-50"
                                title="Revoke platform admin"
                              >
                                <ShieldOff className="h-4 w-4" />
                              </Button>
                            ) : (
                              <Button
                                size="sm"
                                variant="ghost"
                                onClick={() => {
                                  if (confirm(`Grant platform admin to ${user.email}? They will have full access to /admin.`)) {
                                    updateUser(user.user_id, { is_platform_admin: true })
                                  }
                                }}
                                className="h-8 px-2 text-indigo-600 hover:text-indigo-700 hover:bg-indigo-50"
                                title="Grant platform admin"
                              >
                                <Shield className="h-4 w-4" />
                              </Button>
                            )}
                          </>
                        )}
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Legend */}
      <Card className="bg-slate-50 border-slate-200">
        <CardContent className="py-4">
          <div className="space-y-4">
            <div>
              <p className="text-sm text-slate-500 mb-2 font-medium">Role Definitions:</p>
              <div className="flex flex-wrap gap-6 text-sm">
                <div className="flex items-center gap-2">
                  <Badge className="bg-indigo-100 text-indigo-700 border-indigo-200">
                    <Shield className="h-3 w-3 mr-1" />
                    Platform Admin
                  </Badge>
                  <span className="text-slate-600">Access to /admin console (system-wide)</span>
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant="outline" className="border-amber-300 text-amber-700 bg-amber-50">OWNER</Badge>
                  <span className="text-slate-600">Full control within their account</span>
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant="outline" className="border-blue-300 text-blue-700 bg-blue-50">ADMIN</Badge>
                  <span className="text-slate-600">Admin within their account</span>
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant="outline" className="border-slate-300 text-slate-600">MEMBER</Badge>
                  <span className="text-slate-600">Regular member</span>
                </div>
              </div>
            </div>
            <div>
              <p className="text-sm text-slate-500 mb-2 font-medium">Actions:</p>
              <div className="flex flex-wrap gap-6 text-sm">
                <div className="flex items-center gap-2">
                  <UserCheck className="h-4 w-4 text-emerald-600" />
                  <span className="text-slate-600">Activate</span>
                </div>
                <div className="flex items-center gap-2">
                  <UserX className="h-4 w-4 text-red-600" />
                  <span className="text-slate-600">Deactivate</span>
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle className="h-4 w-4 text-blue-600" />
                  <span className="text-slate-600">Verify Email</span>
                </div>
                <div className="flex items-center gap-2">
                  <Send className="h-4 w-4 text-slate-600" />
                  <span className="text-slate-600">Resend Invite</span>
                </div>
                <div className="flex items-center gap-2">
                  <KeyRound className="h-4 w-4 text-amber-600" />
                  <span className="text-slate-600">Password Reset</span>
                </div>
                <div className="flex items-center gap-2">
                  <Shield className="h-4 w-4 text-indigo-600" />
                  <span className="text-slate-600">Grant Admin</span>
                </div>
                <div className="flex items-center gap-2">
                  <ShieldOff className="h-4 w-4 text-red-600" />
                  <span className="text-slate-600">Revoke Admin</span>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
