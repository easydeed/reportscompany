"use client"

import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { Card } from "@/components/ui/card"
import type { EmailLog } from "./types"
import { cn } from "@/lib/utils"

interface EmailLogTableProps {
  logs: EmailLog[]
}

export function EmailLogTable({ logs }: EmailLogTableProps) {
  const formatDate = (date: Date) => {
    return new Intl.DateTimeFormat("en-US", {
      month: "short",
      day: "numeric",
      hour: "numeric",
      minute: "2-digit",
    }).format(date)
  }

  const getCodeColor = (code: number) => {
    if (code >= 200 && code < 300) {
      return "border-green-500/50 bg-green-500/10 text-green-700 dark:text-green-400"
    }
    if (code >= 400) {
      return "border-red-500/50 bg-red-500/10 text-red-700 dark:text-red-400"
    }
    return "border-blue-500/50 bg-blue-500/10 text-blue-700 dark:text-blue-400"
  }

  return (
    <Card className="glass border-border">
      <div className="p-6 border-b border-border">
        <h3 className="text-lg font-display font-semibold text-foreground">Email Log</h3>
        <p className="text-sm text-muted-foreground">Recent email delivery attempts and status</p>
      </div>
      <div className="overflow-x-auto">
        <Table>
          <TableHeader>
            <TableRow className="hover:bg-transparent border-border">
              <TableHead className="font-semibold">Date</TableHead>
              <TableHead className="font-semibold">Recipients</TableHead>
              <TableHead className="font-semibold">Subject</TableHead>
              <TableHead className="font-semibold">Code</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {logs.map((log) => (
              <TableRow key={log.id} className="border-border">
                <TableCell className="text-muted-foreground">{formatDate(log.date)}</TableCell>
                <TableCell>
                  <Badge variant="outline" className="border-slate-500/50 bg-slate-500/10">
                    {log.to} {log.to === 1 ? "recipient" : "recipients"}
                  </Badge>
                </TableCell>
                <TableCell className="font-medium max-w-md truncate">{log.subject}</TableCell>
                <TableCell>
                  <Badge variant="outline" className={cn("font-mono", getCodeColor(log.code))}>
                    {log.code}
                  </Badge>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </Card>
  )
}
