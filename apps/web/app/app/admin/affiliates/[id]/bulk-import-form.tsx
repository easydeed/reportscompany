"use client"

import { useState, useRef } from "react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Badge } from "@/components/ui/badge"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Upload, FileText, Loader2, CheckCircle, XCircle, Download } from "lucide-react"

interface BulkImportFormProps {
  affiliateId: string
  affiliateName: string
}

interface AgentData {
  email: string
  first_name: string
  last_name: string
  name: string
}

interface ImportResult {
  email: string
  success: boolean
  account_id?: string
  user_id?: string
  error?: string
}

export function BulkImportForm({ affiliateId, affiliateName }: BulkImportFormProps) {
  const router = useRouter()
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [agents, setAgents] = useState<AgentData[]>([])
  const [results, setResults] = useState<ImportResult[] | null>(null)
  const [successCount, setSuccessCount] = useState(0)
  const [errorCount, setErrorCount] = useState(0)

  function parseCSV(text: string): AgentData[] {
    const lines = text.trim().split("\n")
    if (lines.length < 2) return []

    const headers = lines[0].toLowerCase().split(",").map(h => h.trim())
    const emailIdx = headers.findIndex(h => h === "email" || h === "e-mail")
    const firstNameIdx = headers.findIndex(h => h === "first_name" || h === "firstname" || h === "first name" || h === "first")
    const lastNameIdx = headers.findIndex(h => h === "last_name" || h === "lastname" || h === "last name" || h === "last")
    const nameIdx = headers.findIndex(h => h === "name" || h === "full_name" || h === "fullname" || h === "full name")

    if (emailIdx === -1) {
      throw new Error("CSV must have an 'email' column")
    }

    const parsedAgents: AgentData[] = []

    for (let i = 1; i < lines.length; i++) {
      const line = lines[i].trim()
      if (!line) continue

      // Handle quoted values with commas
      const values: string[] = []
      let current = ""
      let inQuotes = false

      for (const char of line) {
        if (char === '"') {
          inQuotes = !inQuotes
        } else if (char === "," && !inQuotes) {
          values.push(current.trim())
          current = ""
        } else {
          current += char
        }
      }
      values.push(current.trim())

      const email = values[emailIdx]?.replace(/"/g, "").trim().toLowerCase() || ""
      const firstName = firstNameIdx >= 0 ? values[firstNameIdx]?.replace(/"/g, "").trim() || "" : ""
      const lastName = lastNameIdx >= 0 ? values[lastNameIdx]?.replace(/"/g, "").trim() || "" : ""
      let name = nameIdx >= 0 ? values[nameIdx]?.replace(/"/g, "").trim() || "" : ""

      // Generate name if not provided
      if (!name && (firstName || lastName)) {
        name = `${firstName} ${lastName}`.trim()
      }

      if (email) {
        parsedAgents.push({ email, first_name: firstName, last_name: lastName, name })
      }
    }

    return parsedAgents
  }

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (!file) return

    setError(null)
    setResults(null)

    const reader = new FileReader()
    reader.onload = (event) => {
      try {
        const text = event.target?.result as string
        const parsed = parseCSV(text)
        if (parsed.length === 0) {
          setError("No valid agents found in CSV")
          return
        }
        setAgents(parsed)
      } catch (err: any) {
        setError(err.message || "Failed to parse CSV")
      }
    }
    reader.readAsText(file)
  }

  async function handleImport() {
    if (agents.length === 0) return

    setLoading(true)
    setError(null)

    try {
      const res = await fetch(`/api/proxy/v1/admin/affiliates/${affiliateId}/bulk-import`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          affiliate_id: affiliateId,
          agents: agents,
        }),
      })

      const data = await res.json()

      if (!res.ok) {
        throw new Error(data.detail || data.error || "Import failed")
      }

      setResults(data.results)
      setSuccessCount(data.success_count)
      setErrorCount(data.error_count)

      if (data.success_count > 0) {
        router.refresh()
      }
    } catch (err: any) {
      setError(err.message || "Import failed")
    } finally {
      setLoading(false)
    }
  }

  function handleReset() {
    setAgents([])
    setResults(null)
    setError(null)
    setSuccessCount(0)
    setErrorCount(0)
    if (fileInputRef.current) {
      fileInputRef.current.value = ""
    }
  }

  function downloadTemplate() {
    const template = "email,first_name,last_name,name\njohn@example.com,John,Doe,John Doe\njane@example.com,Jane,Smith,Jane Smith"
    const blob = new Blob([template], { type: "text/csv" })
    const url = URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = "agent_import_template.csv"
    a.click()
    URL.revokeObjectURL(url)
  }

  // Show results if import is complete
  if (results) {
    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Badge variant="outline" className="text-green-600">
              <CheckCircle className="h-3 w-3 mr-1" />
              {successCount} imported
            </Badge>
            {errorCount > 0 && (
              <Badge variant="outline" className="text-red-600">
                <XCircle className="h-3 w-3 mr-1" />
                {errorCount} failed
              </Badge>
            )}
          </div>
          <Button variant="outline" onClick={handleReset}>
            Import More
          </Button>
        </div>

        <div className="max-h-[300px] overflow-auto border rounded">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Email</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Details</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {results.map((result, idx) => (
                <TableRow key={idx}>
                  <TableCell>{result.email}</TableCell>
                  <TableCell>
                    {result.success ? (
                      <Badge variant="outline" className="text-green-600">
                        <CheckCircle className="h-3 w-3 mr-1" />
                        Success
                      </Badge>
                    ) : (
                      <Badge variant="outline" className="text-red-600">
                        <XCircle className="h-3 w-3 mr-1" />
                        Failed
                      </Badge>
                    )}
                  </TableCell>
                  <TableCell className="text-sm text-muted-foreground">
                    {result.success ? "Invite sent" : result.error}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </div>
    )
  }

  // Show preview if agents are loaded
  if (agents.length > 0) {
    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="text-sm text-muted-foreground">
            <FileText className="h-4 w-4 inline mr-1" />
            {agents.length} agent{agents.length !== 1 ? "s" : ""} ready to import
          </div>
          <div className="flex gap-2">
            <Button variant="outline" onClick={handleReset}>
              Cancel
            </Button>
            <Button onClick={handleImport} disabled={loading}>
              {loading && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
              Import {agents.length} Agent{agents.length !== 1 ? "s" : ""}
            </Button>
          </div>
        </div>

        {error && (
          <Alert variant="destructive">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        <div className="max-h-[300px] overflow-auto border rounded">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Email</TableHead>
                <TableHead>First Name</TableHead>
                <TableHead>Last Name</TableHead>
                <TableHead>Name</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {agents.map((agent, idx) => (
                <TableRow key={idx}>
                  <TableCell>{agent.email}</TableCell>
                  <TableCell>{agent.first_name || "-"}</TableCell>
                  <TableCell>{agent.last_name || "-"}</TableCell>
                  <TableCell>{agent.name || "-"}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </div>
    )
  }

  // Show upload form
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <Label>Upload CSV File</Label>
          <p className="text-sm text-muted-foreground">
            Import multiple agents at once for {affiliateName}
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={downloadTemplate}>
          <Download className="h-4 w-4 mr-2" />
          Download Template
        </Button>
      </div>

      <div
        className="border-2 border-dashed rounded-lg p-8 text-center hover:border-primary/50 cursor-pointer transition-colors"
        onClick={() => fileInputRef.current?.click()}
      >
        <Upload className="h-8 w-8 mx-auto text-muted-foreground mb-2" />
        <p className="text-sm text-muted-foreground mb-1">
          Click to upload or drag and drop
        </p>
        <p className="text-xs text-muted-foreground">
          CSV with columns: email, first_name, last_name, name
        </p>
      </div>

      <Input
        ref={fileInputRef}
        type="file"
        accept=".csv"
        onChange={handleFileChange}
        className="hidden"
      />

      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}
    </div>
  )
}
