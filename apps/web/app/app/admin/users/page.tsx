'use client'

import { useEffect, useState } from "react"
import { useSearchParams, useRouter } from "next/navigation"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Skeleton } from "@/components/ui/skeleton"
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
import { Users, ArrowLeft, CheckCircle, XCircle, Mail } from "lucide-react"
import { ResendInviteButton } from "./resend-invite-button"

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
  role: string
}

export default function AdminUsersPage() {
  const searchParams = useSearchParams()
  const router = useRouter()
  const [users, setUsers] = useState<User[]>([])
  const [count, setCount] = useState(0)
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)

  // Local filter state
  const [search, setSearch] = useState(searchParams.get('search') || '')
  const [isActive, setIsActive] = useState(searchParams.get('is_active') || 'all')
  const [role, setRole] = useState(searchParams.get('role') || 'all')

  useEffect(() => {
    async function fetchUsers() {
      setLoading(true)
      try {
        const params = new URLSearchParams()
        const s = searchParams.get('search')
        const ia = searchParams.get('is_active')
        const r = searchParams.get('role')

        if (s) params.set('search', s)
        if (ia && ia !== 'all') params.set('is_active', ia)
        if (r && r !== 'all') params.set('role', r)

        const res = await fetch(`/api/proxy/v1/admin/users?${params.toString()}`, {
          credentials: 'include',
        })
        if (res.ok) {
          const data = await res.json()
          setUsers(data?.users || [])
          setCount(data?.count || 0)
          setTotal(data?.total || 0)
        }
      } catch (err) {
        console.error('Failed to fetch users:', err)
      } finally {
        setLoading(false)
      }
    }
    fetchUsers()
  }, [searchParams])

  function handleFilter(e: React.FormEvent) {
    e.preventDefault()
    const params = new URLSearchParams()
    if (search) params.set('search', search)
    if (isActive !== 'all') params.set('is_active', isActive)
    if (role !== 'all') params.set('role', role)
    router.push(`/app/admin/users?${params.toString()}`)
  }

  const activeCount = users.filter(u => u.is_active).length
  const verifiedCount = users.filter(u => u.email_verified).length

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <Skeleton className="h-10 w-10 rounded" />
          <div>
            <Skeleton className="h-9 w-36 mb-2" />
            <Skeleton className="h-5 w-64" />
          </div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map(i => (
            <Card key={i}><CardContent className="pt-6"><Skeleton className="h-8 w-16" /></CardContent></Card>
          ))}
        </div>
        <Card><CardContent className="pt-6">
          {[1, 2, 3, 4, 5].map(i => (
            <div key={i} className="py-3 flex gap-4">
              <Skeleton className="h-4 w-40" />
              <Skeleton className="h-4 w-24" />
              <Skeleton className="h-5 w-16 rounded-full" />
            </div>
          ))}
        </CardContent></Card>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Link href="/app/admin">
          <Button variant="ghost" size="icon">
            <ArrowLeft className="h-4 w-4" />
          </Button>
        </Link>
        <div>
          <h1 className="text-3xl font-display font-bold text-foreground">All Users</h1>
          <p className="text-muted-foreground mt-1">View and manage all users in the system</p>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Users</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{total}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Showing</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{count}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active</CardTitle>
            <CheckCircle className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{activeCount}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Verified</CardTitle>
            <Mail className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{verifiedCount}</div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card className="mb-6">
        <CardContent className="pt-6">
          <form onSubmit={handleFilter} className="flex flex-wrap gap-4">
            <Input
              placeholder="Search by email or name..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-64"
            />
            <Select value={isActive} onValueChange={setIsActive}>
              <SelectTrigger className="w-40">
                <SelectValue placeholder="All Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="true">Active</SelectItem>
                <SelectItem value="false">Inactive</SelectItem>
              </SelectContent>
            </Select>
            <Select value={role} onValueChange={setRole}>
              <SelectTrigger className="w-40">
                <SelectValue placeholder="All Roles" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Roles</SelectItem>
                <SelectItem value="OWNER">Owner</SelectItem>
                <SelectItem value="MEMBER">Member</SelectItem>
                <SelectItem value="ADMIN">Admin</SelectItem>
              </SelectContent>
            </Select>
            <Button type="submit" variant="secondary">Filter</Button>
            {(searchParams.get('search') || searchParams.get('is_active') || searchParams.get('role')) && (
              <Link href="/app/admin/users">
                <Button variant="ghost" type="button">Clear</Button>
              </Link>
            )}
          </form>
        </CardContent>
      </Card>

      {/* Table */}
      <Card>
        <CardContent className="pt-6">
          {users.length === 0 ? (
            <div className="text-center py-12">
              <Users className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
              <h3 className="text-lg font-semibold mb-2">No users found</h3>
              <p className="text-muted-foreground">
                {searchParams.toString()
                  ? "No users match your filters"
                  : "No users in the system yet"}
              </p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>User</TableHead>
                  <TableHead>Account</TableHead>
                  <TableHead>Role</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Verified</TableHead>
                  <TableHead>Last Login</TableHead>
                  <TableHead>Joined</TableHead>
                  <TableHead></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {users.map((user) => (
                  <TableRow key={user.user_id}>
                    <TableCell>
                      <div>
                        <div className="font-medium">{user.email}</div>
                        {(user.first_name || user.last_name) && (
                          <div className="text-sm text-muted-foreground">
                            {user.first_name} {user.last_name}
                          </div>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      <div>
                        <div className="text-sm">{user.account_name}</div>
                        <Badge variant="outline" className="text-xs">
                          {user.account_type === "INDUSTRY_AFFILIATE" ? "Affiliate" : "Regular"}
                        </Badge>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant={user.role === "ADMIN" ? "default" : "secondary"}>
                        {user.role || "Member"}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      {user.is_active ? (
                        <Badge variant="outline" className="text-green-600">
                          <CheckCircle className="h-3 w-3 mr-1" />
                          Active
                        </Badge>
                      ) : (
                        <Badge variant="outline" className="text-red-600">
                          <XCircle className="h-3 w-3 mr-1" />
                          Inactive
                        </Badge>
                      )}
                    </TableCell>
                    <TableCell>
                      {user.email_verified ? (
                        <CheckCircle className="h-4 w-4 text-green-500" />
                      ) : (
                        <XCircle className="h-4 w-4 text-muted-foreground" />
                      )}
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      {user.last_login_at
                        ? new Date(user.last_login_at).toLocaleDateString()
                        : 'Never'}
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      {user.created_at
                        ? new Date(user.created_at).toLocaleDateString()
                        : '-'}
                    </TableCell>
                    <TableCell>
                      {!user.email_verified && (
                        <ResendInviteButton userId={user.user_id} email={user.email} />
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
