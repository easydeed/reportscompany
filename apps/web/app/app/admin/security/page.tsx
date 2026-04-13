"use client"

import { useEffect, useState, useCallback } from "react"
import Link from "next/link"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
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
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import {
  ArrowLeft,
  ShieldBan,
  ShieldCheck,
  Plus,
  Trash2,
  Loader2,
  Clock,
  Ban,
  Sparkles,
  AlertTriangle,
} from "lucide-react"
import { useToast } from "@/components/ui/use-toast"

interface BlockedIP {
  id: string
  ip_address: string
  reason: string | null
  blocked_by_email: string | null
  created_at: string | null
  expires_at: string | null
}

function formatDate(dateString: string | null): string {
  if (!dateString) return "—"
  return new Date(dateString).toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
  })
}

function getStatus(item: BlockedIP): { label: string; className: string } {
  if (!item.expires_at) {
    return { label: "Permanent", className: "text-red-600 border-red-200 bg-red-50" }
  }
  const expiresAt = new Date(item.expires_at)
  if (expiresAt <= new Date()) {
    return { label: "Expired", className: "text-muted-foreground border-gray-200 bg-gray-50" }
  }
  return { label: "Temporary", className: "text-yellow-600 border-yellow-200 bg-yellow-50" }
}

export default function AdminSecurityPage() {
  const { toast } = useToast()

  const [items, setItems] = useState<BlockedIP[]>([])
  const [loading, setLoading] = useState(true)
  const [includeExpired, setIncludeExpired] = useState(false)

  const [blockOpen, setBlockOpen] = useState(false)
  const [blockForm, setBlockForm] = useState({ ip_address: "", reason: "", expires_at: "" })
  const [saving, setSaving] = useState(false)

  const [confirmDelete, setConfirmDelete] = useState<BlockedIP | null>(null)
  const [deleting, setDeleting] = useState(false)
  const [cleaning, setCleaning] = useState(false)

  const fetchBlocked = useCallback(async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams()
      if (includeExpired) params.set("include_expired", "true")
      const res = await fetch(`/api/proxy/v1/admin/blocked-ips?${params.toString()}`, {
        credentials: "include",
      })
      if (res.ok) {
        const data = await res.json()
        setItems(data?.blocked_ips || [])
      }
    } catch (err) {
      console.error("Failed to fetch blocked IPs:", err)
    } finally {
      setLoading(false)
    }
  }, [includeExpired])

  useEffect(() => {
    fetchBlocked()
  }, [fetchBlocked])

  async function handleBlock() {
    if (!blockForm.ip_address.trim()) {
      toast({ title: "IP address is required", variant: "destructive" })
      return
    }

    setSaving(true)
    try {
      const body: Record<string, string | null> = {
        ip_address: blockForm.ip_address.trim(),
        reason: blockForm.reason.trim() || null,
        expires_at: blockForm.expires_at || null,
      }

      const res = await fetch("/api/proxy/v1/admin/blocked-ips", {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      })

      if (!res.ok) {
        const data = await res.json().catch(() => ({}))
        throw new Error(data.detail || "Failed to block IP")
      }

      toast({ title: "IP blocked", description: blockForm.ip_address })
      setBlockOpen(false)
      setBlockForm({ ip_address: "", reason: "", expires_at: "" })
      fetchBlocked()
    } catch (err) {
      toast({
        title: "Failed to block IP",
        description: err instanceof Error ? err.message : "Unknown error",
        variant: "destructive",
      })
    } finally {
      setSaving(false)
    }
  }

  async function handleUnblock() {
    if (!confirmDelete) return

    setDeleting(true)
    try {
      const res = await fetch(`/api/proxy/v1/admin/blocked-ips/${confirmDelete.id}`, {
        method: "DELETE",
        credentials: "include",
      })

      if (!res.ok) {
        const data = await res.json().catch(() => ({}))
        throw new Error(data.detail || "Failed to unblock IP")
      }

      toast({ title: "IP unblocked", description: confirmDelete.ip_address })
      setConfirmDelete(null)
      setItems((prev) => prev.filter((i) => i.id !== confirmDelete.id))
    } catch (err) {
      toast({
        title: "Failed to unblock IP",
        description: err instanceof Error ? err.message : "Unknown error",
        variant: "destructive",
      })
    } finally {
      setDeleting(false)
    }
  }

  async function handleCleanup() {
    setCleaning(true)
    try {
      const res = await fetch("/api/proxy/v1/admin/blocked-ips/cleanup", {
        method: "POST",
        credentials: "include",
      })

      if (!res.ok) throw new Error("Cleanup failed")

      const data = await res.json()
      toast({
        title: "Cleanup complete",
        description: `Removed ${data.expired_blocks_removed ?? 0} expired blocks, ${data.rate_limits_removed ?? 0} old rate limits`,
      })
      fetchBlocked()
    } catch (err) {
      toast({
        title: "Cleanup failed",
        description: err instanceof Error ? err.message : "Unknown error",
        variant: "destructive",
      })
    } finally {
      setCleaning(false)
    }
  }

  const now = new Date()
  const activeCount = items.filter(
    (i) => !i.expires_at || new Date(i.expires_at) > now
  ).length
  const permanentCount = items.filter((i) => !i.expires_at).length
  const expiredCount = items.filter(
    (i) => i.expires_at && new Date(i.expires_at) <= now
  ).length

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <Skeleton className="h-10 w-10 rounded" />
          <div>
            <Skeleton className="h-9 w-48 mb-2" />
            <Skeleton className="h-5 w-72" />
          </div>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => (
            <Card key={i}>
              <CardContent className="pt-6">
                <Skeleton className="h-8 w-16" />
              </CardContent>
            </Card>
          ))}
        </div>
        <Card>
          <CardContent className="pt-6">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="py-3 flex gap-4">
                <Skeleton className="h-4 w-40" />
                <Skeleton className="h-4 w-24" />
                <Skeleton className="h-5 w-16 rounded-full" />
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link href="/app/admin">
            <Button variant="ghost" size="icon">
              <ArrowLeft className="h-4 w-4" />
            </Button>
          </Link>
          <div>
            <h1 className="text-3xl font-display font-bold text-foreground">
              Security
            </h1>
            <p className="text-muted-foreground mt-1">
              Manage blocked IP addresses and rate limiting
            </p>
          </div>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={handleCleanup}
            disabled={cleaning}
          >
            {cleaning ? (
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
            ) : (
              <Sparkles className="h-4 w-4 mr-2" />
            )}
            Clean Up Expired
          </Button>
          <Button onClick={() => setBlockOpen(true)}>
            <Plus className="h-4 w-4 mr-2" />
            Block IP
          </Button>
        </div>
      </div>

      {/* Metric Cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Blocks</CardTitle>
            <ShieldBan className="h-4 w-4 text-red-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{activeCount}</div>
            <p className="text-xs text-muted-foreground">Currently enforced</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Permanent</CardTitle>
            <Ban className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{permanentCount}</div>
            <p className="text-xs text-muted-foreground">No expiry set</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Expired</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{expiredCount}</div>
            <p className="text-xs text-muted-foreground">Ready for cleanup</p>
          </CardContent>
        </Card>
      </div>

      {/* Toggle include expired */}
      <div className="flex items-center gap-3">
        <Switch
          id="include-expired"
          checked={includeExpired}
          onCheckedChange={setIncludeExpired}
        />
        <Label htmlFor="include-expired" className="cursor-pointer text-sm">
          Show expired entries
        </Label>
      </div>

      {/* Table */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <ShieldBan className="h-5 w-5" />
            Blocked IPs ({items.length})
          </CardTitle>
        </CardHeader>
        <CardContent>
          {items.length === 0 ? (
            <div className="text-center py-12">
              <ShieldCheck className="h-12 w-12 mx-auto text-green-500 mb-4" />
              <h3 className="text-lg font-semibold mb-2">No blocked IPs</h3>
              <p className="text-muted-foreground">
                {includeExpired
                  ? "No IPs have been blocked"
                  : "No active blocks. Toggle above to see expired."}
              </p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="text-[11px] uppercase tracking-wider">
                    IP Address
                  </TableHead>
                  <TableHead className="text-[11px] uppercase tracking-wider">
                    Reason
                  </TableHead>
                  <TableHead className="text-[11px] uppercase tracking-wider">
                    Blocked By
                  </TableHead>
                  <TableHead className="text-[11px] uppercase tracking-wider">
                    Blocked At
                  </TableHead>
                  <TableHead className="text-[11px] uppercase tracking-wider">
                    Expires At
                  </TableHead>
                  <TableHead className="text-[11px] uppercase tracking-wider">
                    Status
                  </TableHead>
                  <TableHead className="text-[11px] uppercase tracking-wider">
                    Actions
                  </TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {items.map((item) => {
                  const status = getStatus(item)
                  const isExpired = status.label === "Expired"

                  return (
                    <TableRow
                      key={item.id}
                      className={isExpired ? "opacity-50" : ""}
                    >
                      <TableCell>
                        <code className="text-sm font-mono bg-muted px-1.5 py-0.5 rounded">
                          {item.ip_address}
                        </code>
                      </TableCell>
                      <TableCell className="text-sm text-muted-foreground max-w-[200px] truncate">
                        {item.reason || "—"}
                      </TableCell>
                      <TableCell className="text-sm text-muted-foreground">
                        {item.blocked_by_email || "System"}
                      </TableCell>
                      <TableCell className="text-sm text-muted-foreground">
                        {formatDate(item.created_at)}
                      </TableCell>
                      <TableCell className="text-sm text-muted-foreground">
                        {item.expires_at ? formatDate(item.expires_at) : "Never"}
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline" className={status.className}>
                          {status.label}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-8 w-8 p-0 text-red-600 hover:text-red-700 hover:bg-red-50"
                          onClick={() => setConfirmDelete(item)}
                          title="Unblock IP"
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </TableCell>
                    </TableRow>
                  )
                })}
              </TableBody>
            </Table>
          )}
          {items.length > 0 && (
            <p className="text-xs text-muted-foreground text-center mt-4">
              Showing {items.length} entr{items.length !== 1 ? "ies" : "y"}
            </p>
          )}
        </CardContent>
      </Card>

      {/* Block IP Dialog */}
      <Dialog open={blockOpen} onOpenChange={setBlockOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Block IP Address</DialogTitle>
            <DialogDescription>
              Block an IP from accessing CMA lead pages and other rate-limited
              endpoints
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-2">
            <div className="space-y-2">
              <Label htmlFor="ip_address">IP Address</Label>
              <Input
                id="ip_address"
                placeholder="e.g. 192.168.1.1"
                value={blockForm.ip_address}
                onChange={(e) =>
                  setBlockForm((f) => ({ ...f, ip_address: e.target.value }))
                }
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="reason">Reason (optional)</Label>
              <Input
                id="reason"
                placeholder="e.g. Spam submissions"
                value={blockForm.reason}
                onChange={(e) =>
                  setBlockForm((f) => ({ ...f, reason: e.target.value }))
                }
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="expires_at">
                Expires At (optional — leave blank for permanent)
              </Label>
              <Input
                id="expires_at"
                type="datetime-local"
                value={blockForm.expires_at}
                onChange={(e) =>
                  setBlockForm((f) => ({ ...f, expires_at: e.target.value }))
                }
              />
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setBlockOpen(false)}
              disabled={saving}
            >
              Cancel
            </Button>
            <Button
              onClick={handleBlock}
              disabled={saving}
              variant="destructive"
            >
              {saving ? (
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <ShieldBan className="h-4 w-4 mr-2" />
              )}
              Block IP
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Confirm Unblock Dialog */}
      <Dialog
        open={!!confirmDelete}
        onOpenChange={(open) => !open && setConfirmDelete(null)}
      >
        <DialogContent className="sm:max-w-sm">
          <DialogHeader>
            <DialogTitle>Unblock IP</DialogTitle>
            <DialogDescription>
              Remove{" "}
              <code className="font-mono text-xs bg-muted px-1 py-0.5 rounded">
                {confirmDelete?.ip_address}
              </code>{" "}
              from the block list? This IP will immediately be able to access
              the platform again.
            </DialogDescription>
          </DialogHeader>
          {confirmDelete?.reason && (
            <div className="bg-yellow-50 border border-yellow-200 text-yellow-800 px-3 py-2 rounded-lg text-sm flex items-start gap-2">
              <AlertTriangle className="h-4 w-4 mt-0.5 flex-shrink-0" />
              <span>Blocked for: {confirmDelete.reason}</span>
            </div>
          )}
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setConfirmDelete(null)}
              disabled={deleting}
            >
              Cancel
            </Button>
            <Button
              onClick={handleUnblock}
              disabled={deleting}
              variant="destructive"
            >
              {deleting ? (
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <Trash2 className="h-4 w-4 mr-2" />
              )}
              Unblock
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
