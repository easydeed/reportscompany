"use client"

import { useState, useEffect } from "react"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
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
  Mail,
  RefreshCw,
  Loader2,
  CheckCircle,
  XCircle,
  Users,
} from "lucide-react"

interface EmailLog {
  id: string
  account_id: string
  account_name: string
  schedule_id: string | null
  report_id: string | null
  provider: string
  to_emails: string[]
  to_count: number
  subject: string
  response_code: number | null
  error: string | null
  created_at: string
  status: string
}

export default function EmailsPage() {
  const [emails, setEmails] = useState<EmailLog[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchEmails()
  }, [])

  async function fetchEmails() {
    setLoading(true)
    try {
      const res = await fetch("/api/v1/admin/emails?limit=200", {
        credentials: "include",
      })
      if (res.ok) {
        const data = await res.json()
        setEmails(data.emails || [])
      }
    } catch (error) {
      console.error("Failed to fetch emails:", error)
    } finally {
      setLoading(false)
    }
  }

  const formatTimeAgo = (date: string) => {
    const d = new Date(date)
    const now = new Date()
    const diff = now.getTime() - d.getTime()
    const mins = Math.floor(diff / (1000 * 60))
    if (mins < 1) return "Just now"
    if (mins < 60) return `${mins}m ago`
    const hours = Math.floor(mins / 60)
    if (hours < 24) return `${hours}h ago`
    const days = Math.floor(hours / 24)
    return `${days}d ago`
  }

  // Calculate stats
  const stats = {
    total: emails.length,
    success: emails.filter(e => e.status === "success").length,
    failed: emails.filter(e => e.status === "failed").length,
    totalRecipients: emails.reduce((sum, e) => sum + e.to_count, 0),
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-slate-900">Email Logs</h1>
          <p className="text-slate-500 mt-1">Monitor all email deliveries across the platform</p>
        </div>
        <Button
          variant="outline"
          onClick={fetchEmails}
          className="border-slate-300 text-slate-600 hover:bg-slate-50"
        >
          <RefreshCw className="h-4 w-4 mr-2" />
          Refresh
        </Button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-4 gap-4">
        <Card className="bg-white border-slate-200 shadow-sm">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">Total Emails</p>
                <p className="text-2xl font-bold text-slate-900">{stats.total}</p>
              </div>
              <Mail className="h-6 w-6 text-slate-300" />
            </div>
          </CardContent>
        </Card>
        <Card className="bg-white border-slate-200 shadow-sm">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">Delivered</p>
                <p className="text-2xl font-bold text-emerald-600">{stats.success}</p>
              </div>
              <CheckCircle className="h-6 w-6 text-emerald-200" />
            </div>
          </CardContent>
        </Card>
        <Card className="bg-white border-slate-200 shadow-sm">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">Failed</p>
                <p className="text-2xl font-bold text-red-600">{stats.failed}</p>
              </div>
              <XCircle className="h-6 w-6 text-red-200" />
            </div>
          </CardContent>
        </Card>
        <Card className="bg-white border-slate-200 shadow-sm">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">Total Recipients</p>
                <p className="text-2xl font-bold text-slate-900">{stats.totalRecipients}</p>
              </div>
              <Users className="h-6 w-6 text-blue-200" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Emails Table */}
      <Card className="bg-white border-slate-200 shadow-sm">
        <CardContent className="pt-6">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-slate-400" />
            </div>
          ) : emails.length === 0 ? (
            <div className="text-center py-12">
              <Mail className="h-12 w-12 mx-auto text-slate-300 mb-4" />
              <p className="text-slate-500">No emails sent yet</p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow className="border-slate-200 hover:bg-transparent">
                  <TableHead className="text-slate-500">Account</TableHead>
                  <TableHead className="text-slate-500">Subject</TableHead>
                  <TableHead className="text-slate-500">Recipients</TableHead>
                  <TableHead className="text-slate-500">Provider</TableHead>
                  <TableHead className="text-slate-500">Status</TableHead>
                  <TableHead className="text-slate-500">Sent</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {emails.map((email) => (
                  <TableRow key={email.id} className="border-slate-100">
                    <TableCell className="text-slate-900 font-medium">
                      {email.account_name}
                    </TableCell>
                    <TableCell>
                      <p className="text-slate-600 truncate max-w-xs">{email.subject}</p>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-1 text-slate-500">
                        <Users className="h-3 w-3" />
                        <span>{email.to_count}</span>
                      </div>
                    </TableCell>
                    <TableCell className="text-slate-400 text-sm">
                      {email.provider}
                    </TableCell>
                    <TableCell>
                      {email.status === "success" ? (
                        <Badge className="bg-emerald-100 text-emerald-700 border-emerald-200">
                          <CheckCircle className="h-3 w-3 mr-1" />
                          Delivered
                        </Badge>
                      ) : (
                        <Badge className="bg-red-100 text-red-700 border-red-200">
                          <XCircle className="h-3 w-3 mr-1" />
                          Failed
                        </Badge>
                      )}
                    </TableCell>
                    <TableCell className="text-slate-400 text-sm">
                      {formatTimeAgo(email.created_at)}
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
