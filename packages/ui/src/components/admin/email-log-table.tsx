"use client"

import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../ui/table"
import { Card } from "../ui/card"
import type { EmailLog } from "./types"
import { cn } from "../../lib/utils"

interface AdminEmailsTableProps {
  logs: EmailLog[]
}

export function AdminEmailsTable({ logs }: AdminEmailsTableProps) {
  const formatDate = (date: Date) => {
    return new Intl.DateTimeFormat("en-US", {
      month: "short",
      day: "numeric",
      hour: "numeric",
      minute: "2-digit",
      second: "2-digit",
    }).format(date)
  }

  const getCodeDisplay = (code: number) => {
    const isSuccess = code >= 200 && code < 300
    const isError = code >= 400

    return (
      <div className="flex items-center gap-2">
        <div
          className={cn("w-2 h-2 rounded-full", isSuccess ? "bg-green-400" : isError ? "bg-red-400" : "bg-cyan-400")}
        />
        <span
          className={cn(
            "font-mono text-sm font-medium",
            isSuccess ? "text-green-400" : isError ? "text-red-400" : "text-cyan-400",
          )}
        >
          {code}
        </span>
      </div>
    )
  }

  return (
    <Card className="glass border-border/50 backdrop-blur-sm">
      <div className="p-6 border-b border-border/50">
        <h3 className="text-lg font-display font-semibold text-white">Email Log</h3>
        <p className="text-sm text-slate-400">Recent email delivery attempts and status</p>
      </div>
      <div className="overflow-x-auto">
        <Table>
          <TableHeader>
            <TableRow className="hover:bg-transparent border-border/50">
              <TableHead className="font-semibold text-slate-300">Sent</TableHead>
              <TableHead className="font-semibold text-slate-300">Subject</TableHead>
              <TableHead className="font-semibold text-slate-300">Code</TableHead>
              <TableHead className="font-semibold text-slate-300 text-right">Recipients</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {logs.map((log) => (
              <TableRow key={log.id} className="border-border/50 hover:bg-slate-800/30">
                <TableCell className="text-slate-400 font-mono text-sm">{formatDate(log.date)}</TableCell>
                <TableCell className="font-medium text-white max-w-md truncate">{log.subject}</TableCell>
                <TableCell>{getCodeDisplay(log.code)}</TableCell>
                <TableCell className="text-right">
                  <span className="text-slate-300 font-mono text-sm">{log.to}</span>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </Card>
  )
}
