"use client"

import { useEffect, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
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
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import {
  MessageSquare,
  CreditCard,
  AlertTriangle,
  Plus,
  Minus,
  Loader2,
  CheckCircle,
  XCircle,
  Search,
} from "lucide-react"
import { toast } from "sonner"

interface AccountCredits {
  account_id: string
  account_name: string
  sms_credits: number
  sms_credits_per_month: number
  lead_capture_enabled: boolean
}

interface SMSLog {
  id: string
  account_id: string
  account_name: string
  to_phone: string
  from_phone: string
  message: string
  status: string
  error: string | null
  created_at: string
}

export default function AdminSMSPage() {
  const [credits, setCredits] = useState<AccountCredits[]>([])
  const [logs, setLogs] = useState<SMSLog[]>([])
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState("")

  // Credit adjustment modal
  const [adjustOpen, setAdjustOpen] = useState(false)
  const [selectedAccount, setSelectedAccount] = useState<string>("")
  const [adjustAmount, setAdjustAmount] = useState<string>("0")
  const [adjusting, setAdjusting] = useState(false)

  useEffect(() => {
    loadData()
  }, [])

  async function loadData() {
    try {
      setLoading(true)
      const [creditsRes, logsRes] = await Promise.all([
        fetch("/api/proxy/v1/admin/sms/credits", { credentials: "include" }),
        fetch("/api/proxy/v1/admin/sms/logs?limit=50", { credentials: "include" }),
      ])

      if (creditsRes.ok) {
        const data = await creditsRes.json()
        setCredits(data.accounts || [])
      }

      if (logsRes.ok) {
        const data = await logsRes.json()
        setLogs(data.logs || [])
      }
    } catch (e) {
      toast.error("Failed to load SMS data")
    } finally {
      setLoading(false)
    }
  }

  async function handleAdjustCredits() {
    if (!selectedAccount || !adjustAmount) return
    
    setAdjusting(true)
    try {
      const res = await fetch("/api/proxy/v1/admin/sms/credits", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          account_id: selectedAccount,
          adjustment: parseInt(adjustAmount),
        }),
      })

      if (!res.ok) throw new Error("Failed to adjust")

      toast.success("Credits adjusted successfully")
      setAdjustOpen(false)
      setSelectedAccount("")
      setAdjustAmount("0")
      loadData()
    } catch {
      toast.error("Failed to adjust credits")
    } finally {
      setAdjusting(false)
    }
  }

  const filteredCredits = credits.filter((c) =>
    c.account_name.toLowerCase().includes(searchQuery.toLowerCase())
  )

  const failedLogs = logs.filter((l) => l.status === "failed")
  const totalCredits = credits.reduce((sum, c) => sum + c.sms_credits, 0)

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-display font-bold">SMS Management</h1>
        <p className="text-muted-foreground mt-2">Manage SMS credits and view delivery logs</p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Credits</CardTitle>
            <CreditCard className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalCredits}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Accounts</CardTitle>
            <MessageSquare className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{credits.length}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">SMS Sent</CardTitle>
            <CheckCircle className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{logs.filter((l) => l.status === "sent").length}</div>
          </CardContent>
        </Card>

        <Card className={failedLogs.length > 0 ? "bg-red-50 border-red-200" : ""}>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Failed</CardTitle>
            <AlertTriangle className={`h-4 w-4 ${failedLogs.length > 0 ? "text-red-500" : "text-muted-foreground"}`} />
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold ${failedLogs.length > 0 ? "text-red-600" : ""}`}>
              {failedLogs.length}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Account Credits Table */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <CreditCard className="h-5 w-5" />
                Account Credits
              </CardTitle>
              <CardDescription>SMS credit balances by account</CardDescription>
            </div>
            <Dialog open={adjustOpen} onOpenChange={setAdjustOpen}>
              <DialogTrigger asChild>
                <Button>
                  <Plus className="w-4 h-4 mr-2" />
                  Adjust Credits
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Adjust SMS Credits</DialogTitle>
                  <DialogDescription>
                    Add or subtract credits from an account
                  </DialogDescription>
                </DialogHeader>
                <div className="space-y-4 py-4">
                  <div className="space-y-2">
                    <Label>Account</Label>
                    <Select value={selectedAccount} onValueChange={setSelectedAccount}>
                      <SelectTrigger>
                        <SelectValue placeholder="Select account" />
                      </SelectTrigger>
                      <SelectContent>
                        {credits.map((c) => (
                          <SelectItem key={c.account_id} value={c.account_id}>
                            {c.account_name} ({c.sms_credits} credits)
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label>Adjustment</Label>
                    <div className="flex gap-2">
                      <Button
                        variant="outline"
                        size="icon"
                        onClick={() => setAdjustAmount((prev) => String(parseInt(prev) - 10))}
                      >
                        <Minus className="w-4 h-4" />
                      </Button>
                      <Input
                        type="number"
                        value={adjustAmount}
                        onChange={(e) => setAdjustAmount(e.target.value)}
                        className="text-center"
                      />
                      <Button
                        variant="outline"
                        size="icon"
                        onClick={() => setAdjustAmount((prev) => String(parseInt(prev) + 10))}
                      >
                        <Plus className="w-4 h-4" />
                      </Button>
                    </div>
                    <p className="text-xs text-muted-foreground">
                      Use positive numbers to add, negative to subtract
                    </p>
                  </div>
                </div>
                <DialogFooter>
                  <Button variant="outline" onClick={() => setAdjustOpen(false)}>
                    Cancel
                  </Button>
                  <Button 
                    onClick={handleAdjustCredits} 
                    disabled={adjusting || !selectedAccount}
                  >
                    {adjusting && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
                    Apply
                  </Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          </div>
        </CardHeader>
        <CardContent>
          <div className="mb-4">
            <div className="relative max-w-xs">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <Input
                placeholder="Search accounts..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-9"
              />
            </div>
          </div>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Account</TableHead>
                <TableHead>Credits</TableHead>
                <TableHead>Monthly Allowance</TableHead>
                <TableHead>Lead Capture</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredCredits.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={4} className="text-center py-8 text-muted-foreground">
                    No accounts found
                  </TableCell>
                </TableRow>
              ) : (
                filteredCredits.map((account) => (
                  <TableRow key={account.account_id}>
                    <TableCell className="font-medium">{account.account_name}</TableCell>
                    <TableCell>
                      <span className={`font-bold ${account.sms_credits <= 0 ? "text-red-600" : ""}`}>
                        {account.sms_credits}
                      </span>
                    </TableCell>
                    <TableCell>{account.sms_credits_per_month}</TableCell>
                    <TableCell>
                      {account.lead_capture_enabled ? (
                        <Badge className="bg-green-100 text-green-800">Enabled</Badge>
                      ) : (
                        <Badge variant="outline">Disabled</Badge>
                      )}
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* SMS Logs */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <MessageSquare className="h-5 w-5" />
            Recent SMS Log
          </CardTitle>
          <CardDescription>Last 50 SMS messages sent</CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Account</TableHead>
                <TableHead>To</TableHead>
                <TableHead>Message</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Sent</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {logs.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={5} className="text-center py-8 text-muted-foreground">
                    No SMS logs found
                  </TableCell>
                </TableRow>
              ) : (
                logs.map((log) => (
                  <TableRow key={log.id}>
                    <TableCell className="font-medium text-sm">{log.account_name}</TableCell>
                    <TableCell className="font-mono text-sm">{log.to_phone}</TableCell>
                    <TableCell className="max-w-[200px] truncate text-sm">
                      {log.message}
                    </TableCell>
                    <TableCell>
                      {log.status === "sent" ? (
                        <Badge className="bg-green-100 text-green-800">Sent</Badge>
                      ) : log.status === "failed" ? (
                        <div>
                          <Badge className="bg-red-100 text-red-800">Failed</Badge>
                          {log.error && (
                            <p className="text-xs text-red-600 mt-1">{log.error}</p>
                          )}
                        </div>
                      ) : (
                        <Badge variant="outline">{log.status}</Badge>
                      )}
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      {new Date(log.created_at).toLocaleString()}
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Failed SMS List */}
      {failedLogs.length > 0 && (
        <Card className="border-red-200 bg-red-50/50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-red-800">
              <XCircle className="h-5 w-5" />
              Failed SMS ({failedLogs.length})
            </CardTitle>
            <CardDescription className="text-red-700">
              Messages that failed to deliver
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {failedLogs.map((log) => (
                <div
                  key={log.id}
                  className="p-3 bg-white rounded-lg border border-red-200"
                >
                  <div className="flex justify-between items-start">
                    <div>
                      <p className="font-medium text-sm">{log.account_name}</p>
                      <p className="text-xs text-muted-foreground">To: {log.to_phone}</p>
                    </div>
                    <span className="text-xs text-muted-foreground">
                      {new Date(log.created_at).toLocaleString()}
                    </span>
                  </div>
                  {log.error && (
                    <p className="text-sm text-red-600 mt-2 p-2 bg-red-50 rounded">
                      {log.error}
                    </p>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

