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
  Clock,
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
          <h1 className="text-3xl font-bold text-white">Email Logs</h1>
          <p className="text-gray-400 mt-1">Monitor all email deliveries across the platform</p>
        </div>
        <Button
          variant="outline"
          onClick={fetchEmails}
          className="border-gray-700 text-gray-300 hover:bg-gray-800"
        >
          <RefreshCw className="h-4 w-4 mr-2" />
          Refresh
        </Button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-4 gap-4">
        <Card className="bg-gray-900 border-gray-800">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-400">Total Emails</p>
                <p className="text-2xl font-bold text-white">{stats.total}</p>
              </div>
              <Mail className="h-6 w-6 text-gray-500" />
            </div>
          </CardContent>
        </Card>
        <Card className="bg-gray-900 border-gray-800">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-400">Delivered</p>
                <p className="text-2xl font-bold text-green-400">{stats.success}</p>
              </div>
              <CheckCircle className="h-6 w-6 text-green-400/30" />
            </div>
          </CardContent>
        </Card>
        <Card className="bg-gray-900 border-gray-800">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-400">Failed</p>
                <p className="text-2xl font-bold text-red-400">{stats.failed}</p>
              </div>
              <XCircle className="h-6 w-6 text-red-400/30" />
            </div>
          </CardContent>
        </Card>
        <Card className="bg-gray-900 border-gray-800">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-400">Total Recipients</p>
                <p className="text-2xl font-bold text-white">{stats.totalRecipients}</p>
              </div>
              <Users className="h-6 w-6 text-blue-400/30" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Emails Table */}
      <Card className="bg-gray-900 border-gray-800">
        <CardContent className="pt-6">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
            </div>
          ) : emails.length === 0 ? (
            <div className="text-center py-12">
              <Mail className="h-12 w-12 mx-auto text-gray-600 mb-4" />
              <p className="text-gray-400">No emails sent yet</p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow className="border-gray-800 hover:bg-transparent">
                  <TableHead className="text-gray-400">Account</TableHead>
                  <TableHead className="text-gray-400">Subject</TableHead>
                  <TableHead className="text-gray-400">Recipients</TableHead>
                  <TableHead className="text-gray-400">Provider</TableHead>
                  <TableHead className="text-gray-400">Status</TableHead>
                  <TableHead className="text-gray-400">Sent</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {emails.map((email) => (
                  <TableRow key={email.id} className="border-gray-800">
                    <TableCell className="text-white font-medium">
                      {email.account_name}
                    </TableCell>
                    <TableCell>
                      <p className="text-gray-300 truncate max-w-xs">{email.subject}</p>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-1 text-gray-400">
                        <Users className="h-3 w-3" />
                        <span>{email.to_count}</span>
                      </div>
                    </TableCell>
                    <TableCell className="text-gray-500 text-sm">
                      {email.provider}
                    </TableCell>
                    <TableCell>
                      {email.status === "success" ? (
                        <Badge className="bg-green-500/20 text-green-400 border-green-500/30">
                          <CheckCircle className="h-3 w-3 mr-1" />
                          Delivered
                        </Badge>
                      ) : (
                        <Badge className="bg-red-500/20 text-red-400 border-red-500/30">
                          <XCircle className="h-3 w-3 mr-1" />
                          Failed
                        </Badge>
                      )}
                    </TableCell>
                    <TableCell className="text-gray-500 text-sm">
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
